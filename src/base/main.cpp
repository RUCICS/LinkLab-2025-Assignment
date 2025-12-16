#include "fle.hpp"
#include "string_utils.hpp"
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <execinfo.h>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std::string_literals;

void segv_handler(int sig, siginfo_t* si, void* ctx)
{
    fprintf(stderr, "Caught SIGSEGV at address: %p\n", si->si_addr);
    fflush(stderr);
    fprintf(stderr, "Error code: %d\n", si->si_code);
    fflush(stderr);

    auto uctx = reinterpret_cast<ucontext_t*>(ctx);

    // 发生段错误的指令地址
    auto rip = uctx->uc_mcontext.gregs[REG_RIP];

    // call 指令前，会先往栈里压入返回地址，RSP 指向栈顶。
    // 这里尝试从栈顶读取 8 字节（对于 x86_64）当作返回地址
    auto rsp = uctx->uc_mcontext.gregs[REG_RSP];
    void* call_site_next = 0;
    // 这里要确保 rsp 是可读，且内存布局正常
    // 对于因为错误跳转而崩溃的大多数场景，下面的读取通常可行
    if (rsp != 0) {
        // 取到栈顶存放的返回地址
        call_site_next = reinterpret_cast<void*>(*reinterpret_cast<uint64_t*>(rsp));
    }

    fprintf(stderr, "Instruction at: %p\n", reinterpret_cast<void*>(rip));
    fflush(stderr);
    // call_site_next 是 call 指令推入的“返回地址”，即 call 指令自身之后的那条指令地址
    // 它通常比 call 指令的开头多 5~7 个字节（具体看是否是 call rel32 或 call r/m64 等）
    // 因此可用 call_site_next - offset 推算出 call 指令的开头
    fprintf(stderr, "Likely return address: %p\n", call_site_next);
    fflush(stderr);

    // 恢复默认的信号处理程序
    signal(SIGSEGV, SIG_DFL);
    // 重新抛出信号
    raise(sig);
}

// 辅助函数：解析程序头
static void parse_program_headers(const json& j, FLEObject& obj)
{
    if (j.contains("phdrs")) {
        for (const auto& phdr_json : j["phdrs"]) {
            ProgramHeader phdr;
            phdr.name = phdr_json["name"].get<std::string>();
            phdr.vaddr = phdr_json["vaddr"].get<uint64_t>();
            phdr.size = phdr_json["size"].get<uint32_t>();
            phdr.flags = phdr_json["flags"].get<uint32_t>();
            obj.phdrs.push_back(phdr);
        }
    }
}

// 辅助函数：解析节头
static void parse_section_headers(const json& j, FLEObject& obj)
{
    if (j.contains("shdrs")) {
        for (const auto& shdr_json : j["shdrs"]) {
            SectionHeader shdr;
            shdr.name = shdr_json["name"].get<std::string>();
            shdr.type = shdr_json["type"].get<uint32_t>();
            shdr.flags = shdr_json["flags"].get<uint32_t>();
            shdr.addr = shdr_json["addr"].get<uint64_t>();
            shdr.offset = shdr_json["offset"].get<uint64_t>();
            shdr.size = shdr_json["size"].get<uint64_t>();
            obj.shdrs.push_back(shdr);
        }
    }
}

// 辅助函数：解析重定位类型
static RelocationType parse_relocation_type(const std::string& type_str)
{
    if (type_str == "rel")
        return RelocationType::R_X86_64_PC32;
    if (type_str == "abs64")
        return RelocationType::R_X86_64_64;
    if (type_str == "abs")
        return RelocationType::R_X86_64_32;
    if (type_str == "abs32s")
        return RelocationType::R_X86_64_32S;
    throw std::runtime_error("Invalid relocation type: " + type_str);
}

static FLEObject parse_fle_from_json(const json& j, const std::string& name)
{
    FLEObject obj;
    obj.name = name;
    obj.type = j["type"].get<std::string>();

    if (obj.type == ".ar") {
        if (j.contains("members")) {
            for (const auto& member_json : j["members"]) {
                std::string member_name = "";
                if (member_json.contains("name")) {
                    member_name = member_json["name"].get<std::string>();
                }
                obj.members.push_back(parse_fle_from_json(member_json, member_name));
            }
        }
        return obj;
    }

    // 如果是可执行文件，读取入口点和程序头
    if (obj.type == ".exe") {
        if (j.contains("entry")) {
            obj.entry = j["entry"].get<size_t>();
        }
        parse_program_headers(j, obj);
    }

    parse_section_headers(j, obj);

    std::unordered_map<std::string, Symbol> symbol_table;

    // 第一遍：收集所有符号定义并计算偏移量
    for (auto& [key, value] : j.items()) {
        if (key == "type" || key == "entry" || key == "phdrs" || key == "shdrs" || key == "members" || key == "name")
            continue;

        // size_t current_offset = 0;
        for (const auto& line : value) {
            std::string line_str = line.get<std::string>();
            size_t colon_pos = line_str.find(':');
            std::string prefix = line_str.substr(0, colon_pos);
            std::string content = line_str.substr(colon_pos + 1);

            if (prefix == "🏷️" || prefix == "📎" || prefix == "📤") {
                std::string name;
                size_t size, offset;
                std::istringstream ss(content);
                ss >> name >> size >> offset;

                name = trim(name);
                SymbolType type = prefix == "🏷️" ? SymbolType::LOCAL : prefix == "📎" ? SymbolType::WEAK
                                                                                      : SymbolType::GLOBAL;

                Symbol sym {
                    type,
                    std::string(key),
                    offset,
                    size,
                    name
                };

                symbol_table[name] = sym;
                obj.symbols.push_back(sym);
            }
        }
    }

    // 第二遍：处理节的内容和重定位
    for (auto& [key, value] : j.items()) {
        if (key == "type" || key == "entry" || key == "phdrs" || key == "shdrs" || key == "members" || key == "name")
            continue;

        FLESection section;
        section.has_symbols = false;

        for (const auto& line : value) {
            std::string line_str = line.get<std::string>();
            size_t colon_pos = line_str.find(':');
            std::string prefix = line_str.substr(0, colon_pos);
            std::string content = line_str.substr(colon_pos + 1);

            if (prefix == "🔢") {
                std::stringstream ss(content);
                uint32_t byte;
                while (ss >> std::hex >> byte) {
                    section.data.push_back(static_cast<uint8_t>(byte));
                }
            } else if (prefix == "❓") {
                std::string reloc_str = trim(content);
                std::regex reloc_pattern(R"(\.(rel|abs64|abs|abs32s)\(([\w.]+)\s*([-+])\s*([0-9a-fA-F]+)\))");
                std::smatch match;

                if (!std::regex_match(reloc_str, match, reloc_pattern)) {
                    throw std::runtime_error("Invalid relocation: " + reloc_str);
                }

                RelocationType type = parse_relocation_type(match[1].str());
                std::string symbol_name = match[2].str();
                std::string sign = match[3].str();
                int64_t append_value = std::stoi(match[4].str(), nullptr, 16);
                if (sign == "-") {
                    append_value = -append_value;
                }

                Relocation reloc {
                    type,
                    section.data.size(),
                    symbol_name,
                    append_value
                };

                auto it = symbol_table.find(symbol_name);
                if (it == symbol_table.end()) {
                    // 如果符号不在符号表中，添加为未定义符号
                    Symbol sym {
                        SymbolType::UNDEFINED,
                        "",
                        0,
                        0,
                        symbol_name
                    };
                    symbol_table[symbol_name] = sym;
                    obj.symbols.push_back(sym);
                }

                section.relocs.push_back(reloc);

                // 根据重定位类型预留空间
                size_t size = (type == RelocationType::R_X86_64_64) ? 8 : 4;
                section.data.insert(section.data.end(), size, 0);
            } else if (prefix == "🏷️" || prefix == "📎" || prefix == "📤") {
                section.has_symbols = true;
            }
        }

        section.name = key;
        obj.sections[key] = section;
    }

    return obj;
}

FLEObject load_fle(const std::string& file)
{
    std::ifstream infile(file);
    std::string content((std::istreambuf_iterator<char>(infile)),
        std::istreambuf_iterator<char>());

    if (content.substr(0, 2) == "#!") {
        content = content.substr(content.find('\n') + 1);
    }

    json j = json::parse(content);
    return parse_fle_from_json(j, get_basename(file));
}

void FLE_ar(const std::vector<std::string>& args)
{
    if (args.size() < 2) {
        throw std::runtime_error("Usage: ar <output.fle> <input1.fle> ...");
    }

    std::string outfile = args[0];
    json ar_json;
    ar_json["type"] = ".ar";
    ar_json["name"] = get_basename(outfile);

    json members = json::array();
    for (size_t i = 1; i < args.size(); ++i) {
        std::ifstream infile(args[i]);
        std::string content((std::istreambuf_iterator<char>(infile)),
            std::istreambuf_iterator<char>());

        if (content.substr(0, 2) == "#!") {
            content = content.substr(content.find('\n') + 1);
        }

        json member_json = json::parse(content);
        // Ensure name is set in the member JSON so it can be recovered
        member_json["name"] = get_basename(args[i]);
        members.push_back(member_json);
    }

    ar_json["members"] = members;

    std::ofstream out(outfile);
    out << ar_json.dump(4) << std::endl;
}

int main(int argc, char* argv[])
{
    // singlestack
    constexpr size_t SIGSTACK_BUFFER_SIZE = 1024 * 1024;
    uint8_t sigstack_buffer[SIGSTACK_BUFFER_SIZE];
    stack_t sigstack;
    sigstack.ss_sp = sigstack_buffer;
    sigstack.ss_size = sizeof(sigstack_buffer);
    sigstack.ss_flags = 0;
    sigaltstack(&sigstack, NULL);

    struct sigaction sa;
    sa.sa_flags = SA_SIGINFO | SA_ONSTACK;
    sa.sa_sigaction = segv_handler;
    if (sigaction(SIGSEGV, &sa, NULL) == -1) {
        std::cerr << "Failed to set up signal handler for SIGSEGV" << std::endl;
        return 1;
    }

    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <command> [args...]\n"
                  << "Commands:\n"
                  << "  objdump <input.fle>              Display contents of FLE file\n"
                  << "  nm <input.fle>                   Display symbol table\n"
                  << "  ld [-o output.fle] input1.fle... Link FLE files\n"
                  << "  exec <input.fle>                 Execute FLE file\n"
                  << "  cc [-o output.fle] input.c...    Compile C files\n"
                  << "  ar <output.fle> <input.fle>...   Create static archive\n"
                  << "  readfle <input.fle>              Display FLE file information\n"
                  << "  disasm <input.fle> <section>     Disassemble section\n";
        return 1;
    }

    std::string tool = "FLE_"s + get_basename(argv[0]);
    std::vector<std::string> args(argv + 1, argv + argc);

    try {
        if (tool == "FLE_objdump") {
            if (args.size() != 1) {
                throw std::runtime_error("Usage: objdump <input.fle>");
            }
            FLEWriter writer;
            FLE_objdump(load_fle(args[0]), writer);
            writer.write_to_file(args[0] + ".objdump");
        } else if (tool == "FLE_nm") {
            if (args.size() != 1) {
                throw std::runtime_error("Usage: nm <input.fle>");
            }
            FLE_nm(load_fle(args[0]));
        } else if (tool == "FLE_exec") {
            if (args.size() != 1) {
                throw std::runtime_error("Usage: exec <input.fle>");
            }
            FLE_exec(load_fle(args[0]));
        } else if (tool == "FLE_ld") {
            std::string outfile = "a.out";
            std::vector<std::string> input_files;

            for (size_t i = 0; i < args.size(); ++i) {
                if (args[i] == "-o" && i + 1 < args.size()) {
                    outfile = args[++i];
                } else {
                    input_files.push_back(args[i]);
                }
            }

            if (input_files.empty()) {
                throw std::runtime_error("No input files specified");
            }

            std::vector<FLEObject> objects;
            for (const auto& file : input_files) {
                objects.push_back(load_fle(file));
            }

            // for (const auto& obj : objects) {
            //     std::cerr << "Object type: " << obj.type << std::endl;
            //     std::cerr << "Symbols:" << std::endl;
            //     for (const auto& sym : obj.symbols) {
            //         std::cerr << "  " << sym.name << " in " << sym.section << std::endl;
            //     }
            // }

            // 链接
            FLEObject linked_obj = FLE_ld(objects);

            // 写入文件
            FLEWriter writer;
            FLE_objdump(linked_obj, writer);
            writer.write_to_file(outfile);
        } else if (tool == "FLE_cc") {
            FLE_cc(args);
        } else if (tool == "FLE_readfle") {
            if (args.size() != 1) {
                throw std::runtime_error("Usage: readfle <input.fle>");
            }
            FLE_readfle(load_fle(args[0]));
        } else if (tool == "FLE_disasm") {
            if (args.size() != 2) {
                throw std::runtime_error("Usage: disasm <input.fle> <section>");
            }
            FLE_disasm(load_fle(args[0]), args[1]);
        } else if (tool == "FLE_ar") {
            FLE_ar(args);
        } else {
            std::cerr << "Unknown tool: " << tool << std::endl;
            return 1;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
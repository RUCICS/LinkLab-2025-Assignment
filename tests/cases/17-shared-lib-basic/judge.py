#!/usr/bin/env python3
"""
B1-1 Judge: 验证动态符号表的正确性
- public_add 和 public_mul 应出现在动态符号表中
- internal_helper 不应出现在动态符号表中
"""
import json
import sys
import os

def load_fle_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def extract_dynsym_names(fle_obj):
    """从FLE对象中提取动态符号表中的符号名"""
    names = set()
    
    # 检查 sections 中的符号定义
    for section_name, section_data in fle_obj.items():
        if not isinstance(section_data, list):
            continue
        for line in section_data:
            if isinstance(line, str):
                # 📤 表示全局符号（应导出）
                # 📎 表示弱符号（也应导出）
                if line.startswith("📤:") or line.startswith("📎:"):
                    # 格式: "📤: symbol_name size offset"
                    parts = line.split(":", 1)[1].strip().split()
                    if parts:
                        names.add(parts[0])
    
    # 也检查 symbols 数组（如果存在）
    if "symbols" in fle_obj:
        for sym in fle_obj["symbols"]:
            if isinstance(sym, dict):
                sym_type = sym.get("type", "")
                sym_name = sym.get("name", "")
                # GLOBAL 或 WEAK 类型的符号应该被导出
                if sym_type in ["GLOBAL", "WEAK", 1, 2]:  # 1=WEAK, 2=GLOBAL in enum
                    names.add(sym_name)
    
    return names

def judge():
    try:
        input_data = json.load(sys.stdin)
        test_dir = input_data["test_dir"]
        build_dir = os.path.join(test_dir, "build")
        
        so_path = os.path.join(build_dir, "libbasic.so")
        
        try:
            so_fle = load_fle_json(so_path)
        except Exception as e:
            print(json.dumps({"success": False, "message": f"Failed to load shared library: {str(e)}"}))
            return
        
        # 验证文件类型
        if so_fle.get("type") != ".so":
            print(json.dumps({"success": False, "message": f"Expected type '.so', got '{so_fle.get('type')}'"}))
            return
        
        # 提取动态符号表
        dynsym_names = extract_dynsym_names(so_fle)
        
        # 验证1: public_add 应该在动态符号表中
        if "public_add" not in dynsym_names:
            print(json.dumps({"success": False, "message": "public_add not found in dynamic symbol table"}))
            return
        
        # 验证2: public_mul 应该在动态符号表中
        if "public_mul" not in dynsym_names:
            print(json.dumps({"success": False, "message": "public_mul not found in dynamic symbol table"}))
            return
        
        # 验证3: internal_helper 不应该在动态符号表中
        if "internal_helper" in dynsym_names:
            print(json.dumps({"success": False, "message": "internal_helper should NOT be in dynamic symbol table (it's static)"}))
            return
        
        print(json.dumps({"success": True, "message": "Dynamic symbol table verification passed."}))
        
    except Exception as e:
        print(json.dumps({"success": False, "message": f"Judge error: {str(e)}"}))

if __name__ == "__main__":
    judge()

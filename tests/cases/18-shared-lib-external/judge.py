#!/usr/bin/env python3
"""
B1-2 Judge: 验证动态重定位表的正确性
- 共享库对 external_func_a 和 external_func_b 的调用应保留在 dyn_relocs 中
"""
import json
import sys
import os

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from common.fle_utils import extract_dynamic_relocs

def load_fle_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def judge():
    try:
        input_data = json.load(sys.stdin)
        test_dir = input_data["test_dir"]
        build_dir = os.path.join(test_dir, "build")
        
        so_path = os.path.join(build_dir, "libexternal.so")
        
        try:
            so_fle = load_fle_json(so_path)
        except Exception as e:
            print(json.dumps({"success": False, "message": f"Failed to load shared library: {str(e)}"}))
            return
        
        # 验证文件类型
        if so_fle.get("type") != ".so":
            print(json.dumps({"success": False, "message": f"Expected type '.so', got '{so_fle.get('type')}'"}))
            return
        
        # 检查动态重定位表（嵌入在节内容中）
        dyn_relocs = extract_dynamic_relocs(so_fle)
        
        # 收集所有被引用的外部符号
        external_symbols = set()
        external_func_a_count = 0
        external_func_b_count = 0
        
        for reloc in dyn_relocs:
            sym_name = reloc.get("symbol", "")
            external_symbols.add(sym_name)
            if sym_name == "external_func_a":
                external_func_a_count += 1
            elif sym_name == "external_func_b":
                external_func_b_count += 1
        
        # 验证1: external_func_a 应该在动态重定位表中
        if "external_func_a" not in external_symbols:
            print(json.dumps({"success": False, "message": "external_func_a not found in dynamic relocations"}))
            return
        
        # 验证2: external_func_b 应该在动态重定位表中
        if "external_func_b" not in external_symbols:
            print(json.dumps({"success": False, "message": "external_func_b not found in dynamic relocations"}))
            return
        
        # 验证3: external_func_a 被调用了两次
        # 情况A (Basic Bonus1): 使用 Text Relocation (PC32)，每个调用点一个重定位，共2个。
        # 情况B (Challenge): 使用 GOT (R_X86_64_64)，合并为一个GOT条目重定位，共1个。
        
        has_got_reloc_a = False
        for reloc in dyn_relocs:
            if reloc.get("symbol") == "external_func_a":
                # R_X86_64_64 (Type 2) implies GOT
                if reloc.get("type") == 2:
                    has_got_reloc_a = True
                    break
        
        if has_got_reloc_a:
            # Advanced implementation: 1 GOT relocation is sufficient
            if external_func_a_count < 1:
                print(json.dumps({
                    "success": False, 
                    "message": f"external_func_a has GOT relocation but count is {external_func_a_count} (expected >= 1)"
                }))
                return
        else:
            # Basic implementation: Must have relocation for each call site
            if external_func_a_count < 2:
                print(json.dumps({
                    "success": False, 
                    "message": f"external_func_a called twice but only {external_func_a_count} relocation(s) found (Basic impl expects 2, Advanced impl expects type 2)"
                }))
                return
        
        # 验证4: lib_call_external 和 lib_get_value 应该被导出
        # 检查动态符号表
        exported_symbols = set()
        for key, value in so_fle.items():
            if isinstance(value, list):
                for line in value:
                    if isinstance(line, str) and (line.startswith("📤:") or line.startswith("📎:")):
                        parts = line.split(":", 1)[1].strip().split()
                        if parts:
                            exported_symbols.add(parts[0])
        
        if "lib_call_external" not in exported_symbols:
            print(json.dumps({"success": False, "message": "lib_call_external not exported"}))
            return
        
        if "lib_get_value" not in exported_symbols:
            print(json.dumps({"success": False, "message": "lib_get_value not exported"}))
            return
        
        print(json.dumps({
            "success": True, 
            "message": f"Dynamic relocation table verification passed. Found {external_func_a_count} relocs for func_a, {external_func_b_count} for func_b."
        }))
        
    except Exception as e:
        print(json.dumps({"success": False, "message": f"Judge error: {str(e)}"}))

if __name__ == "__main__":
    judge()

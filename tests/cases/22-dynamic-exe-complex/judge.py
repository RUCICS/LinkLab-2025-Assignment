#!/usr/bin/env python3
"""
B2-3 Judge: 验证复杂调用场景与offset计算
- 5个函数都应出现在动态重定位表中
- 验证PLT结构的完整性
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
        
        exe_path = os.path.join(build_dir, "program")
        
        try:
            exe_fle = load_fle_json(exe_path)
        except Exception as e:
            print(json.dumps({"success": False, "message": f"Failed to load executable: {str(e)}"}))
            return
        
        # 检查动态重定位表
        dyn_relocs = extract_dynamic_relocs(exe_fle)

        reloc_symbols = set()
        for reloc in dyn_relocs:
            reloc_symbols.add(reloc.get("symbol", ""))
        
        # 验证所有5个函数都在动态重定位表中
        required_symbols = ["func_a", "func_b", "func_c", "func_d", "func_e"]
        missing = [sym for sym in required_symbols if sym not in reloc_symbols]
        
        if missing:
            print(json.dumps({
                "success": False, 
                "message": f"Missing symbols in dyn_relocs: {missing}. Found: {list(reloc_symbols)}"
            }))
            return
        
        func_got_relocs = [r for r in dyn_relocs if r.get("section") == ".got" and r.get("symbol", "").startswith("func_")]
        func_counts = {}
        for reloc in func_got_relocs:
            func_counts[reloc["symbol"]] = func_counts.get(reloc["symbol"], 0) + 1

        for symbol in required_symbols:
            if func_counts.get(symbol, 0) != 1:
                print(json.dumps({
                    "success": False,
                    "message": f"Expected exactly one GOT relocation for {symbol}, found {func_counts.get(symbol, 0)}"
                }))
                return
        
        print(json.dumps({
            "success": True, 
            "message": f"Complex PLT/GOT verification passed. All 5 functions found with {len(func_got_relocs)} GOT slots."
        }))
        
    except Exception as e:
        print(json.dumps({"success": False, "message": f"Judge error: {str(e)}"}))

if __name__ == "__main__":
    judge()

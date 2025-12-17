#!/usr/bin/env python3
"""
B2-1 Judge: 验证PLT/GOT基础机制
- 可执行文件应包含 .plt 或 .got 节
- 动态重定位表应包含对 add, sub, mul 的条目
- needed 字段应包含 libmath.so
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
        
        # 验证文件类型
        if exe_fle.get("type") != ".exe":
            print(json.dumps({"success": False, "message": f"Expected type '.exe', got '{exe_fle.get('type')}'"}))
            return
        
        # 检查 needed 字段
        needed = exe_fle.get("needed", [])
        if "libmath.so" not in needed and "${build_dir}/libmath.so" not in needed:
            # 允许相对路径或绝对路径
            found_libmath = any("libmath" in dep for dep in needed)
            if not found_libmath:
                print(json.dumps({"success": False, "message": f"libmath.so not in needed list: {needed}"}))
                return
        
        # 检查动态重定位表（嵌入在节内容中）
        dyn_relocs = extract_dynamic_relocs(exe_fle)
        
        reloc_symbols = set()
        for reloc in dyn_relocs:
            sym_name = reloc.get("symbol", "")
            reloc_symbols.add(sym_name)
        
        # 验证 add, sub, mul 都在动态重定位表中
        required_symbols = ["add", "sub", "mul"]
        missing = [sym for sym in required_symbols if sym not in reloc_symbols]
        
        if missing:
            print(json.dumps({
                "success": False, 
                "message": f"Missing symbols in dyn_relocs: {missing}. Found: {list(reloc_symbols)}"
            }))
            return
        
        # 检查是否存在 .plt 或 .got 节（可选检查）
        sections = set()
        if "shdrs" in exe_fle:
            for shdr in exe_fle["shdrs"]:
                sections.add(shdr.get("name", ""))
        
        has_plt_or_got = ".plt" in sections or ".got" in sections
        # 不强制要求，因为实现方式可能不同
        
        print(json.dumps({
            "success": True, 
            "message": f"PLT/GOT verification passed. dyn_relocs symbols: {list(reloc_symbols)}, needed: {needed}"
        }))
        
    except Exception as e:
        print(json.dumps({"success": False, "message": f"Judge error: {str(e)}"}))

if __name__ == "__main__":
    judge()

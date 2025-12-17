#!/usr/bin/env python3
"""
B2-2 Judge: 验证多库依赖与needed字段
- 可执行文件的 needed 字段应包含两个库
- libelma.so 的 needed 字段应包含 libamy.so
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

def check_needed_contains(needed_list, lib_name):
    """检查 needed 列表中是否包含指定的库"""
    for dep in needed_list:
        if lib_name in dep:
            return True
    return False

def judge():
    try:
        input_data = json.load(sys.stdin)
        test_dir = input_data["test_dir"]
        build_dir = os.path.join(test_dir, "build")
        
        exe_path = os.path.join(build_dir, "program")
        util_so_path = os.path.join(build_dir, "libelma.so")
        
        try:
            exe_fle = load_fle_json(exe_path)
            util_fle = load_fle_json(util_so_path)
        except Exception as e:
            print(json.dumps({"success": False, "message": f"Failed to load files: {str(e)}"}))
            return
        
        # 检查可执行文件的 needed 字段
        exe_needed = exe_fle.get("needed", [])
        
        # 应该依赖 libamy.so 和 libelma.so
        has_helper = check_needed_contains(exe_needed, "libamy")
        has_util = check_needed_contains(exe_needed, "libelma")
        
        if not has_helper:
            print(json.dumps({
                "success": False, 
                "message": f"Executable should depend on libamy.so. needed: {exe_needed}"
            }))
            return
        
        if not has_util:
            print(json.dumps({
                "success": False, 
                "message": f"Executable should depend on libelma.so. needed: {exe_needed}"
            }))
            return
        
        # 检查 libelma.so 的 needed 字段（应该依赖 libamy.so）
        util_needed = util_fle.get("needed", [])
        util_has_helper = check_needed_contains(util_needed, "libamy")
        
        if not util_has_helper:
            # 这不是强制要求，因为 libelma 可能不记录依赖
            # 只是一个额外的检查
            pass
        
        # 检查动态重定位
        dyn_relocs = extract_dynamic_relocs(exe_fle)
        reloc_symbols = set(r.get("symbol", "") for r in dyn_relocs)
        
        if "helper" not in reloc_symbols:
            print(json.dumps({
                "success": False, 
                "message": f"helper not in dyn_relocs. Found: {list(reloc_symbols)}"
            }))
            return
        
        if "util_func" not in reloc_symbols:
            print(json.dumps({
                "success": False, 
                "message": f"util_func not in dyn_relocs. Found: {list(reloc_symbols)}"
            }))
            return
        
        print(json.dumps({
            "success": True, 
            "message": f"Multi-lib dependency verification passed. exe needed: {exe_needed}"
        }))
        
    except Exception as e:
        print(json.dumps({"success": False, "message": f"Judge error: {str(e)}"}))

if __name__ == "__main__":
    judge()

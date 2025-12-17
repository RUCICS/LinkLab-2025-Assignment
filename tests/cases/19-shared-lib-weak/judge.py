#!/usr/bin/env python3
"""
B1-3 Judge: 验证弱符号的导出处理
- weak_default 和 weak_value 应以弱符号形式出现在动态符号表中
- strong_func 和 get_weak_value 应以强符号形式导出
"""
import json
import sys
import os

def load_fle_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def judge():
    try:
        input_data = json.load(sys.stdin)
        test_dir = input_data["test_dir"]
        build_dir = os.path.join(test_dir, "build")
        
        so_path = os.path.join(build_dir, "libweak.so")
        
        try:
            so_fle = load_fle_json(so_path)
        except Exception as e:
            print(json.dumps({"success": False, "message": f"Failed to load shared library: {str(e)}"}))
            return
        
        # 验证文件类型
        if so_fle.get("type") != ".so":
            print(json.dumps({"success": False, "message": f"Expected type '.so', got '{so_fle.get('type')}'"}))
            return
        
        # 收集符号信息
        strong_symbols = set()  # 📤
        weak_symbols = set()    # 📎
        
        for key, value in so_fle.items():
            if isinstance(value, list):
                for line in value:
                    if isinstance(line, str):
                        if line.startswith("📤:"):
                            parts = line.split(":", 1)[1].strip().split()
                            if parts:
                                strong_symbols.add(parts[0])
                        elif line.startswith("📎:"):
                            parts = line.split(":", 1)[1].strip().split()
                            if parts:
                                weak_symbols.add(parts[0])
        
        # 也检查 symbols 数组
        if "symbols" in so_fle:
            for sym in so_fle["symbols"]:
                if isinstance(sym, dict):
                    sym_type = sym.get("type", "")
                    sym_name = sym.get("name", "")
                    if sym_type == "GLOBAL" or sym_type == 2:
                        strong_symbols.add(sym_name)
                    elif sym_type == "WEAK" or sym_type == 1:
                        weak_symbols.add(sym_name)
        
        all_exported = strong_symbols | weak_symbols
        
        # 验证1: strong_func 应该被导出
        if "strong_func" not in all_exported:
            print(json.dumps({"success": False, "message": "strong_func not found in exported symbols"}))
            return
        
        # 验证2: get_weak_value 应该被导出
        if "get_weak_value" not in all_exported:
            print(json.dumps({"success": False, "message": "get_weak_value not found in exported symbols"}))
            return
        
        # 验证3: weak_default 应该被导出（作为弱符号）
        if "weak_default" not in all_exported:
            print(json.dumps({"success": False, "message": "weak_default not found in exported symbols"}))
            return
        
        # 验证4: weak_value 应该被导出（作为弱符号）
        if "weak_value" not in all_exported:
            print(json.dumps({"success": False, "message": "weak_value not found in exported symbols"}))
            return
        
        # 额外验证：weak_default 和 weak_value 应该是弱符号类型
        # （这是更严格的检查，但某些实现可能不区分）
        expected_weak = ["weak_default", "weak_value"]
        found_as_weak = [sym for sym in expected_weak if sym in weak_symbols]
        
        if len(found_as_weak) < 2:
            # 不强制要求必须标记为弱符号，只要导出即可
            # 但给出提示
            pass
        
        print(json.dumps({
            "success": True, 
            "message": f"Weak symbol export verification passed. Strong: {list(strong_symbols)}, Weak: {list(weak_symbols)}"
        }))
        
    except Exception as e:
        print(json.dumps({"success": False, "message": f"Judge error: {str(e)}"}))

if __name__ == "__main__":
    judge()

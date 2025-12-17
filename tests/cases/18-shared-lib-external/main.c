// 主程序：测试共享库调用外部函数后的计数
extern void lib_call_external(void);
extern int lib_get_value(void);
extern int get_call_count_a(void);
extern int get_call_count_b(void);

int main()
{
    // 调用共享库函数
    lib_call_external();

    // 验证外部函数被正确调用
    int count_a = get_call_count_a(); // 应该是 2（被调用两次）
    int count_b = get_call_count_b(); // 应该是 1（被调用一次）
    int value = lib_get_value(); // 应该是 42

    if (count_a == 2 && count_b == 1 && value == 42) {
        return 0; // 成功
    }
    return 1; // 失败
}

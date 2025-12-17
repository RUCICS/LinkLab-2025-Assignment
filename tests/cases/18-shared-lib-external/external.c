// B1-2: 外部符号的动态重定位保留
// 测试共享库对外部函数的引用是否正确保留到动态重定位表

// 声明外部函数（由其他库提供）
extern void external_func_a(void);
extern void external_func_b(void);

// 库导出的函数，调用外部函数
void lib_call_external(void)
{
    external_func_a();
    external_func_b();
    external_func_a(); // 重复调用，验证每次调用都有重定位
}

// 另一个导出函数
int lib_get_value(void)
{
    return 42;
}

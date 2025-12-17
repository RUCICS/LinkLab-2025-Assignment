// B1-3: 弱符号的导出处理
// 测试共享库中弱符号是否正确导出

// 弱符号：应该被导出，但可被覆盖
__attribute__((weak)) int weak_default(int x)
{
    return x + 100;
}

// 强符号：调用弱符号
int strong_func(int x)
{
    return weak_default(x) * 2;
}

// 另一个弱符号
__attribute__((weak)) int weak_value = 999;

// 使用弱符号的函数
int get_weak_value(void)
{
    return weak_value;
}

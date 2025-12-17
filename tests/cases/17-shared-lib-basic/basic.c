// B1-1: 基础共享库生成
// 测试内部符号处理与动态符号表

// 静态函数：不应被导出
static int internal_helper(int x)
{
    return x * 2;
}

// 全局函数：应被导出
int public_add(int a, int b)
{
    return internal_helper(a) + internal_helper(b);
}

// 全局函数：应被导出
int public_mul(int a, int b)
{
    return a * b;
}

// B2-1: PLT/GOT基础机制 - 主程序
// 使用 -fPIC 编译，调用共享库中的函数

extern int add(int, int);
extern int sub(int, int);
extern int mul(int, int);

int main()
{
    // mul(3, 4) = 12
    // sub(10, 5) = 5
    // add(12, 5) = 17
    int result = add(mul(3, 4), sub(10, 5));

    // 验证结果
    if (result == 17) {
        return 0; // 成功
    }
    return result; // 失败，返回实际结果便于调试
}

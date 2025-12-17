// B2-3: 复杂调用场景 - 主程序
// 以非字母顺序调用多个函数，严格测试PLT offset计算

extern int func_a(int);
extern int func_b(int);
extern int func_c(int);
extern int func_d(int);
extern int func_e(int);

int main()
{
    // 以不同顺序调用，测试PLT stub的正确性
    int r1 = func_e(10); // 10 + 4 = 14
    int r2 = func_a(5); // 5 + 0 = 5
    int r3 = func_c(7); // 7 + 2 = 9
    int r4 = func_b(3); // 3 + 1 = 4
    int r5 = func_d(2); // 2 + 3 = 5

    // 再次调用，验证多次调用的正确性
    int r6 = func_a(1); // 1 + 0 = 1
    int r7 = func_e(0); // 0 + 4 = 4

    // 总和: 14 + 5 + 9 + 4 + 5 + 1 + 4 = 42
    int sum = r1 + r2 + r3 + r4 + r5 + r6 + r7;

    // 验证结果
    if (sum == 42) {
        return 0; // 成功
    }
    return sum; // 失败，返回实际结果便于调试
}

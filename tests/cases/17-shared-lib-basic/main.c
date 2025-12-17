// 使用共享库的主程序
extern int public_add(int, int);
extern int public_mul(int, int);

int main()
{
    // public_add(3, 4) = internal_helper(3) + internal_helper(4) = 6 + 8 = 14
    int sum = public_add(3, 4);
    // public_mul(2, 7) = 14
    int product = public_mul(2, 7);

    // 验证：sum == 14 && product == 14
    if (sum == 14 && product == 14) {
        return 0; // 成功
    }
    return 1; // 失败
}

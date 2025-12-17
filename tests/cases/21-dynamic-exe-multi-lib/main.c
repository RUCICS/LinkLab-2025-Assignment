extern int helper(int);
extern int util_func(int);

int main()
{
    // helper(5) = 5 + 10 = 15
    int a = helper(5);

    // util_func(3) = helper(3) * 2 = (3 + 10) * 2 = 26
    int b = util_func(3);

    // 验证结果
    if (a == 15 && b == 26) {
        return 0; // 成功
    }
    return 1; // 失败
}

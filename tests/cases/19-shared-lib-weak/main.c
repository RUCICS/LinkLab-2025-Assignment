// 使用共享库的主程序
// 不覆盖弱符号，使用默认实现
extern int weak_default(int);
extern int strong_func(int);
extern int get_weak_value(void);

int main()
{
    // strong_func(5) = weak_default(5) * 2 = (5 + 100) * 2 = 210
    int result1 = strong_func(5);

    // weak_default(10) = 10 + 100 = 110
    int result2 = weak_default(10);

    // get_weak_value() = 999
    int result3 = get_weak_value();

    if (result1 == 210 && result2 == 110 && result3 == 999) {
        return 0; // 成功
    }
    return 1; // 失败
}

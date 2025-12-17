// 提供 external_func_a 和 external_func_b 的实现
// 这个文件会被静态链接或作为另一个共享库

static int call_count_a = 0;
static int call_count_b = 0;

void external_func_a(void)
{
    call_count_a++;
}

void external_func_b(void)
{
    call_count_b++;
}

int get_call_count_a(void)
{
    return call_count_a;
}

int get_call_count_b(void)
{
    return call_count_b;
}

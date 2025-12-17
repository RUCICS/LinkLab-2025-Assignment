// B2-3: 复杂调用场景 - 共享库
// 提供多个函数，用于严格测试PLT stub的offset计算

int func_a(int x) { return x; }
int func_b(int x) { return x + 1; }
int func_c(int x) { return x + 2; }
int func_d(int x) { return x + 3; }
int func_e(int x) { return x + 4; }

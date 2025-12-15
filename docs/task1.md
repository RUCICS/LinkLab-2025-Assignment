# 任务一：窥探程序的符号表

你有没有遇到过这样的错误？

```
undefined reference to `printf'
multiple definition of `main'
```

这些都与符号（symbol）有关。符号就像程序中的"名字"，代表了函数、变量等。让我们通过一个例子来理解：

```c
static int counter = 0;       // 静态变量：文件内可见
int shared = 42;              // 全局变量：其他文件可见
extern void print(int x);     // 外部函数：需要其他文件提供

void count() {                // 全局函数
    counter++;                // 访问静态变量
    print(counter);           // 调用外部函数
}
```

这段代码中包含了几种不同的符号：

- `counter`：静态符号，只在文件内可见
- `shared`：全局符号，可以被其他文件引用
- `print`：未定义符号，需要在链接时找到
- `count`：全局函数符号

你的第一个任务是补充 [src/student/nm.cpp](../src/student/nm.cpp) 中的 `FLE_nm` 函数，实现一个工具来查看这些符号。

对于上面的代码，它应该输出三行三列信息：

```
0000000000000000 T count    # 全局函数在 .text 节
0000000000000000 b counter  # 静态变量在 .bss 节
0000000000000000 D shared   # 全局变量在 .data 节
```

每一列的具体含义是：

- 地址：符号**在其所在节中**的偏移量
- 类型：符号的类型和位置
  - 大写（T、D、B、R）：全局符号，分别表示在代码段、数据段、BSS 段、只读数据段
  - 小写（t、d、b、r）：局部符号，分别表示在代码段、数据段、BSS 段、只读数据段
  - W、V：弱符号，分别表示在代码段、还是在数据段或 BSS 段
- 名称：符号的名字

要实现这个工具，你需要遍历符号表，确定每个符号的类型，并按格式打印信息。

> [!TIP]
> 格式化输出可以使用:
>  ```cpp
>  std::cout << std::setw(16) << std::setfill('0') << std::hex << addr;  // C++ 风格
>  ```
>  或
>  ```c
>  printf("%016lx", addr);  // C 风格,输出16位的十六进制数,左侧补0
>  ```
>  以及，在 C++ 20 后，`std::format` 和 `std::print` 提供了更简洁的格式化方案（本实验使用 `-std=c++17` 编译选项，不支持此特性。此方案仅供了解）
>  ```cpp
>  std::print("{:016x}", addr);  // Modern C++ 风格
>  ```

> [!TIP]
> 你可以根据符号的 section 字段判断其位置:
>   - ".text" - 代码段
>   - ".data" - 数据段
>   - ".bss" - BSS段
>   - "" (empty) - 未定义符号
>       - 你应该在 `FLE_nm` 的输出中，忽略所有未定义符号

完成后，运行测试来验证：

```bash
make test_1
```

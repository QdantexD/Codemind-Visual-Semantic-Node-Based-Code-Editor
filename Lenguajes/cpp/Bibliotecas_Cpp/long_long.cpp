// Biblioteca C++ — long long
#include <iostream>

long long llcount = 0;
long long llindex = 1;

long long sumar_long long(long long a, long long b) { return a + b; }
long long multiplicar_long long(long long a, long long b) { return a * b; }

void demo_long_long() {
    long long v = llcount;
    v = sumar_long long(v, llindex);
    std::cout << v << std::endl;
}

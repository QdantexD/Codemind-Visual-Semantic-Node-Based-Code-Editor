// Biblioteca C++ — unsigned long long
#include <iostream>

unsigned long long ullcount = 0;
unsigned long long ullindex = 1;

unsigned long long sumar_unsigned long long(unsigned long long a, unsigned long long b) { return a + b; }
unsigned long long multiplicar_unsigned long long(unsigned long long a, unsigned long long b) { return a * b; }

void demo_unsigned_long_long() {
    unsigned long long v = ullcount;
    v = sumar_unsigned long long(v, ullindex);
    std::cout << v << std::endl;
}

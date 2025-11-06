// Biblioteca C++ — long
#include <iostream>

long lcount = 0;
long lindex = 1;

long sumar_long(long a, long b) { return a + b; }
long multiplicar_long(long a, long b) { return a * b; }

void demo_long() {
    long v = lcount;
    v = sumar_long(v, lindex);
    std::cout << v << std::endl;
}

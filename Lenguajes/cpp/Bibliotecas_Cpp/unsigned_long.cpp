// Biblioteca C++ — unsigned long
#include <iostream>

unsigned long utime = 0;
unsigned long usize = 1;

unsigned long sumar_unsigned long(unsigned long a, unsigned long b) { return a + b; }
unsigned long multiplicar_unsigned long(unsigned long a, unsigned long b) { return a * b; }

void demo_unsigned_long() {
    unsigned long v = utime;
    v = sumar_unsigned long(v, usize);
    std::cout << v << std::endl;
}

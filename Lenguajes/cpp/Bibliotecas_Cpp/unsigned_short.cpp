// Biblioteca C++ — unsigned short
#include <iostream>

unsigned short usmall = 0;
unsigned short ushort = 1;

unsigned short sumar_unsigned short(unsigned short a, unsigned short b) { return a + b; }
unsigned short multiplicar_unsigned short(unsigned short a, unsigned short b) { return a * b; }

void demo_unsigned_short() {
    unsigned short v = usmall;
    v = sumar_unsigned short(v, ushort);
    std::cout << v << std::endl;
}

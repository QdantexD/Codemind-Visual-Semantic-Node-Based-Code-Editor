// Biblioteca C++ — unsigned int
#include <iostream>

unsigned int uid = 0;
unsigned int len = 1;

unsigned int sumar_unsigned int(unsigned int a, unsigned int b) { return a + b; }
unsigned int multiplicar_unsigned int(unsigned int a, unsigned int b) { return a * b; }

void demo_unsigned_int() {
    unsigned int v = uid;
    v = sumar_unsigned int(v, len);
    std::cout << v << std::endl;
}

// Biblioteca C++ — unsigned char
#include <iostream>

unsigned char uc = 0;
unsigned char byte = 1;

unsigned char sumar_unsigned char(unsigned char a, unsigned char b) { return a + b; }
unsigned char multiplicar_unsigned char(unsigned char a, unsigned char b) { return a * b; }

void demo_unsigned_char() {
    unsigned char v = uc;
    v = sumar_unsigned char(v, byte);
    std::cout << v << std::endl;
}

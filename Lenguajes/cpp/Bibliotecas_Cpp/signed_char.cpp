// Biblioteca C++ — signed char
#include <iostream>

signed char sc = 0;
signed char offset = 1;

signed char sumar_signed char(signed char a, signed char b) { return a + b; }
signed char multiplicar_signed char(signed char a, signed char b) { return a * b; }

void demo_signed_char() {
    signed char v = sc;
    v = sumar_signed char(v, offset);
    std::cout << v << std::endl;
}

// Biblioteca C++ — long double
#include <iostream>

long double precisa = 0;
long double ld = 1;

long double sumar_long double(long double a, long double b) { return a + b; }
long double multiplicar_long double(long double a, long double b) { return a * b; }

void demo_long_double() {
    long double v = precisa;
    v = sumar_long double(v, ld);
    std::cout << v << std::endl;
}

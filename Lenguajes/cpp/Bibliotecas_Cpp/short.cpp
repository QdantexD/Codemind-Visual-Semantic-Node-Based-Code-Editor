// Biblioteca C++ — short
#include <iostream>

short sidx = 0;
short small = 1;

short sumar_short(short a, short b) { return a + b; }
short multiplicar_short(short a, short b) { return a * b; }

void demo_short() {
    short v = sidx;
    v = sumar_short(v, small);
    std::cout << v << std::endl;
}

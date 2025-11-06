// Biblioteca C++ — size_t
#include <iostream>

size_t size = 0;
size_t length = 1;

size_t sumar_size_t(size_t a, size_t b) { return a + b; }
size_t multiplicar_size_t(size_t a, size_t b) { return a * b; }

void demo_size_t() {
    size_t v = size;
    v = sumar_size_t(v, length);
    std::cout << v << std::endl;
}

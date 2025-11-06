// Biblioteca C++ — char32_t
#include <iostream>

char32_t u32char = 0;
char32_t u32letter = 1;

char32_t sumar_char32_t(char32_t a, char32_t b) { return a + b; }
char32_t multiplicar_char32_t(char32_t a, char32_t b) { return a * b; }

void demo_char32_t() {
    char32_t v = u32char;
    v = sumar_char32_t(v, u32letter);
    std::cout << v << std::endl;
}

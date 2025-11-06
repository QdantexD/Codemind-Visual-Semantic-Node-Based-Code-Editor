// Biblioteca C++ — char16_t
#include <iostream>

char16_t u16char = 0;
char16_t u16letter = 1;

char16_t sumar_char16_t(char16_t a, char16_t b) { return a + b; }
char16_t multiplicar_char16_t(char16_t a, char16_t b) { return a * b; }

void demo_char16_t() {
    char16_t v = u16char;
    v = sumar_char16_t(v, u16letter);
    std::cout << v << std::endl;
}

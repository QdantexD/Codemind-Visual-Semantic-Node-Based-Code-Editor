// Biblioteca C++ — char
#include <iostream>

char letra = 0;
char caracter = 1;

char sumar_char(char a, char b) { return a + b; }
char multiplicar_char(char a, char b) { return a * b; }

void demo_char() {
    char v = letra;
    v = sumar_char(v, caracter);
    std::cout << v << std::endl;
}

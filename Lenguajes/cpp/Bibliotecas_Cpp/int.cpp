// Biblioteca C++ — int
#include <iostream>

int contador = 0;
int index = 1;

int sumar_int(int a, int b) { return a + b; }
int multiplicar_int(int a, int b) { return a * b; }

void demo_int() {
    int v = contador;
    v = sumar_int(v, index);
    std::cout << v << std::endl;
}

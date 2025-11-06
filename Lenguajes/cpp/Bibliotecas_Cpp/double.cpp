// Biblioteca C++ — double
#include <iostream>

double precio = 0;
double porcentaje = 1;

double sumar_double(double a, double b) { return a + b; }
double multiplicar_double(double a, double b) { return a * b; }

void demo_double() {
    double v = precio;
    v = sumar_double(v, porcentaje);
    std::cout << v << std::endl;
}

// Biblioteca C++ — float
#include <iostream>

float ratio = 0;
float value = 1;

float sumar_float(float a, float b) { return a + b; }
float multiplicar_float(float a, float b) { return a * b; }

void demo_float() {
    float v = ratio;
    v = sumar_float(v, value);
    std::cout << v << std::endl;
}

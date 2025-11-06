// Biblioteca C++ — std::vector
#include <vector>
#include <iostream>

std::vector<int> datos;

void fill_datos() {
    datos.push_back(1);
    datos.push_back(2);
    datos.push_back(3);
}

void print_datos() {
    for (int x : datos) std::cout << x << ' ';
    std::cout << std::endl;
}

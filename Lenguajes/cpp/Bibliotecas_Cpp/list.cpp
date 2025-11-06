// Biblioteca C++ — std::list
#include <list>
#include <iostream>

std::list<int> lista;

void fill_lista() {
    lista.push_back(10);
    lista.push_back(20);
}

void print_lista() {
    for (int x : lista) std::cout << x << ' ';
    std::cout << std::endl;
}

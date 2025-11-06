// Biblioteca C++ — string
#include <string>
#include <iostream>

string nombre = string("nombre");
string path = string("path");

string concatenar(const string& a, const string& b) { return a + b; }

void demo_string() {
    auto res = concatenar(nombre, path);
    std::cout << res << std::endl;
}

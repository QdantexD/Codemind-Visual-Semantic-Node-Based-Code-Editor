// Biblioteca C++ — bool
#include <iostream>

bool flag = 0;
bool active = 1;

bool sumar_bool(bool a, bool b) { return a + b; }
bool multiplicar_bool(bool a, bool b) { return a * b; }

void demo_bool() {
    bool v = flag;
    v = sumar_bool(v, active);
    std::cout << v << std::endl;
}

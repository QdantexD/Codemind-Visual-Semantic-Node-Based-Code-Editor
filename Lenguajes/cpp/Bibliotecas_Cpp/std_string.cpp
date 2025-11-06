// Biblioteca C++ — std::string
#include <string>
#include <iostream>

std::string name = std::string("name");
std::string route = std::string("route");

std::string concatenar(const std::string& a, const std::string& b) { return a + b; }

void demo_std_string() {
    auto res = concatenar(name, route);
    std::cout << res << std::endl;
}

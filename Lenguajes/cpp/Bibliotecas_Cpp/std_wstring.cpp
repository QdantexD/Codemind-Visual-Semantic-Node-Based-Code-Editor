// Biblioteca C++ — std::wstring
#include <string>
#include <iostream>

std::wstring wname = std::wstring("wname");
std::wstring wtext = std::wstring("wtext");

std::wstring concatenar(const std::wstring& a, const std::wstring& b) { return a + b; }

void demo_std_wstring() {
    auto res = concatenar(wname, wtext);
    std::cout << res << std::endl;
}

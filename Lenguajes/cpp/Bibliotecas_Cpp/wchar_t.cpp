// Biblioteca C++ — wchar_t
#include <iostream>

wchar_t wchar = 0;
wchar_t wletter = 1;

wchar_t sumar_wchar_t(wchar_t a, wchar_t b) { return a + b; }
wchar_t multiplicar_wchar_t(wchar_t a, wchar_t b) { return a * b; }

void demo_wchar_t() {
    wchar_t v = wchar;
    v = sumar_wchar_t(v, wletter);
    std::cout << v << std::endl;
}

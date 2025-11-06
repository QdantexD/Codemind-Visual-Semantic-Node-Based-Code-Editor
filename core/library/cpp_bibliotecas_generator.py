import os
import logging
from typing import Dict

logger = logging.getLogger("core.cpp_bibliotecas")

def _sanitize_filename(name: str) -> str:
    return (
        name.replace("::", "_")
            .replace(" ", "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace(":", "_")
    )


def _fundamental_template(type_name: str, var_a: str, var_b: str) -> str:
    return f"""// Biblioteca C++ — {type_name}
#include <iostream>

{type_name} {var_a} = 0;
{type_name} {var_b} = 1;

{type_name} sumar_{type_name}({type_name} a, {type_name} b) {{ return a + b; }}
{type_name} multiplicar_{type_name}({type_name} a, {type_name} b) {{ return a * b; }}

void demo_{_sanitize_filename(type_name)}() {{
    {type_name} v = {var_a};
    v = sumar_{type_name}(v, {var_b});
    std::cout << v << std::endl;
}}
"""


def _string_template(type_name: str, var_a: str, var_b: str) -> str:
    return f"""// Biblioteca C++ — {type_name}
#include <string>
#include <iostream>

{type_name} {var_a} = {type_name}("{var_a}");
{type_name} {var_b} = {type_name}("{var_b}");

{type_name} concatenar(const {type_name}& a, const {type_name}& b) {{ return a + b; }}

void demo_{_sanitize_filename(type_name)}() {{
    auto res = concatenar({var_a}, {var_b});
    std::cout << res << std::endl;
}}
"""


def _vector_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::vector
#include <vector>
#include <iostream>

std::vector<int> {var_name};

void fill_{var_name}() {{
    {var_name}.push_back(1);
    {var_name}.push_back(2);
    {var_name}.push_back(3);
}}

void print_{var_name}() {{
    for (int x : {var_name}) std::cout << x << ' ';
    std::cout << std::endl;
}}
"""


def _list_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::list
#include <list>
#include <iostream>

std::list<int> {var_name};

void fill_{var_name}() {{
    {var_name}.push_back(10);
    {var_name}.push_back(20);
}}

void print_{var_name}() {{
    for (int x : {var_name}) std::cout << x << ' ';
    std::cout << std::endl;
}}
"""


def _deque_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::deque
#include <deque>
#include <iostream>

std::deque<int> {var_name};

void demo_{var_name}() {{
    {var_name}.push_front(1);
    {var_name}.push_back(2);
}}
"""


def _set_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::set
#include <set>

std::set<int> {var_name};

void demo_{var_name}() {{
    {var_name}.insert(1);
    {var_name}.insert(2);
}}
"""


def _unordered_set_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::unordered_set
#include <unordered_set>

std::unordered_set<int> {var_name};

void demo_{var_name}() {{
    {var_name}.insert(42);
}}
"""


def _map_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::map
#include <map>
#include <string>

std::map<std::string, int> {var_name};

void demo_{var_name}() {{
    {var_name}["count"] = 1;
}}
"""


def _unordered_map_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::unordered_map
#include <unordered_map>
#include <string>

std::unordered_map<std::string, int> {var_name};

void demo_{var_name}() {{
    {var_name}["value"] = 7;
}}
"""


def _pair_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::pair
#include <utility>
#include <string>

std::pair<int, std::string> {var_name} = {{1, "a"}};
"""


def _optional_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::optional
#include <optional>

std::optional<int> {var_name};

void demo_{var_name}() {{
    {var_name} = 5;
}}
"""


def _variant_template(var_name: str) -> str:
    return f"""// Biblioteca C++ — std::variant
#include <variant>
#include <string>

std::variant<int, std::string> {var_name};

void demo_{var_name}() {{
    {var_name} = 10;
}}
"""


def _simple_decl(type_name: str, var_a: str, var_b: str) -> str:
    return f"""// Biblioteca C++ — {type_name}
{type_name} {var_a} = {type_name}();
{type_name} {var_b} = {type_name}();
"""


def generate_all_cpp_bibliotecas(output_root: str = None) -> str:
    """Genera archivos de ejemplo para todos los tipos C++ conocidos.

    Crea la carpeta Lenguajes/cpp/Bibliotecas_Cpp en la raíz del proyecto si no existe.
    Devuelve la ruta de salida.
    """
    try:
        # Determinar raíz del proyecto
        here = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
        out_dir = output_root or os.path.join(project_root, "Lenguajes", "cpp", "Bibliotecas_Cpp")
        os.makedirs(out_dir, exist_ok=True)

        # Importar biblioteca de variables para obtener tipos y sugerencias
        from .variable_library import variable_library
        try:
            variable_library.current_language = 'cpp'
        except Exception:
            pass
        all_suggestions: Dict[str, dict] = variable_library.get_all_suggestions() or {}

        count = 0
        for dtype, info in all_suggestions.items():
            suggs = info.get("suggestions", []) or ["valor"]
            a = _sanitize_filename(suggs[0])
            b = _sanitize_filename(suggs[1] if len(suggs) > 1 else f"{a}_2")
            fname = _sanitize_filename(dtype) + ".cpp"
            path = os.path.join(out_dir, fname)

            # Elegir plantilla
            text = None
            fundamental = {
                "bool", "char", "signed char", "unsigned char", "wchar_t",
                "char16_t", "char32_t", "short", "unsigned short", "int",
                "unsigned int", "long", "unsigned long", "long long",
                "unsigned long long", "size_t", "float", "double", "long double"
            }
            if dtype in fundamental:
                text = _fundamental_template(dtype, a, b)
            elif dtype in {"string", "std::string", "std::wstring"}:
                text = _string_template(dtype, a, b)
            elif dtype == "vector":
                text = _vector_template(a)
            elif dtype == "list":
                text = _list_template(a)
            elif dtype == "deque":
                text = _deque_template(a)
            elif dtype == "set":
                text = _set_template(a)
            elif dtype == "unordered_set":
                text = _unordered_set_template(a)
            elif dtype == "map":
                text = _map_template(a)
            elif dtype == "unordered_map":
                text = _unordered_map_template(a)
            elif dtype == "pair":
                text = _pair_template(a)
            elif dtype == "optional":
                text = _optional_template(a)
            elif dtype == "variant":
                text = _variant_template(a)
            else:
                # Fallback genérico
                text = _simple_decl(dtype, a, b)

            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                count += 1
            except Exception as e:
                logger.warning(f"No se pudo escribir {path}: {e}")

        logger.info(f"Bibliotecas C++ generadas: {count} archivos en {out_dir}")
        return out_dir
    except Exception as e:
        logger.exception(f"Error generando Bibliotecas C++: {e}")
        return ""
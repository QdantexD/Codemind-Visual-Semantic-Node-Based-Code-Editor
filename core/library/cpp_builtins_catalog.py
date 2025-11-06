"""
Catálogo de símbolos estándar de C++ para el editor de nodos.

Cada entrada contiene metadatos mínimos para crear nodos semánticos:
- node_id: identificador único estable
- name: nombre del símbolo (tipo, clase, función)
- type: "type" | "class" | "function" | "utility" | "io" | "algorithm" | "pointer" | "chrono" | "thread" | "filesystem" | "regex" | "random"
- header: cabecera de inclusión (por ejemplo: "<vector>")
- description: texto breve
- inputs: nombres de parámetros o entradas (si aplica)
- outputs: salida o tipo de retorno (si aplica)

Se agrupa por categorías para construir submenús.
"""
from typing import Dict, List


def _item(node_id: str, name: str, kind: str, header: str, description: str, inputs: List[str] = None, outputs: List[str] = None) -> Dict:
    return {
        "node_id": node_id,
        "name": name,
        "type": kind,
        "header": header,
        "description": description,
        "inputs": inputs or [],
        "outputs": outputs or [],
    }


def get_cpp_catalog() -> Dict[str, List[Dict]]:
    """Devuelve el catálogo por categorías."""
    tipos = [
        _item("std-int", "int", "type", "<cstdint>", "Entero básico de C++"),
        _item("std-long", "long", "type", "<cstdint>", "Entero largo"),
        _item("std-size_t", "size_t", "type", "<cstddef>", "Tamaño sin signo"),
        _item("std-float", "float", "type", "<cmath>", "Coma flotante simple"),
        _item("std-double", "double", "type", "<cmath>", "Coma flotante doble"),
        _item("std-bool", "bool", "type", "<stdbool.h>", "Booleano"),
        _item("std-char", "char", "type", "<cctype>", "Carácter"),
        _item("std-string", "std::string", "class", "<string>", "Cadena estándar"),
        _item("std-wstring", "std::wstring", "class", "<string>", "Cadena wide"),
        _item("std-optional", "std::optional<T>", "class", "<optional>", "Valor opcional"),
        _item("std-variant", "std::variant<Ts...>", "class", "<variant>", "Sum type"),
        _item("std-pair", "std::pair<A,B>", "class", "<utility>", "Par de valores"),
        _item("std-tuple", "std::tuple<Ts...>", "class", "<tuple>", "Tupla de valores"),
    ]

    contenedores = [
        _item("std-vector", "std::vector<int>", "class", "<vector>", "Vector dinámico"),
        _item("std-list", "std::list<int>", "class", "<list>", "Lista doblemente enlazada"),
        _item("std-deque", "std::deque<int>", "class", "<deque>", "Cola doble"),
        _item("std-array", "std::array<int, N>", "class", "<array>", "Array fijo"),
        _item("std-set", "std::set<int>", "class", "<set>", "Conjunto ordenado"),
        _item("std-uset", "std::unordered_set<int>", "class", "<unordered_set>", "Conjunto hash"),
        _item("std-map", "std::map<std::string,int>", "class", "<map>", "Mapa ordenado"),
        _item("std-umap", "std::unordered_map<std::string,int>", "class", "<unordered_map>", "Mapa hash"),
        _item("std-queue", "std::queue<int>", "class", "<queue>", "Cola FIFO"),
        _item("std-stack", "std::stack<int>", "class", "<stack>", "Pila LIFO"),
        _item("std-priority_queue", "std::priority_queue<int>", "class", "<queue>", "Cola de prioridad"),
    ]

    punteros = [
        _item("std-unique_ptr", "std::unique_ptr<T>", "pointer", "<memory>", "Puntero único"),
        _item("std-shared_ptr", "std::shared_ptr<T>", "pointer", "<memory>", "Puntero compartido"),
        _item("std-weak_ptr", "std::weak_ptr<T>", "pointer", "<memory>", "Puntero débil"),
        _item("std-make_unique", "std::make_unique<T>", "function", "<memory>", "Crea unique_ptr", ["args..."], ["std::unique_ptr<T>"]),
        _item("std-make_shared", "std::make_shared<T>", "function", "<memory>", "Crea shared_ptr", ["args..."], ["std::shared_ptr<T>"]),
    ]

    utilidades = [
        _item("std-move", "std::move", "utility", "<utility>", "Movimiento", ["T&&"], ["T&&"]),
        _item("std-forward", "std::forward", "utility", "<utility>", "Encaminamiento perfecto", ["T&&"], ["T&&"]),
        _item("std-swap", "std::swap", "utility", "<utility>", "Intercambia", ["T&","T&"], ["void"]),
        _item("std-exchange", "std::exchange", "utility", "<utility>", "Reemplaza y retorna", ["T&","U&&"], ["T"]),
    ]

    algoritmos = [
        _item("std-sort", "std::sort", "algorithm", "<algorithm>", "Ordena rango", ["beg","end"], ["void"]),
        _item("std-stable_sort", "std::stable_sort", "algorithm", "<algorithm>", "Orden estable", ["beg","end"], ["void"]),
        _item("std-find", "std::find", "algorithm", "<algorithm>", "Busca elemento", ["beg","end","value"], ["it"]),
        _item("std-accumulate", "std::accumulate", "algorithm", "<numeric>", "Acumula", ["beg","end","init"], ["T"]),
        _item("std-transform", "std::transform", "algorithm", "<algorithm>", "Transforma", ["beg","end","dest","op"], ["dest"]),
        _item("std-copy", "std::copy", "algorithm", "<algorithm>", "Copia", ["beg","end","dest"], ["dest"]),
    ]

    io = [
        _item("std-cout", "std::cout", "io", "<iostream>", "Salida estándar"),
        _item("std-cerr", "std::cerr", "io", "<iostream>", "Salida de errores"),
        _item("std-clog", "std::clog", "io", "<iostream>", "Log estándar"),
        _item("std-endl", "std::endl", "io", "<iostream>", "Fin de línea"),
        _item("std-stringstream", "std::stringstream", "class", "<sstream>", "Stream de cadenas"),
        _item("std-ifstream", "std::ifstream", "class", "<fstream>", "Archivo lectura"),
        _item("std-ofstream", "std::ofstream", "class", "<fstream>", "Archivo escritura"),
    ]

    tiempo_hilos = [
        _item("std-chrono-steady_clock", "std::chrono::steady_clock", "chrono", "<chrono>", "Reloj estable"),
        _item("std-chrono-duration", "std::chrono::duration", "chrono", "<chrono>", "Duración"),
        _item("std-this_thread-sleep_for", "std::this_thread::sleep_for", "thread", "<thread>", "Dormir hilo", ["duration"], ["void"]),
        _item("std-thread", "std::thread", "thread", "<thread>", "Hilo"),
        _item("std-mutex", "std::mutex", "thread", "<mutex>", "Mutex"),
        _item("std-lock_guard", "std::lock_guard<std::mutex>", "thread", "<mutex>", "Guardia de bloqueo"),
        _item("std-async", "std::async", "thread", "<future>", "Tarea asincrónica", ["f","args..."], ["std::future<T>"]),
        _item("std-future", "std::future<T>", "thread", "<future>", "Futuro"),
        _item("std-promise", "std::promise<T>", "thread", "<future>", "Promesa"),
    ]

    archivos = [
        _item("std-filesystem-path", "std::filesystem::path", "filesystem", "<filesystem>", "Ruta"),
        _item("std-filesystem-exists", "std::filesystem::exists", "function", "<filesystem>", "Comprueba existencia", ["path"], ["bool"]),
        _item("std-filesystem-create_directory", "std::filesystem::create_directory", "function", "<filesystem>", "Crea directorio", ["path"], ["bool"]),
    ]

    regex_random = [
        _item("std-regex", "std::regex", "regex", "<regex>", "Expresiones regulares"),
        _item("std-smatch", "std::smatch", "regex", "<regex>", "Match de regex"),
        _item("std-regex_search", "std::regex_search", "function", "<regex>", "Busca regex", ["text","regex"], ["bool"]),
        _item("std-mersenne", "std::mt19937", "random", "<random>", "Generador Mersenne"),
        _item("std-uniform_int_distribution", "std::uniform_int_distribution<int>", "random", "<random>", "Distribución uniforme"),
    ]

    return {
        "Tipos": tipos,
        "Contenedores": contenedores,
        "Punteros": punteros,
        "Utilidades": utilidades,
        "Algoritmos": algoritmos,
        "IO": io,
        "Tiempo/Hilos": tiempo_hilos,
        "Archivos": archivos,
        "Regex/Random": regex_random,
    }
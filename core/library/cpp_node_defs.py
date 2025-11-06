"""
Definiciones semánticas de nodos C++ para VSNC/SNCE.
Cada entrada describe símbolos con metadatos: header, namespace, tipo y relaciones.
"""
from typing import Dict, List


def make_function(namespace: str, header: str, name: str, parameters: List[str], returns: str, connects_to: List[str]) -> Dict:
    return {
        "node_type": "function",
        "language": "C++",
        "namespace": namespace,
        "header": header,
        "name": name,
        "parameters": parameters,
        "returns": returns,
        "connects_to": connects_to,
    }


def std_vector_method(method: str, T: str = "T") -> Dict:
    """Construye meta para métodos frecuentes de std::vector<T>."""
    header = "<vector>"
    ns = "std"
    vt = f"std::vector<{T}>"
    if method == "push_back":
        return make_function(ns, header, "push_back", [f"const {T}& value"], "void", [vt])
    if method == "emplace_back":
        return make_function(ns, header, "emplace_back", ["Args&&... args"], "void", [vt])
    if method == "size":
        return make_function(ns, header, "size", [], "size_t", [vt])
    if method == "clear":
        return make_function(ns, header, "clear", [], "void", [vt])
    if method == "reserve":
        return make_function(ns, header, "reserve", ["size_t new_cap"], "void", [vt])
    if method == "at":
        return make_function(ns, header, "at", ["size_t index"], f"{T}&", [vt])
    # Fallback genérico
    return make_function(ns, header, method, ["..."], "void", [vt])


def list_vector_methods() -> List[str]:
    return ["push_back", "emplace_back", "size", "clear", "reserve", "at"]
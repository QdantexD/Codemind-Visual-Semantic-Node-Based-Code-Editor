"""
Sistema de Biblioteca de Variables por Lenguaje
Autor: Eddi Andreé Salazar Matos
Descripción: Sistema inteligente de sugerencias de variables por lenguaje de programación
"""

import json
import os
import re
import time
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal

class VariableLibrary(QObject):
    """Biblioteca inteligente de variables por lenguaje de programación"""
    
    # Señales
    language_changed = Signal(str)
    variable_created = Signal(str, str, str)  # lenguaje, tipo, nombre
    
    def __init__(self):
        super().__init__()
        self._current_language = "python"
        self._custom_variables = {}  # Variables creadas por el usuario
        self._recent_variables = []    # Variables usadas recientemente
        self._max_recent = 10          # Máximo de variables recientes
        # Cache de escaneo del proyecto
        self._last_scan_path = None
        self._last_scan_time = 0.0
        self._scan_cooldown_seconds = 30.0
        # Modo de contenidos: permitir vaciar listas de sugerencias
        self._suggestions_enabled = False
        
        # Biblioteca de variables predefinidas por lenguaje
        self._language_libraries = {
            "python": {
                "int": {
                    "suggestions": ["contador", "edad", "tamaño", "index", "total", "cantidad", "posicion"],
                    "icon": "📊",
                    "description": "Número entero"
                },
                "str": {
                    "suggestions": ["nombre", "mensaje", "ruta", "texto", "data", "informacion", "contenido"],
                    "icon": "📝",
                    "description": "Texto/Cadena"
                },
                "bool": {
                    "suggestions": ["activo", "visible", "valido", "flag", "enable", "success", "completado"],
                    "icon": "✅",
                    "description": "Verdadero/Falso"
                },
                "list": {
                    "suggestions": ["datos", "items", "resultados", "array", "collection", "elementos", "valores"],
                    "icon": "📋",
                    "description": "Lista de elementos"
                },
                "dict": {
                    "suggestions": ["config", "usuarios", "cache", "settings", "params", "opciones", "metadata"],
                    "icon": "🗂️",
                    "description": "Diccionario/Mapa"
                },
                "float": {
                    "suggestions": ["precio", "porcentaje", "ratio", "decimal", "medida", "peso", "altura"],
                    "icon": "📏",
                    "description": "Número decimal"
                }
            },
            "cpp": {
                # Tipos fundamentales
                "bool": {
                    "suggestions": ["flag", "active", "valid", "enable", "success", "found", "ready"],
                    "icon": "⚡",
                    "description": "Verdadero/Falso"
                },
                "char": {
                    "suggestions": ["letra", "caracter", "sep", "c", "delim", "code"],
                    "icon": "🔣",
                    "description": "Carácter"
                },
                "signed char": {
                    "suggestions": ["sc", "offset", "delta", "byte"],
                    "icon": "🔣",
                    "description": "Carácter con signo"
                },
                "unsigned char": {
                    "suggestions": ["uc", "byte", "ch", "mask"],
                    "icon": "🔣",
                    "description": "Carácter sin signo"
                },
                "wchar_t": {
                    "suggestions": ["wchar", "wletter", "wsep"],
                    "icon": "🔣",
                    "description": "Carácter ancho"
                },
                "char16_t": {
                    "suggestions": ["u16char", "u16letter"],
                    "icon": "🔣",
                    "description": "Carácter UTF-16"
                },
                "char32_t": {
                    "suggestions": ["u32char", "u32letter"],
                    "icon": "🔣",
                    "description": "Carácter UTF-32"
                },
                "short": {
                    "suggestions": ["sidx", "small", "shortval"],
                    "icon": "🔢",
                    "description": "Entero corto"
                },
                "unsigned short": {
                    "suggestions": ["usmall", "ushort", "port"],
                    "icon": "🔢",
                    "description": "Entero corto sin signo"
                },
                "int": {
                    "suggestions": ["contador", "index", "size", "count", "length", "position", "id"],
                    "icon": "🔢",
                    "description": "Número entero"
                },
                "unsigned int": {
                    "suggestions": ["uid", "len", "capacity", "count_u"],
                    "icon": "🔢",
                    "description": "Entero sin signo"
                },
                "long": {
                    "suggestions": ["lcount", "lindex", "time", "ticks"],
                    "icon": "🔢",
                    "description": "Entero largo"
                },
                "unsigned long": {
                    "suggestions": ["utime", "usize", "ulength"],
                    "icon": "🔢",
                    "description": "Entero largo sin signo"
                },
                "long long": {
                    "suggestions": ["llcount", "llindex", "big"],
                    "icon": "🔢",
                    "description": "Entero muy largo"
                },
                "unsigned long long": {
                    "suggestions": ["ullcount", "ullindex", "hash"],
                    "icon": "🔢",
                    "description": "Entero muy largo sin signo"
                },
                "size_t": {
                    "suggestions": ["size", "length", "capacity", "n"],
                    "icon": "📏",
                    "description": "Tamaño plataforma"
                },
                "float": {
                    "suggestions": ["ratio", "value", "percent", "x", "y"],
                    "icon": "📏",
                    "description": "Número decimal simple"
                },
                "double": {
                    "suggestions": ["precio", "porcentaje", "ratio", "decimal", "precision", "weight", "distance"],
                    "icon": "🎯",
                    "description": "Número de precisión"
                },
                "long double": {
                    "suggestions": ["precisa", "ld", "bigdec"],
                    "icon": "🎯",
                    "description": "Número decimal extra precisión"
                },
                # Strings
                "string": {
                    "suggestions": ["nombre", "path", "texto", "message", "content", "filename", "data"],
                    "icon": "🔤",
                    "description": "Texto/Cadena"
                },
                "std::string": {
                    "suggestions": ["name", "route", "text", "msg", "content"],
                    "icon": "🔤",
                    "description": "Texto/Cadena (std::string)"
                },
                "std::wstring": {
                    "suggestions": ["wname", "wtext"],
                    "icon": "🔤",
                    "description": "Texto ancho"
                },
                # Contenedores clásicos
                "vector": {
                    "suggestions": ["datos", "items", "list", "array", "elements", "values", "objects"],
                    "icon": "📊",
                    "description": "Vector/Array"
                },
                "list": {
                    "suggestions": ["lista", "cola", "nodos"],
                    "icon": "📋",
                    "description": "Lista enlazada"
                },
                "deque": {
                    "suggestions": ["deque", "dq", "buffer"],
                    "icon": "📚",
                    "description": "Doble cola"
                },
                "set": {
                    "suggestions": ["conjunto", "unic", "keys"],
                    "icon": "🧩",
                    "description": "Conjunto ordenado"
                },
                "unordered_set": {
                    "suggestions": ["uset", "ukeys", "bucket"],
                    "icon": "🧩",
                    "description": "Conjunto no ordenado"
                },
                "map": {
                    "suggestions": ["config", "users", "cache", "dictionary", "table", "index", "store"],
                    "icon": "🗺️",
                    "description": "Mapa/Diccionario"
                },
                "unordered_map": {
                    "suggestions": ["umap", "hash", "lookup"],
                    "icon": "🗺️",
                    "description": "Mapa no ordenado"
                },
                # Utilidades modernas
                "pair": {
                    "suggestions": ["par", "kv", "range"],
                    "icon": "🔗",
                    "description": "Par de valores"
                },
                "optional": {
                    "suggestions": ["opt", "talvez", "maybe"],
                    "icon": "❓",
                    "description": "Valor opcional"
                },
                "variant": {
                    "suggestions": ["var", "multi", "union"],
                    "icon": "🔀",
                    "description": "Tipo múltiple"
                }
            },
            "javascript": {
                "number": {
                    "suggestions": ["contador", "edad", "tamaño", "index", "total", "cantidad", "posicion"],
                    "icon": "🔢",
                    "description": "Número"
                },
                "string": {
                    "suggestions": ["nombre", "mensaje", "ruta", "texto", "data", "informacion", "contenido"],
                    "icon": "📝",
                    "description": "Texto/Cadena"
                },
                "boolean": {
                    "suggestions": ["activo", "visible", "valido", "flag", "enable", "success", "completado"],
                    "icon": "✨",
                    "description": "Verdadero/Falso"
                },
                "array": {
                    "suggestions": ["datos", "items", "resultados", "list", "collection", "elementos", "valores"],
                    "icon": "📚",
                    "description": "Array/Lista"
                },
                "object": {
                    "suggestions": ["config", "usuarios", "cache", "settings", "params", "opciones", "metadata"],
                    "icon": "📦",
                    "description": "Objeto/Diccionario"
                }
            }
        }
    
    @property
    def current_language(self) -> str:
        """Obtener el lenguaje actual"""
        return self._current_language
    
    @current_language.setter
    def current_language(self, language: str):
        """Cambiar el lenguaje actual"""
        if language in self._language_libraries:
            self._current_language = language
            self.language_changed.emit(language)
    
    def get_available_languages(self) -> List[str]:
        """Obtener lista de lenguajes disponibles"""
        return list(self._language_libraries.keys())
    
    def get_type_suggestions(self, data_type: str) -> List[str]:
        """Obtener sugerencias de nombres para un tipo específico"""
        language_lib = self._language_libraries.get(self._current_language, {})
        type_info = language_lib.get(data_type, {})
        suggestions = type_info.get("suggestions", [])
        
        # Agregar variables personalizadas del mismo tipo
        custom_vars = self._custom_variables.get(self._current_language, {}).get(data_type, [])
        suggestions.extend(custom_vars)
        
        # Agregar variables recientes del mismo tipo
        recent_vars = [var for var in self._recent_variables if var.get("type") == data_type]
        recent_names = [var.get("name") for var in recent_vars]
        suggestions.extend(recent_names)
        
        # Eliminar duplicados y mantener orden
        return list(dict.fromkeys(suggestions))
    
    def get_all_suggestions(self) -> Dict[str, dict]:
        """Obtener todas las sugerencias para el lenguaje actual"""
        # Si las sugerencias están deshabilitadas, devolver vacío
        if not getattr(self, "_suggestions_enabled", True):
            return {}
        language_lib = self._language_libraries.get(self._current_language, {})
        result = {}
        
        for data_type, type_info in language_lib.items():
            result[data_type] = {
                "suggestions": self.get_type_suggestions(data_type),
                "icon": type_info.get("icon", "🔧"),
                "description": type_info.get("description", "Tipo de dato")
            }
        
        return result

    def set_suggestions_enabled(self, enabled: bool):
        """Habilitar o deshabilitar la entrega de sugerencias (vacía contenidos cuando False)."""
        try:
            self._suggestions_enabled = bool(enabled)
        except Exception:
            self._suggestions_enabled = False

    # ------------------------------
    # Plantillas de código C++ por variable
    # ------------------------------
    def build_cpp_code_template(self, data_type: str, var_name: str) -> str:
        """Construye una plantilla de código C++ para una variable dada.
        Incluye cabeceras y una declaración/uso básico al estilo VS Code.
        """
        dt = (data_type or "").strip()
        name = (var_name or dt or "var").strip()
        hdrs = []
        lines = []

        def add(line: str):
            lines.append(line)

        # Cabeceras y contenido por tipo
        if dt in {"int", "short", "unsigned int", "long", "unsigned long", "long long", "unsigned long long", "size_t"}:
            hdrs = ["<iostream>"]
            add(f"{dt} {name} = 0;")
            add(f"std::cout << \"{name}=\" << {name} << std::endl;")
        elif dt in {"float"}:
            hdrs = ["<iostream>"]
            add(f"float {name} = 0.0f;")
            add(f"std::cout << \"{name}=\" << {name} << std::endl;")
        elif dt in {"double", "long double"}:
            hdrs = ["<iostream>"]
            add(f"{dt} {name} = 0.0;")
            add(f"std::cout << \"{name}=\" << {name} << std::endl;")
        elif dt in {"bool"}:
            hdrs = ["<iostream>"]
            add(f"bool {name} = false;")
            add(f"std::cout << std::boolalpha << \"{name}=\" << {name} << std::endl;")
        elif dt in {"string", "std::string"}:
            hdrs = ["<string>", "<iostream>"]
            use_type = "std::string" if dt == "std::string" else "std::string"
            add(f"{use_type} {name} = \"\";")
            add(f"{name}.append(\"texto\");")
            add(f"std::cout << {name} << std::endl;")
        elif dt in {"std::wstring"}:
            hdrs = ["<string>", "<iostream>"]
            add(f"std::wstring {name} = L\"\";")
            add(f"std::wcout << {name} << std::endl;")
        elif dt in {"vector"}:
            hdrs = ["<vector>", "<iostream>"]
            add(f"std::vector<int> {name};")
            add(f"{name}.push_back(0);")
            add(f"std::cout << \"size=\" << {name}.size() << std::endl;")
        elif dt in {"list"}:
            hdrs = ["<list>", "<iostream>"]
            add(f"std::list<int> {name};")
            add(f"{name}.push_back(1);")
            add(f"std::cout << {name}.size() << std::endl;")
        elif dt in {"deque"}:
            hdrs = ["<deque>", "<iostream>"]
            add(f"std::deque<int> {name};")
            add(f"{name}.push_back(2);")
            add(f"std::cout << {name}.size() << std::endl;")
        elif dt in {"set"}:
            hdrs = ["<set>", "<iostream>"]
            add(f"std::set<int> {name};")
            add(f"{name}.insert(3);")
            add(f"std::cout << {name}.size() << std::endl;")
        elif dt in {"unordered_set"}:
            hdrs = ["<unordered_set>", "<iostream>"]
            add(f"std::unordered_set<int> {name};")
            add(f"{name}.insert(4);")
            add(f"std::cout << {name}.size() << std::endl;")
        elif dt in {"map"}:
            hdrs = ["<map>", "<string>", "<iostream>"]
            add(f"std::map<std::string, int> {name};")
            add(f"{name}[\"key\"] = 42;")
            add(f"std::cout << {name}[\"key\"] << std::endl;")
        elif dt in {"unordered_map"}:
            hdrs = ["<unordered_map>", "<string>", "<iostream>"]
            add(f"std::unordered_map<std::string, int> {name};")
            add(f"{name}[\"key\"] = 7;")
            add(f"std::cout << {name}[\"key\"] << std::endl;")
        elif dt in {"pair"}:
            hdrs = ["<utility>", "<iostream>"]
            add(f"std::pair<int, int> {name} = {{0, 0}};")
            add(f"std::cout << {name}.first << \",\" << {name}.second << std::endl;")
        elif dt in {"optional"}:
            hdrs = ["<optional>", "<iostream>"]
            add(f"std::optional<int> {name} = std::nullopt;")
            add(f"{name} = 5;")
            add(f"std::cout << ({name}.has_value() ? *{name} : -1) << std::endl;")
        elif dt in {"variant"}:
            hdrs = ["<variant>", "<string>", "<iostream>"]
            add(f"std::variant<int, double, std::string> {name} = 0;")
            add(f"{name} = std::string(\"hola\");")
            add(f"std::cout << \"variant set\" << std::endl;")
        else:
            # Fallback genérico
            hdrs = ["<iostream>"]
            add(f"auto {name} = 0;")
            add(f"std::cout << \"{name}=\" << {name} << std::endl;")

        # Ensamblar cabeceras + código
        hdr_text = "\n".join([f"#include {h}" for h in hdrs])
        body = "\n".join(lines)
        return f"{hdr_text}\n\n// variable: {dt} '{name}'\n{body}\n"
    
    def add_custom_variable(self, data_type: str, name: str):
        """Agregar variable personalizada"""
        if self._current_language not in self._custom_variables:
            self._custom_variables[self._current_language] = {}
        
        if data_type not in self._custom_variables[self._current_language]:
            self._custom_variables[self._current_language][data_type] = []
        
        if name not in self._custom_variables[self._current_language][data_type]:
            self._custom_variables[self._current_language][data_type].append(name)
            self.variable_created.emit(self._current_language, data_type, name)
    
    def add_recent_variable(self, data_type: str, name: str, value: any):
        """Agregar variable al historial reciente"""
        variable_info = {
            "type": data_type,
            "name": name,
            "value": value,
            "timestamp": self._get_timestamp()
        }
        
        # Agregar al principio
        self._recent_variables.insert(0, variable_info)
        
        # Mantener solo las más recientes
        if len(self._recent_variables) > self._max_recent:
            self._recent_variables = self._recent_variables[:self._max_recent]
    
    def get_variable_info(self, data_type: str, name: str) -> dict:
        """Obtener información sobre una variable específica"""
        language_lib = self._language_libraries.get(self._current_language, {})
        type_info = language_lib.get(data_type, {})
        
        return {
            "type": data_type,
            "name": name,
            "icon": type_info.get("icon", "🔧"),
            "description": type_info.get("description", "Variable personalizada"),
            "language": self._current_language
        }
    
    def search_variables(self, search_term: str) -> List[dict]:
        """Buscar variables por nombre o tipo"""
        results = []
        all_suggestions = self.get_all_suggestions()
        
        search_term = search_term.lower()
        
        for data_type, type_info in all_suggestions.items():
            # Buscar en el nombre del tipo
            if search_term in data_type.lower():
                results.append({
                    "type": "type_match",
                    "data_type": data_type,
                    "icon": type_info["icon"],
                    "description": f"Tipo: {type_info['description']}"
                })
            
            # Buscar en las sugerencias
            for suggestion in type_info["suggestions"]:
                if search_term in suggestion.lower():
                    results.append({
                        "type": "variable_match",
                        "data_type": data_type,
                        "name": suggestion,
                        "icon": type_info["icon"],
                        "description": f"{type_info['icon']} {data_type}: {suggestion}"
                    })
        
        return results
    
    def _get_timestamp(self) -> float:
        """Obtener timestamp actual"""
        import time
        return time.time()
    
    def export_library(self, filepath: str):
        """Exportar la biblioteca a archivo JSON"""
        data = {
            "language_libraries": self._language_libraries,
            "custom_variables": self._custom_variables,
            "recent_variables": self._recent_variables,
            "current_language": self._current_language
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def import_library(self, filepath: str):
        """Importar biblioteca desde archivo JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Actualizar bibliotecas
            if "language_libraries" in data:
                self._language_libraries.update(data["language_libraries"])
            
            if "custom_variables" in data:
                self._custom_variables.update(data["custom_variables"])
            
            if "recent_variables" in data:
                self._recent_variables = data["recent_variables"]
            
            if "current_language" in data:
                self.current_language = data["current_language"]
                
        except Exception as e:
            print(f"Error al importar biblioteca: {e}")
    
    def get_tab_completion_suggestions(self, partial_name: str = "") -> List[dict]:
        """Obtener sugerencias para autocompletado con TAB"""
        # Antes de generar sugerencias, intentar escanear el proyecto (con cooldown)
        try:
            self._ensure_project_scan()
        except Exception:
            pass
        suggestions = []
        all_suggestions = self.get_all_suggestions()
        
        for data_type, type_info in all_suggestions.items():
            for variable_name in type_info["suggestions"]:
                # Si no hay nombre parcial o coincide con el inicio
                if not partial_name or variable_name.startswith(partial_name.lower()):
                    suggestions.append({
                        "name": variable_name,
                        "type": data_type,
                        "icon": type_info["icon"],
                        "description": type_info["description"],
                        "priority": self._calculate_priority(variable_name, partial_name)
                    })
        
        # Ordenar por prioridad (coincidencias exactas primero)
        suggestions.sort(key=lambda x: x["priority"], reverse=True)
        
        return suggestions[:10]  # Máximo 10 sugerencias
    
    def _calculate_priority(self, variable_name: str, partial_name: str) -> int:
        """Calcular prioridad de una sugerencia"""
        priority = 0
        
        # Coincidencia exacta tiene máxima prioridad
        if variable_name == partial_name:
            priority += 100
        
        # Coincidencia al inicio tiene alta prioridad
        if variable_name.startswith(partial_name):
            priority += 50
        
        # Variables recientes tienen prioridad adicional
        recent_names = [var.get("name") for var in self._recent_variables]
        if variable_name in recent_names:
            priority += 30
        
        # Longitud más corta = mejor (más fácil de escribir)
        priority += max(0, 20 - len(variable_name))
        
        return priority

    # ------------------------------
    # Escaneo de proyecto para enriquecer sugerencias
    # ------------------------------
    def _ensure_project_scan(self):
        """Ejecuta un escaneo ligero del proyecto si el último escaneo está desfasado."""
        try:
            root = os.getcwd()
            now = time.time()
            if self._last_scan_path != root or (now - self._last_scan_time) > self._scan_cooldown_seconds:
                self.scan_project(root)
                self._last_scan_path = root
                self._last_scan_time = now
        except Exception:
            pass

    def scan_project(self, root_path: str, max_files: int = 400):
        """Escanea archivos del proyecto para descubrir variables y enriquecer la biblioteca.
        - Soporta Python (.py), C/C++ (.c/.h/.cpp/.hpp/.cc), JavaScript/TypeScript (.js/.ts)
        - Heurístico, no compila/parsea; extracción por regex.
        """
        try:
            files_scanned = 0
            for dirpath, dirnames, filenames in os.walk(root_path):
                # Ignorar carpetas comunes de dependencias/caches
                base = os.path.basename(dirpath).lower()
                if base in {".git", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".vscode"}:
                    continue
                for fname in filenames:
                    fpath = os.path.join(dirpath, fname)
                    ext = os.path.splitext(fname)[1].lower()
                    try:
                        if ext in {".py"}:
                            self._scan_python_file(fpath)
                            files_scanned += 1
                        elif ext in {".c", ".h", ".cpp", ".hpp", ".cc"}:
                            self._scan_cpp_file(fpath)
                            files_scanned += 1
                        elif ext in {".js", ".ts"}:
                            self._scan_js_file(fpath)
                            files_scanned += 1
                    except Exception:
                        pass
                    if files_scanned >= max_files:
                        return
        except Exception:
            pass

    def _add_discovered(self, language: str, data_type: str, name: str):
        """Añade nombre descubierto a variables personalizadas evitando duplicados."""
        try:
            if language not in self._custom_variables:
                self._custom_variables[language] = {}
            if data_type not in self._custom_variables[language]:
                self._custom_variables[language][data_type] = []
            name = (name or "").strip()
            if name and name not in self._custom_variables[language][data_type]:
                self._custom_variables[language][data_type].append(name)
        except Exception:
            pass

    def _scan_python_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            return
        # Asignaciones simples: nombre = valor
        for m in re.finditer(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$", text, re.M):
            name, value = m.group(1), m.group(2)
            value = value.strip()
            if re.match(r"^[-+]?\d+$", value):
                self._add_discovered("python", "int", name)
            elif re.match(r"^[-+]?\d*\.\d+", value):
                self._add_discovered("python", "float", name)
            elif re.match(r'^["\'].*["\']$', value):
                self._add_discovered("python", "str", name)
            elif value.startswith("["):
                self._add_discovered("python", "list", name)
            elif value.startswith("{"):
                self._add_discovered("python", "dict", name)
            elif value.lower() in {"true", "false"}:
                self._add_discovered("python", "bool", name)

    def _scan_cpp_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            return
        patterns = {
            "int": r"\bint\s+([a-zA-Z_]\w*)",
            "double": r"\bdouble\s+([a-zA-Z_]\w*)",
            "bool": r"\bbool\s+([a-zA-Z_]\w*)",
            "string": r"\b(?:std::string|string)\s+([a-zA-Z_]\w*)",
            "vector": r"\bstd::vector<[^>]+>\s+([a-zA-Z_]\w*)",
            "map": r"\bstd::map<[^>]+>\s+([a-zA-Z_]\w*)",
        }
        for dtype, pat in patterns.items():
            for m in re.finditer(pat, text):
                self._add_discovered("cpp", dtype, m.group(1))

    def _scan_js_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            return
        decl_re = re.compile(r"\b(?:const|let|var)\s+([a-zA-Z_]\w*)(?:\s*=\s*([^;\n]+))?", re.M)
        for m in decl_re.finditer(text):
            name = m.group(1)
            value = (m.group(2) or "").strip()
            if value:
                if re.match(r"^[-+]?\d+(?:\.\d+)?$", value):
                    self._add_discovered("javascript", "number", name)
                elif value.lower() in {"true", "false"}:
                    self._add_discovered("javascript", "boolean", name)
                elif value.startswith("["):
                    self._add_discovered("javascript", "array", name)
                elif value.startswith("{"):
                    self._add_discovered("javascript", "object", name)
                elif re.match(r'^["\'].*["\']$', value):
                    self._add_discovered("javascript", "string", name)
                else:
                    # Por defecto, asumir string
                    self._add_discovered("javascript", "string", name)
            else:
                # Sin asignación: asumir number genérico
                self._add_discovered("javascript", "number", name)

# Instancia global para uso en toda la aplicación
variable_library = VariableLibrary()
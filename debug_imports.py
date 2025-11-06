#!/usr/bin/env python3
"""
Debug para verificar las importaciones
"""

import sys
import os

print("Python version:", sys.version)
print("Python path:", sys.path)
print("Current directory:", os.getcwd())
print("Contents of current directory:", os.listdir("."))

# Intentar importar PySide6
try:
    import PySide6
    print("✅ PySide6 imported successfully")
    print("PySide6 version:", PySide6.__version__)
except ImportError as e:
    print("❌ PySide6 import failed:", e)

# Intentar importar desde core
try:
    from core.library.variable_library import variable_library
    print("✅ variable_library imported successfully")
    print("Available languages:", list(variable_library._language_libraries.keys()))
except ImportError as e:
    print("❌ variable_library import failed:", e)

# Intentar importar desde core
try:
    from core.ui.tab_completion_widget import TabCompletionWidget
    print("✅ TabCompletionWidget imported successfully")
except ImportError as e:
    print("❌ TabCompletionWidget import failed:", e)

# Intentar importar desde core
try:
    from core.nodes.variable_node import VariableNode
    print("✅ VariableNode imported successfully")
except ImportError as e:
    print("❌ VariableNode import failed:", e)

# Intentar importar desde core
try:
    from core.graph.node_view import NodeView
    print("✅ NodeView imported successfully")
except ImportError as e:
    print("❌ NodeView import failed:", e)
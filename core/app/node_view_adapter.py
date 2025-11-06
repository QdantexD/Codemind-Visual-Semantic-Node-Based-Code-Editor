from PySide6.QtCore import Qt
import logging

logger = logging.getLogger("core.node_view_adapter")

class MyNodeGraphController:
    """Controlador simple para gestionar nodos sin dependencias externas."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.nodes = []
        logger.info("MyNodeGraphController inicializado")
    
    def add_node(self, node_type="generic", title="Node", x=0, y=0):
        """Añade un nodo al grafo."""
        node_data = {
            'type': node_type,
            'title': title,
            'x': x,
            'y': y,
            'id': len(self.nodes)
        }
        self.nodes.append(node_data)
        return node_data
    
    def remove_node(self, node_id):
        """Elimina un nodo del grafo."""
        self.nodes = [n for n in self.nodes if n['id'] != node_id]
    
    def get_nodes(self):
        """Obtiene todos los nodos."""
        return self.nodes
    
    def clear(self):
        """Limpia todos los nodos."""
        self.nodes.clear()

from typing import Dict, List, Tuple, Any


class GraphRuntime:
    """Runtime sencillo de dataflow para el editor de nodos.

    - Mantiene un mapa de conexiones (start -> end) con nombres de puertos.
    - Propaga valores desde los puertos de salida de cada nodo hacia los puertos de entrada conectados.
    - Invoca `compute_output_values()` en cada nodo para obtener los valores actuales.
    - Itera algunas veces hasta estabilizar (evita ciclos infinitos con límite de iteraciones).
    """

    def __init__(self, view=None):
        self.view = view
        self._connections: List[Tuple[Any, Any, str, str]] = []

    def rebuild_from_view(self):
        """Reconstruye el mapa de conexiones a partir de `view.connections`."""
        self._connections.clear()
        if not self.view:
            return
        try:
            for c in getattr(self.view, 'connections', []) or []:
                if getattr(c, 'start_item', None) and getattr(c, 'end_item', None):
                    self._connections.append((c.start_item, c.end_item, getattr(c, 'start_port', 'output'), getattr(c, 'end_port', 'input')))
        except Exception:
            pass

    def evaluate_all(self, max_iters: int = 8):
        """Evalúa y propaga el grafo completo.

        - Llama a `compute_output_values()` de cada nodo para obtener sus salidas.
        - Propaga a través de las conexiones hacia `receive_input_value()` del nodo destino.
        - Repite hasta que no haya cambios o se alcance `max_iters`.
        """
        if not self.view:
            return

        # Recolectar nodos
        try:
            nodes = [it for it in self.view._scene.items() if hasattr(it, 'compute_output_values')]
        except Exception:
            nodes = []

        def _snapshot_inputs() -> Dict[Any, Dict[str, Any]]:
            snap: Dict[Any, Dict[str, Any]] = {}
            for n in nodes:
                try:
                    snap[n] = dict(getattr(n, 'input_values', {}) or {})
                except Exception:
                    snap[n] = {}
            return snap

        last_inputs = _snapshot_inputs()

        # Reiniciar inputs en nodos Output para evitar duplicados entre evaluaciones
        try:
            for n in nodes:
                if str(getattr(n, 'node_type', '')).lower() == 'output':
                    setattr(n, 'input_values', {})
        except Exception:
            pass

        for _ in range(max_iters):
            # Calcular salidas de cada nodo
            for n in nodes:
                try:
                    outputs = n.compute_output_values()
                    if isinstance(outputs, dict):
                        n.output_values = outputs
                except Exception:
                    # Ignorar nodos que fallen al computar
                    pass

            # Propagar por las conexiones
            changed = False
            for start, end, start_port, end_port in list(self._connections):
                try:
                    val = None
                    if hasattr(start, 'output_values'):
                        val = (start.output_values or {}).get(start_port, None)
                    # Si no hay output_values, usar contenido como fallback
                    if val is None and hasattr(start, 'to_plain_text'):
                        val = start.to_plain_text()
                    # Entregar al destino (combinando si el destino es un nodo 'output')
                    if hasattr(end, 'receive_input_value'):
                        prev = (end.input_values or {}).get(end_port, None)
                        # Para nodos Output, NO acumular historial: tomar siempre el último valor
                        try:
                            if str(getattr(end, 'node_type', '')).lower() == 'output':
                                new_val = val
                            else:
                                new_val = val
                        except Exception:
                            new_val = val
                        end.receive_input_value(end_port, new_val)
                        now = (end.input_values or {}).get(end_port, None)
                        if now != prev:
                            changed = True
                except Exception:
                    # Conexión rota o nodos sin API
                    pass

            # Si no hubo cambios en inputs, estamos estables
            current_inputs = _snapshot_inputs()
            if current_inputs == last_inputs and not changed:
                break
            last_inputs = current_inputs

        # Post-procesado: permitir que nodos de tipo "output" reflejen valores combinados
        for n in nodes:
            try:
                if str(getattr(n, 'node_type', '')).lower() == 'output':
                    # Si es snapshot, nunca sobrescribir su contenido
                    try:
                        if getattr(n, 'is_snapshot', False):
                            continue
                    except Exception:
                        pass
                    vals = []
                    try:
                        for v in (getattr(n, 'input_values', {}) or {}).values():
                            if v is None:
                                continue
                            if isinstance(v, list):
                                for sv in v:
                                    if sv is not None:
                                        vals.append(str(sv))
                            else:
                                vals.append(str(v))
                    except Exception:
                        pass
                    # Solo actualizar el contenido si hay valores entrantes.
                    # Si no hay entradas, mantener el contenido existente (permite nodos snapshot).
                    if vals:
                        combined = "\n".join(vals)
                        if hasattr(n, 'update_from_text'):
                            n.update_from_text(combined)
            except Exception:
                pass
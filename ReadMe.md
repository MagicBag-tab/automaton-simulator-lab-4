# Visualizador de árboles sintácticos

Este repositorio contiene una herramienta para convertir expresiones regulares (infix) a postfix, mostrar la conversión paso a paso y construir/visualizar el árbol sintáctico.

Video de demostración:
https://youtu.be/G1JCtFw-vEM

Cómo usar

- Asegúrate de tener Python 3.11/3.12 (recomendado) o tu intérprete preferido.
- Instala dependencias si usas la GUI (`pygame`):

```bash
python -m pip install pygame
```

- Ejecuta la aplicación:

```bash
python main.py
```

Qué hace esta versión

- Muestra la conversión infix → postfix con animación.
- Internamente simplifica las extensiones `+` y `?` antes de crear el árbol (se muestran como expandidas en la UI).

Archivos relevantes

- `main.py` — punto de entrada.
- `visualizer.py` — interfaz gráfica y dibujo.
- `postfix.py` — tokenización, conversión y funciones de expansión.
- `syntax_tree.py` — construcción de pasos del árbol sintáctico.

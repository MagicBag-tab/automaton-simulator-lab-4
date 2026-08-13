# Visualizador de Autómatas (Algoritmo de Thompson)

Este repositorio contiene una herramienta interactiva para convertir expresiones regulares (infix) a postfix, mostrar la conversión paso a paso, construir/visualizar el árbol sintáctico, y finalmente **generar, visualizar y simular el Autómata Finito no Determinista (AFN)** utilizando el algoritmo de Thompson.

Video de demostración:
https://youtu.be/SdLeQzmttwQ

## Requisitos y Configuración

- Asegúrate de tener Python 3.11/3.12 (recomendado) o tu intérprete preferido.
- Instala las dependencias necesarias para la interfaz gráfica (`pygame`):

```bash
python -m pip install pygame
```

## Instrucciones de Uso

1. Escribe tus expresiones regulares en el archivo `expresiones.txt` (una por línea).
2. Ejecuta la aplicación desde la terminal:

```bash
python main.py
```

3. **Fase de Consola (Simulación)**: 
   - El programa leerá las expresiones y te pedirá por terminal que ingreses una cadena `w` para probar si es aceptada o no por el AFN generado.
   - Si deseas saltar esta fase y pasar directo al dibujo, simplemente presiona `Ctrl + C`.
4. **Fase Visual (Pygame)**: 
   - Tras terminar las pruebas (o saltarlas), se abrirá automáticamente la ventana gráfica.
   - Verás paso a paso la conversión a Postfix y el Árbol Sintáctico.
   - Haz clic en el botón **"Ver AFN"** para pasar al lienzo inmersivo y ver el grafo resultante del Autómata de Thompson.

## Archivos Relevantes

- `main.py` — Punto de entrada (gestiona la consola y llama a la interfaz).
- `thompson.py` / `afn.py` — Estructuras y algoritmo de construcción del AFN.
- `simulator.py` — Lógica de simulación de cadenas (Cerradura Epsilon y Movimiento).
- `visualizer.py` / `afn_render.py` — Interfaz gráfica y motores de dibujado.
- `postfix.py` — Tokenización, conversión a postfix y funciones de expansión.

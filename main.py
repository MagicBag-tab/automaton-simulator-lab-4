import sys
sys.stdout.reconfigure(encoding='utf-8')
from postfix import conversion_steps, expand_postfix
from thompson import build_afn_from_postfix
from simulator import simulate_afn

def process_regex(regex, w):
    try:
        _, steps = conversion_steps(regex)
        postfix_tokens = steps[-1]["output"]
        expanded_tokens = expand_postfix(postfix_tokens)
        
        afn = build_afn_from_postfix(expanded_tokens)
        
        if simulate_afn(afn, w):
            print("Resultado: sí")
        else:
            print("Resultado: no")
            
    except Exception as e:
        print(f"Error procesando la regex: {e}")

def main():
    try:
        with open("expresiones.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("No se encontró el archivo 'expresiones.txt'.")
        return
        
    print(f"Integración Inicial: Se leyeron {len(lines)} expresiones regulares.\n")
    
    for regex in lines:
        print(f"--- Evaluando: {regex} ---")
        try:
            w = input("Ingrese la cadena w: ")
            process_regex(regex, w)
        except EOFError:
            print("Fin de la entrada.")
            break
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaltando directamente al visualizador...")
        pass
        
    print("Iniciando la interfaz gráfica (Pygame)...")
    from visualizer import VisualizerApp, load_expressions
    try:
        app = VisualizerApp(load_expressions())
        app.run()
    except Exception as e:
        print(f"Error al iniciar Pygame: {e}")

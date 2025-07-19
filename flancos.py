import time, random, os, sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def generar_estímulo():
    # 50% congruente (central →) o incongruente (central ←)
    if random.random() < 0.5:
        return "→ → → → →", 'D'   # D = Derecha
    else:
        return "← ← ← ← ←", 'I'   # I = Izquierda

def presentar_estímulo(cadena):
    clear_screen()
    print(cadena)
    return time.perf_counter()

def leer_respuesta():
    while True:
        resp = input("Dirección (I/D, Q=salir): ").strip().upper()
        if resp in ('I','D','Q'):
            return resp, time.perf_counter()
        print("  Entrada inválida. Escribe I, D o Q y presiona Enter.")

def dar_feedback(acierto, rt):
    if acierto:
        print(f"¡Correcto!   RT = {rt:.0f} ms")
    else:
        print(f"Incorrecto.  RT = {rt:.0f} ms")
    time.sleep(1)

def sumario_bloque(resultados):
    if not resultados:
        print("\nNo hay resultados para mostrar.")
        return
    total = len(resultados)
    correctos = sum(1 for a, _ in resultados if a)
    perc = correctos / total * 100
    rt_med = sum(rt for _, rt in resultados) / total
    print(f"\nResumen del bloque:")
    print(f"  Ensayos: {total}")
    print(f"  Aciertos: {perc:.1f}%")
    print(f"  RT medio: {rt_med:.0f} ms")

def flujo_principal(num_ensayos):
    resultados = []
    for i in range(1, num_ensayos + 1):
        cadena, correcta = generar_estímulo()
        t0 = presentar_estímulo(cadena)
        resp, t1 = leer_respuesta()
        if resp == 'Q':
            print("\nSaliendo antes de completar todos los ensayos.")
            break
        acierto = (resp == correcta)
        rt = (t1 - t0) * 1000
        dar_feedback(acierto, rt)
        resultados.append((acierto, rt))
    sumario_bloque(resultados)
    input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    num_ensayos = int(input("Número de ensayos (default 20): ") or 20)
    flujo_principal(num_ensayos)

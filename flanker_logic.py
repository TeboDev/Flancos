#!/usr/bin/env python3
import os
import sys
import time
import random
import csv
from datetime import datetime
from statistics import mean, stdev

# Lectura no bloqueante Windows/Unix
if os.name == 'nt':
    import msvcrt
else:
    import select

# — Utilidades de pantalla —
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def wait(msg="Pulsa Enter para continuar..."):
    input(msg)

# — Lectura con límite de tiempo —  
def read_response(deadline_ms):
    t0 = time.perf_counter()
    resp = None
    while True:
        elapsed = (time.perf_counter() - t0) * 1000
        if elapsed >= deadline_ms:
            break
        if os.name == 'nt':
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                resp = ch.strip().upper()
                break
        else:
            if select.select([sys.stdin], [], [], 0)[0]:
                resp = sys.stdin.readline().strip().upper()
                break
        time.sleep(0.005)
    return resp or '', elapsed

# — Generación de estímulos con emojis —  
def make_stimulus(cond):
    # H = Happy, A = Angry, N = Neutral
    sym = {
        'F': '😄',
        'E': '😡',
        'N': '😐'
    }

    # Congruente: centro y flancos iguales
    if cond == 'cong':
        center = random.choice(['F','E'])
        flank = center

    # Incongruente: centro distinto de flancos
    elif cond == 'incong':
        center = random.choice(['F','E'])
        flank = 'E' if center == 'F' else 'F'

    # Neutral: centro H/A pero flancos neutrales
    else:
        center = random.choice(['F','E'])
        flank = 'N'

    cadena = f"{sym[flank]} {sym[flank]} {sym[center]} {sym[flank]} {sym[flank]}"
    # devolvemos: cadena, condición del trial y respuesta correcta ('H' o 'A')
    return cadena, cond, center

# — Un ensayo —  
def run_trial(idx, cond, total, cfg, practice_mode):
    clear()
    print(f"Ensayo {idx} / {total}")
    # fijación
    print("\n  +  ")
    time.sleep(cfg['fixation_ms']/1000)

    # estímulo
    stim, condition, correct = make_stimulus(cond)
    print("\n " + stim)
    print("\n(😄 = F   |   😡 = E   |   Q = salir)\n")

    # respuesta
    resp, rt = read_response(cfg['deadline_ms'])
    omision = (resp == '') or (resp == 'Q')
    invalida = (rt < cfg['minrt']) or (rt > cfg['maxrt'])
    acierto = (resp == correct) and not omision and not invalida

    # feedback práctica
    if practice_mode:
        if omision:
            msg = "😶 Omisión"
        elif invalida:
            msg = f"😵 RT inválido ({rt:.0f} ms)"
        elif acierto:
            msg = f"😊 ¡Correcto! ({rt:.0f} ms)"
        else:
            msg = f"😞 Incorrecto ({rt:.0f} ms)"
        print("\n" + msg)
        time.sleep(0.8)
    else:
        # confirmación mínima en bloque experimental
        print("\n👉 Respuesta registrada")
        time.sleep(0.4)

    return {
        'ensayo':   idx,
        'cond':     condition,
        'resp':     resp,
        'correct':  correct,
        'rt':       round(rt,1),
        'acierto':  acierto,
        'omision':  omision,
        'invalida': invalida,
        'timestamp':datetime.now().isoformat()
    }

# — Un bloque de ensayos —  
def run_block(n_trials, start_idx, cfg, practice_mode):
    block = "Práctica" if practice_mode else "Experimental"
    clear()
    print(f"--- Bloque {block}: {n_trials} ensayos ---")
    if practice_mode:
        wait()
    else:
        print("Comienza en 2 segundos...")
        time.sleep(2)

    # preparar condiciones
    types = ['cong','incong','neutral']
    base = n_trials // 3
    counts = [base]*3
    for i in range(n_trials - sum(counts)):
        counts[i] += 1
    conds = sum(([t]*c for t,c in zip(types,counts)), [])
    random.shuffle(conds)

    results = []
    for offset, cond in enumerate(conds):
        idx = start_idx + offset
        res = run_trial(idx, cond, n_trials, cfg, practice_mode)
        results.append(res)
        if res['resp'] == 'Q':
            return results, True

        # ITI con jitter
        wait_time = max(0, cfg['iti_s'] + random.uniform(-cfg['jitter_s'], cfg['jitter_s']))
        time.sleep(wait_time)

        # Pausa cada X ensayos
        if (offset+1) % cfg['breaks'] == 0 and (offset+1) < n_trials:
            clear()
            print("Pausa breve. Pulsa Enter para seguir.")
            wait()
    return results, False

# — Guardar y resumir —  
def save_csv(data, demo, filename):
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    with open(filename,'w',newline='') as f:
        cols = list(demo.keys()) + list(data[0].keys())
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in data:
            row = {**demo, **r}
            w.writerow(row)

def compute_summary(data):
    by_cond = {'cong':[], 'incong':[], 'neutral':[]}
    for r in data:
        if not r['omision'] and not r['invalida']:
            by_cond[r['cond']].append(r['rt'])
    lines = ["=== Resumen Final ==="]
    for name, rts in by_cond.items():
        if rts:
            μ = mean(rts)
            σ = stdev(rts) if len(rts)>1 else 0
            lines.append(f"{name.capitalize():10}: n={len(rts):3}  RTμ={μ:6.1f}±{σ:5.1f} ms")
    if by_cond['cong'] and by_cond['incong']:
        eff = mean(by_cond['incong']) - mean(by_cond['cong'])
        lines.append(f"\nEfecto conflicto (Incong–Cong): {eff:.1f} ms")
    return "\n".join(lines)

# — MAIN interactivo —  
if __name__ == '__main__':
    clear()
    # Por ejemplo, podrías pedir aquí la configuración y luego:
    # results_prac, _ = run_block(cfg['practice'], 1, cfg, True)
    # results_exp, _ = run_block(cfg['trials'], cfg['practice']+1, cfg, False)
    # print(compute_summary(results_prac + results_exp))
    pass

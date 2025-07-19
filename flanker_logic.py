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

# — Generación de estímulos —
def make_stimulus(cond):
    if cond == 'cong':
        center = random.choice(['D','I'])
        flank = center
    elif cond == 'incong':
        center = random.choice(['D','I'])
        flank = 'I' if center=='D' else 'D'
    else:  # neutral
        center = random.choice(['D','I'])
        flank = 'N'
    sym = {'D':'→','I':'←','N':'○'}
    return f"{sym[flank]} {sym[flank]} {sym[center]} {sym[flank]} {sym[flank]}", cond, center

# — Un ensayo —
def run_trial(idx, cond, total, cfg, practice_mode):
    clear()
    print(f"Ensayo {idx} / {total}")
    # fijación
    print("\n  +  ")
    time.sleep(cfg['fixation_ms']/1000)
    # estímulo
    stim, condition, correct = make_stimulus(cond)
    print("\n " + stim + "\n")
    # respuesta
    resp, rt = read_response(cfg['deadline_ms'])
    omision = rt > cfg['deadline_ms']
    invalida = rt < cfg['min_rt'] or rt > cfg['max_rt']
    acierto = (resp == correct) and not omision and not invalida
    # feedback práctica
    if practice_mode:
        if omision:
            msg = "Omisión"
        elif invalida:
            msg = f"RT inválido ({rt:.0f} ms)"
        elif acierto:
            msg = f"Correcto ({rt:.0f} ms)"
        else:
            msg = f"Incorrecto ({rt:.0f} ms)"
        print(msg)
        time.sleep(0.8)
    else:
        # confirmación mínima en bloque experimental
        print("Respuesta registrada")
        time.sleep(0.4)
    return {
        'ensayo': idx,
        'cond': condition,
        'resp': resp,
        'correct': correct,
        'rt': round(rt,1),
        'acierto': acierto,
        'omision': omision,
        'invalida': invalida,
        'timestamp': datetime.now().isoformat()
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
        if res['resp']=='Q':
            return results, True  # interrupción
        time.sleep(max(0, cfg['iti_s'] + random.uniform(-cfg['jitter_s'], cfg['jitter_s'])))
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

def print_summary(all_data):
    by_cond = {'cong':[], 'incong':[], 'neutral':[]}
    for r in all_data:
        if not r['omision'] and not r['invalida']:
            by_cond[r['cond']].append(r['rt'])
    print("\n=== Resumen Final ===")
    for name, rts in by_cond.items():
        if rts:
            μ = mean(rts)
            σ = stdev(rts) if len(rts)>1 else 0.0
            print(f"{name.capitalize():10}: n={len(rts):3}  RTμ={μ:6.1f}±{σ:5.1f} ms")
    if by_cond['cong'] and by_cond['incong']:
        eff = mean(by_cond['incong']) - mean(by_cond['cong'])
        print(f"\nEfecto conflicto (Incong−Cong): {eff:.1f} ms")

def compute_summary(data):
    # devuelve un string con el resumen, idéntico a print_summary()
    by_cond = {'cong':[], 'incong':[], 'neutral':[]}
    for r in data:
        if not r['omision'] and not r['invalida']:
            by_cond[r['cond']].append(r['rt'])
    lines = ["=== Resumen Final ==="]
    for name, rts in by_cond.items():
        if rts:
            μ = mean(rts); σ = stdev(rts) if len(rts)>1 else 0
            lines.append(f"{name.capitalize():10}: n={len(rts):3}  RTμ={μ:6.1f}±{σ:5.1f} ms")
    if by_cond['cong'] and by_cond['incong']:
        eff = mean(by_cond['incong']) - mean(by_cond['cong'])
        lines.append(f"\nEfecto conflicto (Incong–Cong): {eff:.1f} ms")
    return "\n".join(lines)

# — MAIN interactivo —
if __name__=='__main__':
    clear()
   

// static/js/task.js

// Espera ms milisegundos
function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// POST JSON a la ruta indicada
async function postJSON(url, data) {
  await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });
}

async function run() {
  const D = document.getElementById('display');
  let idx = 1;  
  const cfg = window.cfg;  // tu config inyectada en task.html

  // Corre un bloque (práctica o experimental)
  async function runBlock(nTrials, practice) {
    if (practice) {
      alert('Empieza bloque de práctica');
    } else {
      D.textContent = 'Bloque experimental comienza en 2 segundos...';
      await wait(2000);
    }

    // Construye lista de condiciones equilibradas
    const types = ['cong','incong','neutral'];
    let base = Math.floor(nTrials / 3);
    let counts = [base, base, base];
    for (let i = 0; i < nTrials - base*3; i++) counts[i]++;
    let conds = [];
    types.forEach((t,i) => conds.push(...Array(counts[i]).fill(t)));
    conds.sort(() => Math.random() - 0.5);

    // Itera ensayos
    for (let cond of conds) {
      // Fijación
      D.textContent = '+';
      await wait(cfg.fixation_ms);

      // Pide estímulo al servidor
      const resp1 = await fetch(`/trial?cond=${cond}`);
      const { stimulus, correct } = await resp1.json();
      D.textContent = stimulus;

      // Captura respuesta con deadline
      const t0 = performance.now();
      let resp = '';
      function handler(e) {
        const k = e.key.toUpperCase();
        if (['F','E','Q'].includes(k)) {
          resp = k;
          document.removeEventListener('keydown', handler);
        }
      }
      document.addEventListener('keydown', handler);
      while (performance.now() - t0 < cfg.deadline_ms && resp === '') {
        await wait(1);
      }
      document.removeEventListener('keydown', handler);
      const rt = performance.now() - t0;

      // Envía resultado
      const omision = resp === '';
      const invalida = rt < cfg.minrt || rt > cfg.maxrt;
      await postJSON('/response', { 
        idx, cond, resp, rt, omision, invalida, correct 
      });

      // Feedback
      if (practice) {
        let msg;
        if (omision) {
          msg = 'Omisión';
        } else if (invalida) {
          msg = `RT inválido (${Math.round(rt)} ms)`;
        } else if (resp !== correct) {
          msg = 'Incorrecto';
        } else {
          msg = '¡Correcto!';
        }
        D.textContent = `${msg}  RT=${Math.round(rt)} ms`;
        await wait(800);
      } else {
        D.textContent = omision
          ? 'Omisión registrada'
          : 'Respuesta registrada';
        await wait(400);
      }

      // ITI con jitter
      const iti = cfg.iti_s + (Math.random()*2 - 1)*cfg.jitter_s;
      await wait(iti*1000);

      idx++;
    }
  }

  // 1) bloque de práctica
  await runBlock(cfg.practice, true);
  // 2) bloques experimentales
  for (let b = 0; b < cfg.blocks; b++) {
    await runBlock(cfg.trials, false);
  }
  // Al terminar redirige a resumen
  window.location.href = '/summary';
}

window.addEventListener('DOMContentLoaded', run);

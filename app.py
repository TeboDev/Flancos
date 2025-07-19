# app.py
from flask import session, request
from flask import Flask, render_template, request, session, redirect, url_for, send_file
import io
import csv
from datetime import datetime
from flask import (
    Flask, render_template, request, session,
    redirect, url_for, jsonify, send_file
)
from flanker_logic import make_stimulus, compute_summary, save_csv
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'cualquier_cadena_segura'

#  — RUTA DE CONFIGURACIÓN —
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        session['config'] = {
            # -- primero los datos de sujeto --
            'subj':   request.form['subj'],
            'edad':   request.form['edad'],
            'sexo':   request.form['sexo'],

            # -- ahora los parámetros de la tarea --
            'practice':    int(request.form['practice']),
            'blocks':      int(request.form['blocks']),
            'trials':      int(request.form['trials']),
            'deadline_ms': int(request.form['deadline']),
            'fixation_ms': int(request.form['fixation']),
            'minrt':       int(request.form['minrt']),
            'maxrt':       int(request.form['maxrt']),
            'iti_s':       float(request.form['iti']),
            'jitter_s':    float(request.form['jitter']),
            'breaks':      int(request.form['breaks']),
        }
        session['results'] = []
        return redirect(url_for('task'))
    return render_template('index.html')

#  — PANTALLA DE PRUEBA (cliente se encarga de la temporización) —
@app.route('/task')
def task():
    cfg = session.get('config')
    if not cfg:
        return redirect(url_for('index'))
    return render_template('task.html', config=cfg)

#  — SERVIR UN TRIAL (estímulo) —
@app.route('/trial')
def trial():
    cond = request.args.get('cond')
    stim, _cond_name, correct = make_stimulus(cond)
    return jsonify({'stimulus': stim, 'correct': correct})


#  — RECIBIR RESPUESTA POST AJAX —


@app.route('/response', methods=['POST'])
def response():
    data = request.get_json() or {}

    # 1) Aseguramos que session['results'] exista
    if 'results' not in session:
        session['results'] = []

    # 2) Construimos el registro usando get() para no lanzar KeyError
    record = {
        'ensayo':    data.get('idx'),
        'cond':      data.get('cond'),
        'resp':      data.get('resp'),
        'correct':   data.get('correct'),
        'rt':        data.get('rt'),
        'omision':   data.get('omision', False),
        'invalida':  data.get('invalida', False),
        'timestamp': datetime.now().isoformat()
    }

    # 3) Añadimos y forzamos a Flask a actualizar la sesión
    session['results'].append(record)
    session.modified = True

    return ('', 204)


#  — PANTALLA DE RESUMEN Y CSV —
@app.route('/summary')
def summary():
    results = session.get('results', [])
    summary_text = compute_summary(results)
    return render_template('summary.html', summary=summary_text)

#  — DESCARGA DEL CSV —
import io
from flask import make_response

@app.route('/download_csv')
def download_csv():
    results = session.get('results', [])
    config  = session.get('config', {})

    if not results:
        return redirect(url_for('index'))

    # Datos demográficos
    demo = {
        'id':    config.get('subj','noid'),
        'edad':  config.get('edad',''),
        'sexo':  config.get('sexo',''),
        'fecha': datetime.now().isoformat()
    }

    # Creamos un StringIO en memoria
    si = io.StringIO()
    # Cabeceras: datos demográficos + columnas de cada ensayo
    fieldnames = list(demo.keys()) + list(results[0].keys())
    writer = csv.DictWriter(si, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow({**demo, **r})

    # Volcamos el contenido a la respuesta HTTP
    output = make_response(si.getvalue())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"flanker_{demo['id']}_{timestamp}.csv"

    output.headers['Content-Disposition'] = f'attachment; filename={filename}'
    output.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return output

    # Envía el archivo al cliente como descarga
    return send_file(fname, as_attachment=True)
if __name__ == '__main__':
    app.run(debug=True)

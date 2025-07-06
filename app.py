import json
import os
import csv
import sqlite3
import time
import eventlet

eventlet.monkey_patch()

from io import StringIO
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for, request,
    jsonify, session, make_response
)
from flask_socketio import SocketIO, emit
from flask_sock import Sock

from config import DADOS_DB, INTERVALO_GRAVACAO, VALOR_KWH
from database.init_db import init_dados_db, init_users_db
from database.users import validar_usuario, criar_usuario, usuario_existe
from database.devices import validar_dispositivo
from database.utils import (
    salvar_historico, registrar_evento,
    buscar_historico, buscar_eventos
)
from utils.timezone_utils import utc_to_local, local_to_utc
from utils.alarms import verificar_e_registrar_alarmes
from utils.energy_calc import calcular_acumulado_mensal
from utils.historico_query import buscar_dados_periodo
from utils.statistics import calcular_estatisticas_periodo
from utils.energy_forecast import calcular_previsao_consumo
from export.export_monthly_csv import exportar_csv
from export.export_monthly_pdf import exportar_pdf
from routes.devices_web import devices_web
from routes.devices import devices_bp


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
sock = Sock(app)
socketio = SocketIO(app, async_mode='eventlet')
app.register_blueprint(devices_bp)
app.register_blueprint(devices_web)

# Variável para rastrear último contato do ESP
ultimo_contato_esp = None
ultimo_gravado = None

# Inicialização dos bancos
init_dados_db()
init_users_db()

# Decorador de login obrigatório
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

# ROTAS PRINCIPAIS ------------------------

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['username'])

@app.route('/historico', methods=['GET'])
@login_required
def historico():
    # Range de datas disponível no banco
    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM historico')
    min_ts, max_ts = cursor.fetchone()
    conn.close()

    # Filtros vindos do formulário
    data_inicio_raw = request.args.get('inicio')
    data_fim_raw = request.args.get('fim')
    corrente_min = request.args.get('corrente_min')
    corrente_max = request.args.get('corrente_max')
    tensao_min = request.args.get('tensao_min')
    tensao_max = request.args.get('tensao_max')
    limite = request.args.get('limite', 10, type=int)
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * limite

    query = 'SELECT timestamp, corrente, tensao, potencia FROM historico WHERE 1=1'
    params = []

    # Convertendo datas locais para UTC antes da consulta
    data_inicio = local_to_utc(data_inicio_raw) if data_inicio_raw else None
    data_fim = local_to_utc(data_fim_raw) if data_fim_raw else None

    if data_inicio:
        query += ' AND timestamp >= ?'
        params.append(data_inicio)
    if data_fim:
        query += ' AND timestamp <= ?'
        params.append(data_fim)
    if corrente_min:
        query += ' AND corrente >= ?'
        params.append(float(corrente_min))
    if corrente_max:
        query += ' AND corrente <= ?'
        params.append(float(corrente_max))
    if tensao_min:
        query += ' AND tensao >= ?'
        params.append(float(tensao_min))
    if tensao_max:
        query += ' AND tensao <= ?'
        params.append(float(tensao_max))

    query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([limite, offset])

    rows = buscar_historico(query, params)

    # Converter UTC para Local antes de enviar ao template
    rows_converted = []
    for row in rows:
        local_timestamp = utc_to_local(row[0])
        rows_converted.append((local_timestamp, row[1], row[2], row[3]))

    # Preparar navegação de página
    next_page = page + 1
    prev_page = page - 1 if page > 1 else 1

    return render_template('historico.html',
                           rows=rows_converted,
                           min_ts=utc_to_local(min_ts),
                           max_ts=utc_to_local(max_ts),
                           page=page,
                           next_page=next_page,
                           prev_page=prev_page,
                           limit=limite)

@app.route('/exportar_dados')
@login_required
def exportar_dados():
    try:
        exportar_csv()
        exportar_pdf()
        mensagem = "✅ Exportação CSV e PDF concluída com sucesso!"
    except Exception as e:
        mensagem = f"❌ Erro durante exportação: {str(e)}"

    return render_template('exportar.html', mensagem=mensagem)

@app.route('/dados_periodo')
@login_required
def dados_periodo():
    tipo = request.args.get('periodo', 'ultima_hora')
    inicio_str = request.args.get('inicio')
    fim_str = request.args.get('fim')

    inicio = None
    fim = datetime.now(timezone.utc)

    if tipo == 'personalizado' and inicio_str and fim_str:
        try:
            from utils.timezone_utils import local_to_utc
            inicio_utc_str = local_to_utc(inicio_str)
            fim_utc_str = local_to_utc(fim_str)
            inicio = datetime.strptime(inicio_utc_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            fim = datetime.strptime(fim_utc_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        except:
            return jsonify({'erro': 'Formato de data inválido'}), 400

    timestamps, correntes, tensoes, potencias = buscar_dados_periodo(tipo, inicio, fim)

    return jsonify({
        'timestamps': timestamps,
        'correntes': correntes,
        'tensoes': tensoes,
        'potencias': potencias
    })

@app.route('/eventos')
@login_required
def eventos():
    rows = buscar_eventos()

    # Converter os timestamps para horário local
    from utils.timezone_utils import utc_to_local
    eventos_convertidos = []
    for row in rows:
        local_timestamp = utc_to_local(row[0])
        eventos_convertidos.append((local_timestamp, row[1], row[2]))

    return render_template('eventos.html', eventos=eventos_convertidos)

@app.route('/exportar_eventos_csv')
@login_required
def exportar_eventos_csv():
    eventos = buscar_eventos(limit=1000)  # Exportar até os últimos 1000 eventos (ajuste se quiser)

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Data/Hora', 'Tipo', 'Mensagem'])

    for row in eventos:
        local_ts = utc_to_local(row[0])
        writer.writerow([local_ts, row[1], row[2]])

    output = make_response(si.getvalue())
    data_hoje = datetime.now().strftime('%Y%m%d')
    output.headers['Content-Disposition'] = f'attachment; filename=eventos_{data_hoje}.csv'
    output.headers['Content-type'] = 'text/csv'
    return output

@app.route('/ultimo_alarme')
@login_required
def ultimo_alarme():
    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, mensagem FROM eventos ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()

    if row:
        return {'timestamp': utc_to_local(row[0]), 'mensagem': row[1]}
    return {'mensagem': None}

@app.route('/status_esp')
@login_required
def status_esp():
    global ultimo_contato_esp
    agora = datetime.now(timezone.utc)

    if ultimo_contato_esp:
        delta = (agora - ultimo_contato_esp).total_seconds()
        if delta < 5:
            return {'status': 'online'}
        else:
            return {'status': 'offline', 'ultima_comunicacao': utc_to_local(ultimo_contato_esp.strftime('%Y-%m-%d %H:%M:%S'))}
    else:
        return {'status': 'desconhecido'}

@app.route('/acumulado_mensal')
@login_required
def acumulado_mensal():
    energia_kwh, custo_reais = calcular_acumulado_mensal()
    return jsonify({'energia_kwh': energia_kwh, 'custo_reais': custo_reais})

@app.route('/estatisticas')
@login_required
def estatisticas():
    fim = local_to_utc(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')  # Últimos 30 dias

    stats = calcular_estatisticas_periodo(inicio, fim)

    if stats is None:
        return render_template('estatisticas.html', erro='Sem dados para o período.')

    return render_template('estatisticas.html', stats=stats)

@app.route('/previsao_consumo')
@login_required
def previsao_consumo():
    energia_atual, estimado = calcular_previsao_consumo()
    return jsonify({
        'consumo_atual_kwh': energia_atual,
        'consumo_estimado_kwh': estimado,
        'custo_estimado': estimado * VALOR_KWH
    })

# WebSocket para receber dados do ESP
# @socketio.on('new_data')
# def handle_new_data(data):
#     global ultimo_contato_esp, ultimo_gravado
#
#     device_id = data.get('device_id')
#     token = data.get('token')
#
#     if not validar_dispositivo(device_id, token):
#         print(f"Tentativa de conexão inválida! Device: {device_id}, Token: {token}")
#         return  # Ignora dados inválidos
#
#     ultimo_contato_esp = datetime.now(timezone.utc)
#     timestamp_utc = ultimo_contato_esp.strftime('%Y-%m-%d %H:%M:%S')
#
#     corrente = data.get('corrente')
#     tensao = data.get('tensao')
#     potencia = data.get('potencia')
#
#     # Checar se já se passaram pelo menos 500ms desde a última gravação
#     agora = datetime.now(timezone.utc)
#     if not ultimo_gravado or (agora - ultimo_gravado).total_seconds() >= INTERVALO_GRAVACAO:
#         verificar_e_registrar_alarmes(corrente, tensao, potencia, timestamp_utc)
#         salvar_historico(timestamp_utc, corrente, tensao, potencia)
#         ultimo_gravado = agora
#
#     # Continua transmitindo os dados ao Dashboard em tempo real (não afeta)
#     emit('new_data', data, broadcast=True)


@sock.route('/ws')  # ou outro path de sua escolha
def ws_receive(ws):
    global ultimo_contato_esp, ultimo_gravado

    while True:
        msg = ws.receive()
        if msg is None:
            # Conexão fechou do lado do ESP
            break
        print(msg)
        try:
            data = json.loads(msg)
        except ValueError:
            # Mensagem não era JSON válido
            app.logger.warning('WS puro recebeu payload inválido')
            continue

        # Validação de device_id e token
        device_id = data.get('device_id')
        token     = data.get('token')
        if not validar_dispositivo(device_id, token):
            app.logger.warning(f'Tentativa inválida: {device_id} / {token}')
            continue

        # Marca último contato
        ultimo_contato_esp = datetime.now(timezone.utc)
        timestamp_utc = ultimo_contato_esp.strftime('%Y-%m-%d %H:%M:%S')

        corrente = data.get('corrente')
        tensao   = data.get('tensao')
        potencia = data.get('potencia')

        # Grava no histórico a cada INTERVALO_GRAVACAO
        agora = datetime.now(timezone.utc)
        if not ultimo_gravado or (agora - ultimo_gravado).total_seconds() >= INTERVALO_GRAVACAO:
            verificar_e_registrar_alarmes(corrente, tensao, potencia, timestamp_utc)
            salvar_historico(timestamp_utc, corrente, tensao, potencia)
            ultimo_gravado = agora

        # Rebroadcast para os clientes web conectados ao Flask-SocketIO
        socketio.emit('new_data', data)

        # Opcional: enviar um ACK de volta ao ESP
        ws.send('OK')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if validar_usuario(username, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', erro='Credenciais inválidas')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if usuario_existe(username):
            return render_template('cadastro.html', erro='Usuário já existe.')

        criar_usuario(username, password)
        return redirect(url_for('login'))

    return render_template('cadastro.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

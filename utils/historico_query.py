from config import DADOS_DB
import sqlite3
from datetime import datetime, timezone, timedelta
from utils.timezone_utils import utc_to_local

def buscar_dados_periodo(tipo, inicio=None, fim=None):
    agora = datetime.now(timezone.utc)

    if tipo == 'ultima_hora':
        inicio = agora - timedelta(hours=1)
    elif tipo == 'ultimo_dia':
        inicio = agora - timedelta(days=1)
    elif tipo == 'ultimos_7_dias':
        inicio = agora - timedelta(days=7)
    elif tipo == 'personalizado':
        # Aqui os parâmetros inicio e fim já devem estar como datetime UTC-aware
        if not inicio or not fim:
            return [], [], [], []

    inicio_str = inicio.strftime('%Y-%m-%d %H:%M:%S')
    fim_str = fim.strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, corrente, tensao, potencia FROM historico WHERE timestamp BETWEEN ? AND ? ORDER BY id ASC', (inicio_str, fim_str))
    rows = cursor.fetchall()
    conn.close()

    timestamps = [utc_to_local(r[0]) for r in rows]
    correntes = [r[1] for r in rows]
    tensoens = [r[2] for r in rows]
    potencias = [r[3] for r in rows]

    return timestamps, correntes, tensoens, potencias

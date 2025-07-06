from config import DADOS_DB, VALOR_KWH
import sqlite3
from datetime import datetime, timezone, timedelta
from utils.timezone_utils import local_to_utc

def calcular_acumulado_mensal():
    agora = datetime.now(timezone.utc)
    if agora.day >= 13:
        inicio = agora.replace(day=13)
    else:
        inicio = (agora.replace(day=1) - timedelta(days=1)).replace(day=13)

    inicio_str = inicio.strftime('%Y-%m-%d %H:%M:%S')
    fim_str = agora.strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, potencia FROM historico WHERE timestamp BETWEEN ? AND ?', (inicio_str, fim_str))
    rows = cursor.fetchall()
    conn.close()

    energia_kwh = 0
    ultimo_tempo = None

    for row in rows:
        timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        potencia = row[1]

        if ultimo_tempo:
            delta_horas = (timestamp - ultimo_tempo).total_seconds() / 3600
            energia_kwh += (potencia / 1000) * delta_horas

        ultimo_tempo = timestamp

    custo_reais = energia_kwh * VALOR_KWH
    return energia_kwh, custo_reais

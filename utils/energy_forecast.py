import sqlite3
from datetime import datetime, timezone, timedelta
from config import DADOS_DB

def calcular_previsao_consumo():
    agora = datetime.now(timezone.utc)

    if agora.day >= 13:
        inicio = agora.replace(day=13, hour=0, minute=0, second=0, microsecond=0)
    else:
        mes_anterior = agora.replace(day=1) - timedelta(days=1)
        inicio = mes_anterior.replace(day=13, hour=0, minute=0, second=0, microsecond=0)

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

    horas_passadas = (agora - inicio).total_seconds() / 3600
    if horas_passadas > 0:
        media_kwh_por_hora = energia_kwh / horas_passadas
    else:
        media_kwh_por_hora = 0

    # Calcular horas restantes até o fim do mês
    proximo_mes = (agora.replace(day=28) + timedelta(days=4)).replace(day=1)
    fim_mes = proximo_mes - timedelta(seconds=1)
    horas_restantes = (fim_mes - agora).total_seconds() / 3600

    consumo_estimado = energia_kwh + (media_kwh_por_hora * horas_restantes)

    return energia_kwh, consumo_estimado

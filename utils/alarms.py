from config import ALARMES
from database.utils import registrar_evento

def verificar_e_registrar_alarmes(corrente, tensao, potencia, timestamp):
    if corrente > ALARMES['corrente_max']:
        registrar_evento(timestamp, 'ALERTA', f'Corrente alta: {corrente:.2f}A')

    if tensao < ALARMES['tensao_min'] or tensao > ALARMES['tensao_max']:
        registrar_evento(timestamp, 'ALERTA', f'Tensão fora dos limites: {tensao:.2f}V')

    if potencia > ALARMES['potencia_max']:
        registrar_evento(timestamp, 'ALERTA', f'Potência alta: {potencia:.2f}W')

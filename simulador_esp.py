import socketio
import random
import time

# Cria cliente SocketIO
sio = socketio.Client()

try:
    while True:
        # Conecta ao servidor Flask-SocketIO
        sio.connect('http://localhost:5000')

        print("Simulador ESP32 conectado ao servidor WebSocket!")

        while True:
            # Gera valores aleatórios simulados
            corrente = round(random.uniform(0, 10), 2)
            tensao = round(random.uniform(200, 240), 2)
            potencia = round(corrente * tensao, 2)

            # Monta o JSON
            dados = {
                'corrente': corrente,
                'tensao': tensao,
                'potencia': potencia,
                'token': '9fGx2pL7qVb5Zr1C',
                'device_id': 'ESP001'
            }

            # Envia via WebSocket
            sio.emit('new_data', dados)
            print(f"Enviado: {dados}")

            # Aguarda 0.5 segundo antes do próximo envio
            time.sleep(0.5)

except KeyboardInterrupt:
    print("Simulador encerrado manualmente.")
    sio.disconnect()

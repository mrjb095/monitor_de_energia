import os
from dotenv import load_dotenv

# Carregar as variáveis do arquivo .env
load_dotenv('.env')

DADOS_DB='dados.db'
USERS_DB='users.db'

# Configuração do banco de dados PostgreSQL
POSTGRESQL_URL = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': int(os.getenv('POSTGRES_PORT'))
}

# Tarifa de energia
VALOR_KWH = float(os.getenv('VALOR_KWH'))

# Intervalo de gravação (em segundos)
INTERVALO_GRAVACAO = int(os.getenv('INTERVALO_GRAVACAO'))

# Chave secreta Flask (para sessões, cookies etc)
SECRET_KEY = os.getenv('SECRET_KEY')

# Outras configurações opcionais que você pode adicionar no futuro:
# DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
ALARMES = {
    'corrente_max': 10,   # Exemplo: Corrente acima de 10A
    'tensao_min': 209,    # Exemplo: Tensão abaixo de 200V
    'tensao_max': 231,    # Exemplo: Tensão acima de 240V
    'potencia_max': 2200  # Exemplo: Potência acima de 2200W
}
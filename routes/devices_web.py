from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, abort
)
#from flask_login import login_required
import requests

from database.utils import get_device_by_id

devices_web = Blueprint('devices_web', __name__)

API_PREFIX = '/api/devices'

@devices_web.route('/devices')
#@login_required
def list_devices():
    # busca todos os devices do banco
    devices = get_device_by_id()
    return render_template('devices.html', devices=devices)


@devices_web.route('/devices/<device_id>', methods=['GET', 'POST'])
#@login_required
def device_detail(device_id):
    # busca o registro no banco
    device = get_device_by_id(device_id)
    if not device:
        abort(404, 'Dispositivo não encontrado')

    # URL base para chamar a API de devices
    base = f'http://localhost:5000{API_PREFIX}/{device_id}'

    if request.method == 'POST':
        # pega campos do formulário
        payload = {}
        if 'serverIP' in request.form:
            payload['serverIP'] = request.form['serverIP']
        if 'serverPort' in request.form:
            payload['serverPort'] = request.form['serverPort']
        if 'intervalo' in request.form:
            payload['intervalo'] = int(request.form['intervalo'])

        # envia para o ESP via nossa API
        r = requests.post(f'{base}/config', json=payload, timeout=30)
        if r.status_code == 200:
            flash('Configuração enviada com sucesso', 'success')
        else:
            flash(f'Erro ao configurar: {r.text}', 'danger')

        return redirect(url_for('devices_web.device_detail', device_id=device_id))

    # GET: coleta status, config e health
    try:
        status  = requests.get(f'{base}/status', timeout=30).json()
        config  = requests.get(f'{base}/config', timeout=30).json()
        health  = requests.get(f'{base}/health', timeout=30).json()
    except requests.RequestException as e:
        flash(f'Erro de conexão: {e}', 'warning')
        status = config = health = {}

    return render_template(
        'device_detail.html',
        device=device,
        status=status,
        config=config,
        health=health
    )

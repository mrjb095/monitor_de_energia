# routes/devices.py
import requests
from flask import Blueprint, jsonify, request, current_app, abort
from flask_login import login_required
from database.utils import get_device_by_id

devices_bp = Blueprint('devices', __name__, url_prefix='/api/devices')

def _build_url(device, path):
    print(f'http://{device["ip"]}{path}')
    return f'http://{device["ip"]}{path}'

@devices_bp.route('', methods=['GET'])
#@login_required
def list_devices():
    # get_device_by_id(None) => retorna todos
    devices = get_device_by_id()
    return jsonify([{
        'device_id': d['device_id'],
        'ip': d['ip'],
        'port': d['port'],
        'last_seen': d['last_seen']
    } for d in devices])

@devices_bp.route('<device_id>/status', methods=['GET'])
#@login_required
def device_status(device_id):
    device = get_device_by_id(device_id)
    if not device:
        abort(404, 'Device não encontrado')
    try:
        r = requests.get(_build_url(device, '/status'), timeout=30)
        return jsonify(r.json())
    except requests.RequestException as e:
        current_app.logger.error(f"Erro de conexão com {device_id}: {e}")
        abort(502, 'Falha ao conectar com o dispositivo')

@devices_bp.route('<device_id>/config', methods=['GET'])
#@login_required
def device_get_config(device_id):
    device = get_device_by_id(device_id)
    if not device:
        abort(404, 'Device não encontrado')
    try:
        r = requests.get(_build_url(device, '/config'), timeout=30)
        return jsonify(r.json())
    except requests.RequestException as e:
        current_app.logger.error(f"Erro de conexão com {device_id}: {e}")
        abort(502, 'Falha ao conectar com o dispositivo')

@devices_bp.route('<device_id>/config', methods=['POST'])
#@login_required
def device_set_config(device_id):
    device = get_device_by_id(device_id)
    if not device:
        abort(404, 'Device não encontrado')
    payload = request.get_json(force=True)
    try:
        r = requests.post(
            _build_url(device, '/config'),
            json=payload,
            timeout=5
        )
        return jsonify(r.json()), r.status_code
    except requests.RequestException as e:
        current_app.logger.error(f"Erro de conexão com {device_id}: {e}")
        abort(502, 'Falha ao conectar com o dispositivo')

@devices_bp.route('<device_id>/restart', methods=['POST'])
#@login_required
def device_restart(device_id):
    device = get_device_by_id(device_id)
    if not device:
        abort(404, 'Device não encontrado')
    try:
        r = requests.post(_build_url(device, '/restart'), timeout=30)
        return jsonify(r.json()), r.status_code
    except requests.RequestException as e:
        current_app.logger.error(f"Erro de conexão com {device_id}: {e}")
        abort(502, 'Falha ao conectar com o dispositivo')

@devices_bp.route('<device_id>/health', methods=['GET'])
#@login_required
def device_health(device_id):
    device = get_device_by_id(device_id)
    if not device:
        abort(404, 'Device não encontrado')
    try:
        r = requests.get(_build_url(device, '/health'), timeout=30)
        return jsonify(r.json())
    except requests.RequestException as e:
        current_app.logger.error(f"Erro de conexão com {device_id}: {e}")
        abort(502, 'Falha ao conectar com o dispositivo')

from flask import Flask, request, jsonify
import pyads
import time
import threading
 
app = Flask(__name__)
 
# Local AMS Net ID
LOCAL_AMS_NET_ID = '192.168.0.20.1.1'
 
pyads.set_local_address(LOCAL_AMS_NET_ID)
 
# ADS connection settings 
PLC_AMS_NET_ID = '5.13.228.76.1.1'     
PLC_IP_ADDRESS = '192.168.0.10'      
PLC_PORT = 801 
 
# PLC Symbol Names
SYM_START = '.GAUTOMATICCONTROLS.BSTART'
SYM_STOP = '.GAUTOMATICCONTROLS.BSTOP'
SYM_MODE = '.BMODE'


POSITION_SYMBOLS = {
'x': '.GPOSITION.FPOS_X',
'y': '.GPOSITION.FPOS_Y',
'z': '.GCPOSITION.FPOS_Z',
}

SETTINGS_SYMBOLS = {
    'thickness': '.FSET_MATERIAL_THICKNESS',
    'speed': '.FSET_SPEED',
}

JOG_SYMBOLS = {
    ('x', 'plus'): '.GMANUALCONTROLS.BJOG_X_PLUS',
    ('x', 'minus'): '.GMANUALCONTROLS.BJOG_X_MINUS',
    ('y', 'plus'): '.GMANUALCONTROLS.BJOG_Y_PLUS',
    ('y', 'minus'): '.GMANUALCONTROLS.BJOG_Y_MINUS',
    ('z', 'plus'): '.GMANUALCONTROLS.BJOG_Z_PLUS',
    ('z', 'minus'): '.GMANUALCONTROLS.BJOG_Z_MINUS',
}

AXIS_TOGGLE_SYMBOLS = {
    'x': '.GMANUALCONTROLS.BAXIS_X_ENABLE',
    'y': '.GMANUALCONTROLS.BAXIS_Y_ENABLE',
    'z': '.GMANUALCONTROLS.BAXIS_Z_ENABLE',
}


AXIS_ACTION_SYMBOLS = {
    ('x', 'reset'): '.GMANUALCONTROLS.BAXIS_X_RESET',
    ('x', 'stop'): '.GMANUALCONTROLS.BAXIS_X_STOP',
    ('y', 'reset'): '.GMANUALCONTROLS.BAXIS_Y_RESET',
    ('y', 'stop'): '.GMANUALCONTROLS.BAXIS_Y_STOP',
    ('z', 'reset'): '.GMANUALCONTROLS.BAXIS_Z_RESET',
    ('z', 'stop'): '.GMANUALCONTROLS.BAXIS_Z_STOP',
}

plc_connection = None
plc_lock = threading.Lock()


def get_plc():
    return pyads.Connection(PLC_AMS_NET_ID, PLC_PORT, PLC_IP_ADDRESS)
 
# Position
@app.route('/position', methods=['GET'])
def get_position():
    with get_plc() as plc:
      x = plc.read_by_name(POSITION_SYMBOLS['x'], pyads.PLCTYPE_LREAL)
      y = plc.read_by_name(POSITION_SYMBOLS['y'], pyads.PLCTYPE_LREAL)
      z = plc.read_by_name(POSITION_SYMBOLS['z'], pyads.PLCTYPE_LREAL)
    return jsonify({'x': x, 'y': y, 'z': z})


# Mode
@app.route('/mode', methods=['GET'])
def get_mode():
    with get_plc() as plc:
       value = plc.read_by_name(SYM_MODE, pyads.PLCTYPE_BOOL)
    return ('1' if value else '0')
 
@app.route('/mode', methods=['POST'])
def set_mode():
    value = request.args.get('value')
    if value not in ('0', '1'):
        return 'Invalid value', 400

    with get_plc() as plc:
       plc.write_by_name(SYM_MODE, value == '1', pyads.PLCTYPE_BOOL)
    return 'OK'
 
# Commands Automat
@app.route('/command', methods=['POST'])
def send_command():
    button = request.args.get('button')
    state = request.args.get('state')
    symbol_map = {'start': SYM_START, 'stop': SYM_STOP}

    if button not in symbol_map or state not in ('0', '1'):
        return 'Invalid parameters', 400

    with get_plc() as plc:
       plc.write_by_name(symbol_map[button], state == '1', pyads.PLCTYPE_BOOL)
    return 'OK'
 

# Settings 
@app.route('/settings', methods=['GET'])
def get_settings():
    plc = get_plc()
    thickness = plc.read_by_name(SETTINGS_SYMBOLS['thickness'], pyads.PLCTYPE_LREAL)
    speed = plc.read_by_name(SETTINGS_SYMBOLS['speed'], pyads.PLCTYPE_LREAL)
    return jsonify({'thickness': thickness, 'speed': speed})

@app.route('/settings', methods=['POST'])
def set_settings():
    key = request.args.get('key')
    value = request.args.get('value')

    if key not in SETTINGS_SYMBOLS:
        return 'Invalid parameters', 400

    try:
        value = float(value)
    except (TypeError, ValueError):
        return 'Invalid parameters', 400

    if value < 0:
        return 'Invalid parameters', 400

    with get_plc() as plc:
       plc.write_by_name(SETTINGS_SYMBOLS[key], value, pyads.PLCTYPE_LREAL)
    return 'OK'

# Axis
@app.route('/axis', methods=['GET'])
def get_axis():
    with get_plc() as plc:
       x = plc.read_by_name(AXIS_TOGGLE_SYMBOLS['x'], pyads.PLCTYPE_BOOL)
       y = plc.read_by_name(AXIS_TOGGLE_SYMBOLS['y'], pyads.PLCTYPE_BOOL)
       z = plc.read_by_name(AXIS_TOGGLE_SYMBOLS['z'], pyads.PLCTYPE_BOOL)
    return jsonify({
        'x': '1' if x else '0',
        'y': '1' if y else '0',
        'z': '1' if z else '0',
    })


@app.route('/axis', methods=['POST'])
def set_axis():
    axis = request.args.get('axis')
    value = request.args.get('value')

    if axis not in AXIS_TOGGLE_SYMBOLS or value not in ('0', '1'):
        return 'Invalid parameters', 400

    with get_plc() as plc:
       plc.write_by_name(AXIS_TOGGLE_SYMBOLS[axis], value == '1', pyads.PLCTYPE_BOOL)
    return 'OK'


# Axis Action Controls
@app.route('/axis_action', methods=['POST'])
def axis_action():
    axis = request.args.get('axis')
    action = request.args.get('action')
    state = request.args.get('state')

    key = (axis, action)
    if key not in AXIS_ACTION_SYMBOLS or state not in ('0', '1'):
        return 'Invalid parameters', 400

    with get_plc() as plc:
      plc.write_by_name(AXIS_ACTION_SYMBOLS[key], state == '1', pyads.PLCTYPE_BOOL)
    return 'OK'

# Jog Controls
@app.route('/jog', methods=['POST'])
def jog():
    axis = request.args.get('axis')
    direction = request.args.get('dir')
    state = request.args.get('state')

    key = (axis, direction)
    if key not in JOG_SYMBOLS or state not in ('0', '1'):
        return 'Invalid parameters', 400

    with get_plc() as plc:
       plc.write_by_name(JOG_SYMBOLS[key], state == '1', pyads.PLCTYPE_BOOL)
    return 'OK'
 
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

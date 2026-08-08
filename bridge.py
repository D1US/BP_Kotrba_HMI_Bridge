from flask import Flask, request, jsonify
import pyads
 
app = Flask(__name__)
 
# ===== ADS connection settings =====
# TODO: replace with your real PLC's AMS Net ID and port once known
PLC_AMS_NET_ID = '5.13.228.76.1.1'
PLC_PORT = 801  # standard TwinCAT 3 PLC runtime port
 
# ===== PLC symbol names (from your TwinCAT project) =====
SYM_START = 'bStart'
SYM_STOP = 'bStop'
SYM_MODE = 'bMode'
 
SYM_POS_X = 'fPos_x'
SYM_POS_Y = 'fPos_y'
SYM_POS_Z = 'fPos_z'
 
JOG_SYMBOLS = {
    ('x', 'plus'): 'bJog_x_plus',
    ('x', 'minus'): 'bJog_x_minus',
    ('y', 'plus'): 'bJog_y_plus',
    ('y', 'minus'): 'bJog_y_minus',
    ('z', 'plus'): 'bJog_z_plus',
    ('z', 'minus'): 'bJog_z_minus',
}
 
 
def get_plc():
    return pyads.Connection(PLC_AMS_NET_ID, PLC_PORT)
 
 
@app.route('/position', methods=['GET'])
def get_position():
    with get_plc() as plc:
        x = plc.read_by_name(SYM_POS_X, pyads.PLCTYPE_INT)
        y = plc.read_by_name(SYM_POS_Y, pyads.PLCTYPE_INT)
        z = plc.read_by_name(SYM_POS_Z, pyads.PLCTYPE_INT)
    return jsonify({'x': x, 'y': y, 'z': z})
 
 
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
 
 
@app.route('/command', methods=['POST'])
def send_command():
    button = request.args.get('button')
    symbol_map = {'start': SYM_START, 'stop': SYM_STOP}
 
    if button not in symbol_map:
        return 'Invalid button', 400
 
    with get_plc() as plc:
        plc.write_by_name(symbol_map[button], True, pyads.PLCTYPE_BOOL)
    return 'OK'
 
 
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
    # Bound to 0.0.0.0 so other containers on the same Docker network can
    # reach it via the Compose service name (e.g. http://bridge:5000).
    # NOT exposed to the host/outside world as long as this container has
    # no "ports:" mapping in docker-compose.yml.
    app.run(host='0.0.0.0', port=5000)

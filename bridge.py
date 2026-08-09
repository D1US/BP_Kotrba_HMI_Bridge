from flask import Flask, request, jsonify
import pyads

app = Flask(__name__)

# ===== Local AMS Net ID (this Pi/bridge's identity on the ADS network) =====
LOCAL_AMS_NET_ID = '192.168.0.20.1.1'

pyads.set_local_address(LOCAL_AMS_NET_ID)

# ===== ADS connection settings =====
PLC_AMS_NET_ID = '5.13.228.76.1.1'
PLC_IP_ADDRESS = '192.168.0.10'
PLC_PORT = 801  # TwinCAT 2 PLC runtime port (801 = first runtime instance)

# ===== PLC symbol names (from your TwinCAT project) =====
# Confirmed via a debug symbol dump against the real running PLC - these are
# flat global variables (leading dot, no GVL grouping), all uppercase.
SYM_POS_X = '.FPOS_X'
SYM_POS_Y = '.FPOS_Y'
SYM_POS_Z = '.FPOS_Z'
SYM_MODE = '.BMODE'

# ===== Momentary/hold-type outputs =====
# Start, Stop, and all six jog directions are all the *same kind* of thing:
# a boolean the browser sets to True on press and False on release. They
# all share this one lookup table and are written through the single
# /write endpoint below - there is no separate code path for Start/Stop
# vs Jog, so they behave identically by construction.
WRITE_SYMBOLS = {
    'start': '.BSTART',
    'stop': '.BSTOP',
    'jog_x_plus': '.BJOG_X_PLUS',
    'jog_x_minus': '.BJOG_X_MINUS',
    'jog_y_plus': '.BJOG_Y_PLUS',
    'jog_y_minus': '.BJOG_Y_MINUS',
    'jog_z_plus': '.BJOG_Z_PLUS',
    'jog_z_minus': '.BJOG_Z_MINUS',
}


def get_plc():
    return pyads.Connection(PLC_AMS_NET_ID, PLC_PORT, PLC_IP_ADDRESS)


@app.route('/position', methods=['GET'])
def get_position():
    with get_plc() as plc:
        x = plc.read_by_name(SYM_POS_X, pyads.PLCTYPE_LREAL)
        y = plc.read_by_name(SYM_POS_Y, pyads.PLCTYPE_LREAL)
        z = plc.read_by_name(SYM_POS_Z, pyads.PLCTYPE_LREAL)
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


@app.route('/write', methods=['POST'])
def write():
    """
    Generic momentary/hold write. Used for Start, Stop, and all Jog
    directions - anything that behaves like a press/release pushbutton.
    Params: key (one of WRITE_SYMBOLS), state ('0' or '1')
    """
    key = request.args.get('key')
    state = request.args.get('state')

    if key not in WRITE_SYMBOLS or state not in ('0', '1'):
        return 'Invalid parameters', 400

    with get_plc() as plc:
        plc.write_by_name(WRITE_SYMBOLS[key], state == '1', pyads.PLCTYPE_BOOL)
    return 'OK'


if __name__ == '__main__':
    # This container runs with network_mode: host (see docker-compose.yml),
    # so it shares the Pi's real network interface directly - required for
    # a stable ADS route to/from the PLC. It is reachable from the 'web'
    # container via host.docker.internal:5000 (see config.php).
    app.run(host='0.0.0.0', port=5000)

""" REST-ful API for the Siren system. """
from flask import current_app, Flask, jsonify

PORT = 12346
HOST = '0.0.0.0'

def run_rest(siren):
    app = Flask('siren')
    app.config.from_mapping(
        SIREN=siren
    )

    @app.route('/tone', methods=['GET'])
    def handle_tone():
        siren = current_app.config['SIREN']
        tone = {
            'tone': list(siren.generate_api_mappings()['tone'].keys()),
        }
        return jsonify(tone)

    @app.route('/tone/<tone>', methods=['GET'])
    def handle_activate_tone(tone):
        siren = current_app.config['SIREN']
        mappings = siren.generate_api_mappings()['tone']
        if tone not in mappings.keys():
            return jsonify({'error', f'Tone {tone} not valid'})
        mappings[tone]()
        return jsonify({})

    @app.route('/control', methods=['GET'])
    def handle_control():
        siren = current_app.config['SIREN']
        control = {
            'control': list(siren.generate_api_mappings()['control'].keys()),
        }
        return jsonify(control)

    @app.route('/control/<control>', methods=['GET'])
    def handle_activate_control(control):
        siren = current_app.config['SIREN']
        mappings = siren.generate_api_mappings()['control']
        if control not in mappings.keys():
            return jsonify({'error', f'Control {control} not valid'})
        mappings[control]()
        return jsonify({})

    @app.route('/debug', methods=['GET'])
    def handle_debug():
        siren = current_app.config['SIREN']
        debug = {
            'debug': list(siren.generate_api_mappings()['debug'].keys()),
        }
        return jsonify(debug)

    @app.route('/debug/<debug>', methods=['GET'])
    def handle_activate_debug(debug):
        siren = current_app.config['SIREN']
        mappings = siren.generate_api_mappings()['debug']
        if debug not in mappings.keys():
            return jsonify({'error', f'Debug {debug} not valid'})
        mappings[debug]()
        return jsonify({})

    @app.route('/on', methods=['GET'])
    def handle_on():
        siren = current_app.config['SIREN']
        mappings = siren.generate_api_mappings()
        if 'on' not in mappings.keys():
            return jsonify({'error', f'/on not supported'})
        mappings['on']()
        return jsonify({})

    @app.route('/off', methods=['GET'])
    def handle_off():
        siren = current_app.config['SIREN']
        mappings = siren.generate_api_mappings()
        if 'off' not in mappings.keys():
            return jsonify({'error', f'/off not supported'})
        mappings['off']()
        return jsonify({})

    app.run(host=HOST, port=PORT)

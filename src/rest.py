""" REST-ful API for the Siren system. """
from flask import current_app, Flask, jsonify

PORT = 12346
HOST = '0.0.0.0'

def run_rest(siren):
    app = Flask('siren')
    app.config.from_mapping(
        SIREN=siren
    )

    @app.route('/trigger', methods=['GET'])
    def handle_trigger():
        siren = current_app.config['SIREN']
        triggers = {
            'triggers': list(siren.generate_api_mappings().keys()),
        }
        print(triggers)
        return jsonify(triggers)

    @app.route('/trigger/<trigger>', methods=['GET'])
    def handle_activate_trigger(trigger):
        siren = current_app.config['SIREN']
        mappings = siren.generate_api_mappings()
        if trigger not in mappings.keys():
            return jsonify({'error', 'Trigger %s not a valid trigger' % trigger})
        mappings[trigger]()
        return jsonify({})

    app.run(host=HOST, port=PORT)

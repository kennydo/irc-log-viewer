import logging
import os
from flask import Flask, jsonify, session
from irclogviewer.auth import auth as auth_blueprint
from irclogviewer.logs import logs as logs_blueprint


logger = logging.getLogger(__name__)
app = Flask(__name__)
if 'FLASK_SETTINGS' in os.environ:
    app.config.from_envvar('FLASK_SETTINGS')
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(logs_blueprint, url_prefix='/logs')


@app.route('/')
def index():
    return jsonify(session)

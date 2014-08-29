import logging
from flask import Flask, jsonify, session
from irclogviewer.auth import auth as auth_blueprint


logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_envvar('FLASK_SETTINGS')
app.register_blueprint(auth_blueprint)


@app.route('/')
def index():
    return jsonify(session)

import datetime
import os
from flask import Flask, redirect, session, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from irclogviewer.auth import auth as auth_blueprint
from irclogviewer.logs import logs as logs_blueprint


app = Flask(__name__)
if 'FLASK_SETTINGS' in os.environ:
    app.config.from_envvar('FLASK_SETTINGS')
    db = SQLAlchemy(app)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(logs_blueprint, url_prefix='/logs')


@app.context_processor
def inject_session_user():
    return dict(session_user=session.get('user'))


@app.context_processor
def inject_today():
    return dict(today=datetime.date.today())


@app.route('/')
def index():
    return redirect(url_for('logs.index'))

import datetime
from flask import Flask, redirect, session, url_for
from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_envvar('FLASK_SETTINGS')
    db.init_app(app)

    from irclogviewer.auth import auth as auth_blueprint
    from irclogviewer.logs import logs as logs_blueprint
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
    return app
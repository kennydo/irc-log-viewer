import datetime
import http.client
from urllib.parse import quote
from flask import Flask, redirect, session, render_template, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from irclogviewer.dates import DateConverter


db = SQLAlchemy()


def render_http_status_code_template(template, status_code):
    """Shortcut to ``render_template`` that passes in ``status_code``
    and ``status_name`` to the template.

    :param str template: template location
    :param status_code: an HTTP status code from ``http.client``
    """
    status_name = http.client.responses[status_code]
    return render_template(template,
                           status_code=status_code,
                           status_name=status_name), status_code


def create_app():
    app = Flask(__name__)
    app.config.from_envvar('FLASK_SETTINGS')
    app.url_map.converters['date'] = DateConverter
    db.init_app(app)

    # noinspection PyUnusedLocal
    @app.context_processor
    def inject_session_user():
        return dict(session_user=session.get('user'))

    # noinspection PyUnusedLocal
    @app.context_processor
    def inject_today():
        return dict(today=datetime.date.today())

    # noinspection PyUnusedLocal
    @app.context_processor
    def get_encoded_path():
        """Get the URL-encoded path part of the input ``url``."""
        def inner(url):
            # '#' is an especially problematic character, since we want
            # the unquoted string to be '%23', not '#'
            path = url.split('/', 3)[-1].replace('#', '%23')
            return quote('/' + path)
        return dict(get_encoded_path=inner)

    # noinspection PyUnusedLocal
    @app.route('/')
    def index():
        return redirect(url_for('logs.index'))

    # noinspection PyUnusedLocal
    @app.errorhandler(http.client.FORBIDDEN)
    def http_forbidden(e):
        return render_http_status_code_template(
            'http_status_code.html',
            http.client.FORBIDDEN)

    # noinspection PyUnusedLocal
    @app.errorhandler(http.client.NOT_FOUND)
    def http_not_found(e):
        return render_http_status_code_template(
            'http_status_code.html',
            http.client.NOT_FOUND)

    from irclogviewer.auth import auth as auth_blueprint
    from irclogviewer.logs import logs as logs_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(logs_blueprint, url_prefix='/logs')

    return app

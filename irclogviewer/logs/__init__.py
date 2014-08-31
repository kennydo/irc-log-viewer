import calendar
import logging
from flask import abort, Blueprint, render_template, url_for, jsonify
from .dates import sorted_unique_log_dates, sorted_unique_year_months, parse_log_date
from .znc import ZncDirectory, ZncUser, ZncLog

logger = logging.getLogger(__name__)
logs = Blueprint('logs', __name__, template_folder='templates')
znc_directory = None


def inject_znc_users():
    users =[user for user in znc_directory.users.keys()]
    return dict(znc_users=users)


def get_znc_user_or_404(user):
    if user not in znc_directory.users:
        abort(404)
    return znc_directory.users[user]


@logs.record_once
def init_znc_directory(setup_state):
    global znc_directory
    app = setup_state.app

    znc_directory = ZncDirectory(app.config.get('ZNC_DIRECTORY'))
    app.context_processor(inject_znc_users)


@logs.route('/')
def list_users():
    return render_template('users.html')


def show_calendar_of_logs(logs, date_url_function, title):
    log_dates = sorted_unique_log_dates(logs)
    year_month_tuples = sorted_unique_year_months(log_dates)
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)

    return render_template(
        'calendar.html',
        title=title,
        calendar=cal,
        log_dates=log_dates,
        year_month_tuples=year_month_tuples,
        date_url_function=date_url_function,
    )


@logs.route('/users/<user>/dates')
def list_user_dates(user):
    znc_user = get_znc_user_or_404(user)

    def date_url_function(d):
        return url_for('.list_date_channels',
                       user=user,
                       date=d.strftime("%Y%m%d"))

    return show_calendar_of_logs(
        znc_user.logs.all(),
        date_url_function,
        "{0} Logs".format(user),
    )


@logs.route('/users/<user>/dates/<date>')
def list_date_channels(user, date):
    znc_user = get_znc_user_or_404(user)
    date = parse_log_date(date)

    channels = znc_user.logs.filter(date=date)


@logs.route('/users/<user>/channels')
def list_user_channels(user):
    znc_user = get_znc_user_or_404(user)
    channels = set(log.channel for log in znc_user.logs.all())

    return render_template(
        'channels.html',
        user=user,
        channels=channels,
    )


@logs.route('/users/<user>/channels/<channel>')
def list_channel_dates(user, channel):
    znc_user = get_znc_user_or_404(user)

    def date_url_function(d):
        return url_for('.get_log',
                       user=user,
                       channel=channel,
                       date=d.strftime("%Y%m%d"))

    return show_calendar_of_logs(
        znc_user.logs.filter(channel=channel),
        date_url_function,
        "{0} Logs".format(user),
    )


@logs.route('/users/<user>/channels/<channel>/<date>')
def get_log(user, channel, date):
    pass
import calendar
import logging
from flask import abort, Blueprint, render_template, Response, url_for
from .dates import sorted_unique_year_months, parse_log_date
from .irc_parser import parse_irc_line
from .znc import ZncDirectory, ZncUser, ZncLog

logger = logging.getLogger(__name__)
logs = Blueprint('logs', __name__, template_folder='templates')
znc_directory = None


def inject_znc_users():
    users =[user for user in znc_directory.users.keys()]
    return dict(znc_users=users)

def to_month_name(month_number):
    return calendar.month_name[month_number]


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
    app.jinja_env.filters['to_month_name'] = to_month_name


@logs.route('/')
def list_users():
    return render_template('users.html')


def show_calendar_of_logs(logs, date_url_function, title):
    log_dates = set(log.date for log in logs)
    year_month_tuples = sorted_unique_year_months(log_dates)
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)

    most_recent_log_date = None
    if log_dates:
        most_recent_log_date = sorted(log_dates)[-1]

    return render_template(
        'calendar.html',
        title=title,
        calendar=cal,
        log_dates=log_dates,
        most_recent_log_date = most_recent_log_date,
        year_month_tuples=year_month_tuples,
        date_url_function=date_url_function,
    )


@logs.route('/users/<user>/dates')
def list_user_dates(user):
    znc_user = get_znc_user_or_404(user)

    def date_url_function(d):
        return url_for(
            '.list_date_channels',
            user=user,
            date=d.strftime("%Y%m%d")
        )

    return show_calendar_of_logs(
        znc_user.logs.all(),
        date_url_function,
        "{0} Logs".format(user),
    )


@logs.route('/users/<user>/dates/<date>')
def list_date_channels(user, date):
    znc_user = get_znc_user_or_404(user)
    date = parse_log_date(date)
    channels = set(log.channel for log in znc_user.logs.filter(date=date))

    def channel_url_function(channel):
        return url_for(
            '.get_log',
            user=user,
            date=date.strftime("%Y%m%d"),
            channel=channel
        )

    return render_template(
        'channels.html',
        title='Channels for {0} on {1}'.format(user, date),
        user=user,
        date=date,
        channels=channels,
        channel_url_function=channel_url_function,
    )


@logs.route('/users/<user>/channels')
def list_user_channels(user):
    znc_user = get_znc_user_or_404(user)
    channels = set(log.channel for log in znc_user.logs.all())

    def channel_url_function(channel):
        return url_for('.list_channel_dates', user=user, channel=channel)

    return render_template(
        'channels.html',
        title='Channels for {0}'.format(user),
        user=user,
        channels=channels,
        channel_url_function=channel_url_function,
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
    znc_user = get_znc_user_or_404(user)
    log = znc_user.logs.get(date=parse_log_date(date), channel=channel)
    if not log:
        abort(404)

    def generate_lines():
        with open(log.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                yield repr(parse_irc_line(line))
    return Response(generate_lines(), mimetype='text/html')
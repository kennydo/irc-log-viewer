import calendar
import datetime
from flask import abort, Blueprint, render_template, request, session
from .authorization import email_can_read_channel_logs
from .dates import sorted_unique_year_months, parse_log_date
from .filters import filters_mapping
from .irc_parser import parse_irc_line
from .znc import ZncDirectory


logs = Blueprint('logs', __name__, template_folder='templates')
znc_directory = None


def inject_znc_users():
    users = [user for user in znc_directory.users.keys()]
    return dict(znc_users=users)


def get_znc_user_or_404(user):
    if user not in znc_directory.users:
        abort(404)
    return znc_directory.users[user]


def get_session_user_email():
    return session.get('user', {}).get('email', None)


@logs.record_once
def init_znc_directory(setup_state):
    global znc_directory
    app = setup_state.app

    if 'ZNC_DIRECTORY' in app.config:
        znc_directory = ZncDirectory(app.config.get('ZNC_DIRECTORY'))
    else:
        raise ValueError("ZNC_DIRECTORY was not set in flask config")
    app.context_processor(inject_znc_users)
    app.jinja_env.filters.update(**filters_mapping)


@logs.route('/')
def index():
    return render_template('index.html')


@logs.route('/calendar')
def show_calendar():
    """Shows the month calendars for each viewable log
    """
    log_dates = set()
    for znc_user in znc_directory.users.values():
        log_dates.update(
            log.date for log in znc_user.logs.all()
            if email_can_read_channel_logs(
                get_session_user_email(),
                znc_user.name,
                log.channel,
            )
        )
    year_month_tuples = sorted_unique_year_months(log_dates)
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)

    most_recent_log_date = None
    if log_dates:
        most_recent_log_date = sorted(log_dates)[-1]

    return render_template(
        'calendar.html',
        calendar=cal,
        log_dates=log_dates,
        most_recent_log_date=most_recent_log_date,
        year_month_tuples=year_month_tuples,
    )


@logs.route('/channels')
def list_channels():
    """List all of the channels that each :class:`irclogviewer.logs.znc.ZncUser`
    has logs for.
    """
    # latest_logs maps from ZncUser -> str channel name -> latest ZncLog
    latest_logs = {}

    session_user_email = get_session_user_email()

    specific_date = request.args.get('date', None)
    if 'date' in request.args:
        if request.args['date'].lower() == "today":
            specific_date = datetime.date.today()
        else:
            specific_date = datetime.datetime.strptime(
                request.args['date'],
                "%Y-%m-%d",
            ).date()
        log_generator = lambda zuser: zuser.logs.filter(date=specific_date)
    else:
        log_generator = lambda zuser: zuser.logs.all()

    for znc_user in znc_directory.users.values():
        latest_logs[znc_user] = {}
        filtered_logs = [
            log for log in log_generator(znc_user)
            if email_can_read_channel_logs(session_user_email,
                                           znc_user.name,
                                           log.channel)
        ]

        for log in filtered_logs:
            if log.channel in latest_logs[znc_user]:
                current_latest_log = latest_logs[znc_user][log.channel]
                if log.modified_time > current_latest_log.modified_time:
                    latest_logs[znc_user][log.channel] = log
            else:
                latest_logs[znc_user][log.channel] = log

    # maps from ZncUser -> list of ZncLog, ordered by modified_time (desc)
    sorted_latest_logs = {}
    for znc_user, latest_log_by_channel in latest_logs.items():
        sorted_latest_logs[znc_user] = [
            znc_log
            for channel_name, znc_log
            in sorted(latest_log_by_channel.items(),
                      key=lambda item: item[1],
                      reverse=True)
        ]

    return render_template(
        'channels.html',
        latest_logs=sorted_latest_logs,
        specific_date=specific_date,
    )


@logs.route('/users/<user>/channels/<channel>/<date>')
def get_log(user, channel, date):
    """Get a specific log."""
    znc_user = get_znc_user_or_404(user)
    date = datetime.datetime.strptime(
        date,
        "%Y-%m-%d",
    ).date()

    email = get_session_user_email()
    if not email_can_read_channel_logs(email, znc_user.name, channel):
        abort(403)

    logs = znc_user.logs.filter(channel=channel)

    for i_index, i_log in enumerate(logs):
        if i_log.date == date:
            log = i_log
            break
    else:
        log = None

    if not log:
        abort(404)

    if i_index > 0:
        earlier_log = logs[i_index - 1]
    else:
        earlier_log = None

    if (i_index + 1) < len(logs):
        later_log = logs[i_index + 1]
    else:
        later_log = None

    with open(log.log_path, 'r', encoding='utf-8', errors='ignore') as f:
        irc_lines = [parse_irc_line(line) for line in f]
    return render_template(
        'log.html',
        znc_user=znc_user,
        earlier_log=earlier_log,
        later_log=later_log,
        log=log,
        irc_lines=irc_lines,
    )

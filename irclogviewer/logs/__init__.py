import calendar
import datetime

from flask import abort, Blueprint, render_template, request, session

from irclogviewer.models import db, IrcUserChannel, IrcLog
from irclogviewer.logs.authorization import email_can_read_channel_logs
from irclogviewer.logs.dates import parse_log_date, sorted_unique_year_months
from irclogviewer.logs.filters import filters_mapping
from irclogviewer.logs.irc_parser import parse_irc_line


logs = Blueprint('logs', __name__, template_folder='templates')


def get_session_user_email():
    return session.get('user', {}).get('email', None)


@logs.record_once
def init_znc_directory(setup_state):
    app = setup_state.app
    app.jinja_env.filters.update(**filters_mapping)


@logs.route('/')
def index():
    return render_template('index.html')


@logs.route('/calendar')
def show_calendar():
    """Shows the month calendars for each viewable log
    """
    query = db.session.query(IrcLog.date.distinct())\
                      .order_by(IrcLog.date)\
                      .all()
    log_dates = [row[0] for row in query]

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

    query = db.session.query(IrcLog)
    if specific_date:
        query = query.filter(IrcLog.date==specific_date)
    query = query.group_by(IrcLog.user_channel)\
                 .order_by(IrcLog.user.asc(),
                           IrcLog.date.desc(),
                           IrcLog.last_modified.desc(),
                           IrcLog.channel.asc())

    for log in query.all():
        if not email_can_read_channel_logs(session_user_email,
                                           log.user,
                                           log.channel):
            continue
        if log.user not in latest_logs:
            latest_logs[log.user] = []

        latest_logs[log.user].append(log)

    return render_template(
        'channels.html',
        latest_logs=latest_logs,
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

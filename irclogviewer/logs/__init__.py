import calendar
from flask import abort, Blueprint, render_template, session, url_for
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
    app.context_processor(inject_znc_users)
    app.jinja_env.filters.update(**filters_mapping)


@logs.route('/')
def list_users():
    return render_template('users.html')


def show_calendar_of_logs(logs, date_url_function, title):
    """

    :param logs: IRC logs
    :type logs: list of :class:`~irclogviewer.logs.znc.ZncLog`
    :param date_url_function: 1 arity function called on each
        :class:`~datetime.date` in the calendar
    :param str title: desired page title
    """
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
        most_recent_log_date=most_recent_log_date,
        year_month_tuples=year_month_tuples,
        date_url_function=date_url_function,
    )


@logs.route('/users/<user>/dates')
def list_user_dates(user):
    """List all of the dates that contain logs for this ``user``"""
    znc_user = get_znc_user_or_404(user)
    logs = [
        log for log in znc_user.logs.all()
        if email_can_read_channel_logs(
            get_session_user_email(),
            znc_user.name,
            log.channel,
        )
    ]

    def date_url_function(d):
        """Link to the channels that have logs for the given
        :class:`~datetime.date` ``d``.
        """
        return url_for(
            '.list_date_channels',
            user=user,
            date=d.strftime("%Y%m%d")
        )

    return show_calendar_of_logs(
        logs,
        date_url_function,
        "{0} Logs".format(user),
    )


@logs.route('/users/<user>/dates/<date>')
def list_date_channels(user, date):
    """List all of the channels that have logs on this ``date``."""
    znc_user = get_znc_user_or_404(user)
    date = parse_log_date(date)
    channels = set(
        log.channel for log in znc_user.logs.filter(date=date)
        if email_can_read_channel_logs(
            get_session_user_email(),
            znc_user.name,
            log.channel,
        )
    )

    def channel_url_function(channel):
        """Now that we know the date and channel, go right to the log."""
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
    """List all of the channels that this ``user`` has logs for."""
    znc_user = get_znc_user_or_404(user)
    channels = set(
        log.channel for log in znc_user.logs.all()
        if email_can_read_channel_logs(
            get_session_user_email(),
            znc_user.name,
            log.channel,
        )
    )

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
    """List all of the dates that this user was logging ``channel``."""
    znc_user = get_znc_user_or_404(user)
    logs = [
        log for log in znc_user.logs.filter(channel=channel)
        if email_can_read_channel_logs(
            get_session_user_email(),
            znc_user.name,
            log.channel,
        )
    ]

    def date_url_function(d):
        return url_for('.get_log',
                       user=user,
                       channel=channel,
                       date=d.strftime("%Y%m%d"))

    return show_calendar_of_logs(
        logs,
        date_url_function,
        "{0} Logs".format(user),
    )


@logs.route('/users/<user>/channels/<channel>/<date>')
def get_log(user, channel, date):
    """Get a specific log."""
    znc_user = get_znc_user_or_404(user)
    date = parse_log_date(date)

    email = get_session_user_email()
    if not email_can_read_channel_logs(email, znc_user.name, channel):
        abort(403)

    log = znc_user.logs.get(date=date, channel=channel)
    if not log:
        abort(404)

    with open(log.log_path, 'r', encoding='utf-8') as f:
        irc_lines = [parse_irc_line(line) for line in f]
    return render_template(
        'log.html',
        user=user,
        channel=channel,
        date=date,
        irc_lines=irc_lines,
    )

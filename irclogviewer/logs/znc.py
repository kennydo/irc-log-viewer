from collections import Mapping
from functools import total_ordering
import logging
import re
import os
from .dates import parse_log_date

LOG_FILENAME_PATTERN = re.compile(
    '(?P<channel>.+)_(?P<date>\d{4}\d{2}\d{2}).log'
)
log = logging.getLogger(__name__)


class ZncDirectory(object):
    """Representation of a ``.znc`` directory that contains a ``users``
    directory.
    """
    def __init__(self, znc_path):
        """
        :param str znc_path: path to (typically) a ``.znc`` directory
        :raises ValueError: if ``znc_path`` doesn't exist or if it doesn't have
            a ``users`` directory
        """
        self.znc_path = os.path.abspath(znc_path)

        if not os.path.isdir(self.znc_path):
            raise ValueError('No ZNC directory found at path {0}'.format(
                self.znc_path)
            )

        self.users = ZncUserMapping(self.znc_path)

    def __repr__(self):
        return '<ZncDirectory znc_path={znc_path}>'.format(**self.__dict__)


class ZncUser(object):
    """Representation of a single ZNC user."""

    def __init__(self, user_path):
        """
        :param str user_path: path to a user under the ``users`` directory
        :raises ValueError: if the ``user_path`` isn't a valid directory
        """
        self.user_path = user_path
        self.name = os.path.basename(self.user_path)
        self.logs = ZncLogManager(user_path)

    def __repr__(self):
        return '<ZncUser user_path={user_path}>'.format(**self.__dict__)


class ZncUserMapping(Mapping):
    """Provide a dictionary-like way to access ZNC users."""

    def __init__(self, znc_path):
        """
        :param str znc_path: typically a path to a ``.znc`` directory
        :raises ValueError: if the given ``znc_path`` doesn't have a ``users``
            directory
        """
        self.users_path = os.path.join(znc_path, 'users')
        if not os.path.isdir(self.users_path):
            raise ValueError('No user directory found in path {0}'.format(
                self.users_path)
            )

    def __len__(self):
        return len(os.listdir(self.users_path))

    def __getitem__(self, user):
        user_directory = os.path.join(self.users_path, user)
        if not os.path.isdir(user_directory):
            raise KeyError(
                'No user directory found for user "{0}" in path {1}'.format(
                    user, self.users_path)
            )
        return ZncUser(user_directory)

    def __iter__(self):
        for user in os.listdir(self.users_path):
            yield user

    def __repr__(self):
        return '<ZncUserMapping users_path={users_path}>'.format(
            **self.__dict__)


@total_ordering
class ZncLog(object):
    """Representation of a single ZNC log file."""

    @classmethod
    def from_path(cls, log_path):
        """Construct a new :class:`ZncLog` based on the given ``log_path``.

        :param str log_path: path to a possible log file
        :raises ValueError: if the filename in ``log_path`` is not recognized
        :rtype: ZncLog
        """
        filename = os.path.basename(log_path)
        match = LOG_FILENAME_PATTERN.match(filename)
        if not match:
            raise ValueError(
                'Log filename "{0}" has an unsupported format'.format(filename)
            )
        groups = match.groupdict()

        channel = groups['channel']
        date = parse_log_date(groups['date'])

        return cls(log_path, channel, date)

    def __init__(self, log_path, channel, date):
        self.log_path = log_path
        self.date = date
        self.channel = channel

    def __repr__(self):
        return '<ZncLog date={date} channel={channel} log_path={log_path}>'.\
            format(**self.__dict__)

    # We sort ZncLog objects first by date, then by channel
    def __lt__(self, other):
        if self.date < other.date:
            return True
        elif self.date == other.date:
            return self.channel < other.channel
        return False

    def __le__(self, other):
        if self.date < other.date:
            return True
        elif self.date == other.date:
            return self.channel <= other.channel
        return False

    def __eq__(self, other):
        return self.date == other.date and self.channel == other.channel

    def __ne__(self, other):
        return self.date != other.date or self.channel != other.channel

    def __gt__(self, other):
        if self.date > other.date:
            return True
        elif self.date == other.date:
            return self.channel > other.channel
        return False

    def __ge__(self, other):
        if self.date > other.date:
            return True
        elif self.date == other.date:
            return self.channel >= other.channel
        return False


class ZncLogManager(object):
    """Provide a nice interface to a ZNC user's logs."""

    def __init__(self, user_path):
        """
        :param str user_path: path to where a user's ``log`` directory would
            be if the ``log`` directory existed
        """
        self.logs_path = os.path.join(user_path, 'moddata', 'log')

    def all(self):
        """Generator that yields all the valid :class:`ZncLog` objects it can
        successfully parse and create.
        """
        if not os.path.isdir(self.logs_path):
            raise StopIteration()

        for filename in os.listdir(self.logs_path):
            try:
                znc_log = ZncLog.from_path(
                    os.path.join(self.logs_path, filename))
            except ValueError as e:
                log.exception("Invalid filename in log directory: " + str(e))
            else:
                yield znc_log

    def filter(self, date=None, channel=None):
        """Return only the :class:`ZncLog` objects that match the date filter,
        channel filter, or combined date and channel filter.

        At least one of ``date`` or ``channel`` must be given as an argument.

        :param datetime.date date: (optional) date you are interested in
        :param str channel: (optional) channel you are interested in
        :raises ValueError: if neither ``date`` nor ``channel`` arguments were
            defined
        :rtype: list of :class:`ZncLog`
        :returns: a sorted list of :class:`ZncLog` objects meeting the criteria
        """
        if date and channel:
            predicate = lambda l: l.date == date and l.channel == channel
        elif date:
            predicate = lambda l: l.date == date
        elif channel:
            predicate = lambda l: l.channel == channel
        else:
            raise ValueError("Neither date nor channel were specified")

        return sorted(znc_log for znc_log in self.all() if predicate(znc_log))

    def get(self, date=None, channel=None):
        """Get only the :class:`ZncLog` object that was from the given ``date``
        for the given ``channel``.

        :param datetime.date date: date you are interested in
        :param str channel: channel you are interested in
        :return: the desired log object, if it exists, or None
        :rtype: :class:`ZncLog` or None
        """
        if not date or not channel:
            raise ValueError("Neither date nor channel were specified")

        znc_logs = self.filter(date=date, channel=channel)
        if znc_logs:
            return znc_logs[0]
        return None

    def __repr__(self):
        return '<ZncLogManager logs_path={logs_path}>'.format(**self.__dict__)

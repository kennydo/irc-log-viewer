from collections import namedtuple
import datetime
from werkzeug.routing import BaseConverter, ValidationError

YearMonth = namedtuple('YearMonth', ['year', 'month'])


class DateConverter(BaseConverter):
    def to_python(self, value):
        """Convert a date-ish :class:`str` to a :class:`~datetime.date` object.

        :param str value: a date-like string
        :return: a :class:`datetime.date` object
        """
        if value == 'today':
            return datetime.date.today()

        try:
            date = parse_dashed_date(value)
        except ValueError as e:
            raise ValidationError(str(e))
        return date

    def to_url(self, value):
        """Make a dashed date string.

        :param value: a date
        :type value: :class:`datetime.date`
        :return: a dashed string in the YYYY-MM-DD format
        """
        return value.strftime("%Y-%m-%d")


def sorted_unique_year_months(dates):
    """Get a sorted list (ascending) of the unique (year, month) tuples that
    appear in ``date_set``.
    :type dates: iterable of :class:`datetime.date`
    :rtype: list of :class:`YearMonth`
    """
    year_months = set()
    for d in dates:
        year_months.add(YearMonth(d.year, d.month))

    return sorted(year_months)


def parse_date(raw_date):
    """General-purpose date parser. Can handle YYYY-MM-DD, YYYYMMDD, or
    the string "today".

    :param str raw_date: a date
    :return: a :class:`datetime.date` object
    """
    if '-' in raw_date:
        return parse_dashed_date(raw_date)
    elif raw_date == 'today':
        return datetime.date.today()
    else:
        return parse_undashed_date(raw_date)


def parse_undashed_date(raw_date):
    """Parse the YYYYMMDD date format that ZNC uses.

    :param str raw_date: a string of the form YYYYMMDD
    :returns: a :class:`~datetime.date` object
    """
    return datetime.datetime.strptime(raw_date, "%Y%m%d").date()


def parse_dashed_date(raw_date):
    """Parse the YYYY-MM-DD date format that :class:`datetime.date` objects
    default to.

    :param str raw_date: a string of the form YYYY-MM-DD
    :returnss: a :class:`datetime.date` object
    """
    return datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()

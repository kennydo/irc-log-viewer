from collections import namedtuple
import datetime


YearMonth = namedtuple('YearMonth', ['year', 'month'])


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


def parse_log_date(raw_date):
    """Parse the YYYYMMDD date format that ZNC uses.

    :param str raw_date: a string of the form YYYYMMDD
    :returns: a :class:`~datetime.date` object
    """
    return datetime.datetime.strptime(raw_date, "%Y%m%d").date()

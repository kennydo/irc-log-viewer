from collections import namedtuple
import datetime


YearMonth = namedtuple('YearMonth', ['year', 'month'])


def sorted_unique_year_months(date_set):
    """Get a sorted list (ascending) of the unique (year, month) tuples that
    appear in ``date_set``.
    :type date_set: set of :class:`datetime.date`
    :rtype: list of :class:`YearMonth`
    """
    year_months = set()
    for d in date_set:
        year_months.add(YearMonth(d.year, d.month))

    return sorted(year_months)


def parse_log_date(raw_date):
    return datetime.datetime.strptime(raw_date, "%Y%m%d").date()

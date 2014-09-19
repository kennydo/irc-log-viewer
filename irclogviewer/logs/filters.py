import calendar
import datetime
from functools import lru_cache, wraps
import re

from flask import Markup


# based on https://gist.github.com/gruber/249502
# from http://daringfireball.net/2010/07/improved_regex_for_matching_urls
URL_REGEX = re.compile(
    r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.]'
    r'[a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\('
    r'([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))'
)


filters_mapping = {}


def register_jinja_filter(func):
    @wraps(func)
    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    filters_mapping[func.__name__] = inner
    return inner


@register_jinja_filter
def to_month_name(month_number):
    return calendar.month_name[month_number]


@register_jinja_filter
def irc_line_state_to_css_classes(irc_line_state):
    classes = []
    if irc_line_state.is_bold:
        classes.append("irc-bold")
    if irc_line_state.has_underline:
        classes.append("irc-underline")
    if irc_line_state.fg_color:
        classes.append("irc-fg-" + str(irc_line_state.fg_color))
    if irc_line_state.bg_color:
        classes.append("irc-bg-" + str(irc_line_state.bg_color))
    return classes


@register_jinja_filter
def plain_urls_to_links(irc_text):
    return Markup(
        URL_REGEX.sub(r'<a href="\g<1>" target="_blank">\g<1></a>', irc_text)
    )


@register_jinja_filter
@lru_cache(maxsize=128)
def irc_nick_to_color_id(nick):
    # Not all colors are suitable for colorizing a nick
    colors = [2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13]
    ascii_sum = sum(ord(char) for char in nick)
    return colors[ascii_sum % len(colors)]


@register_jinja_filter
def date_before(date):
    return date - datetime.timedelta(days=1)


@register_jinja_filter
def date_after(date):
    return date + datetime.timedelta(days=1)

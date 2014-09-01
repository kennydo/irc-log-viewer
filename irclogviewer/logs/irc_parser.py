from collections import namedtuple
from enum import Enum
import re


class IrcControlCode(Enum):
    color = '\x03'      # ^C = color
    reset = '\x0F'      # ^O = reset
    underline = '\x1F'  # ^_ = underline
    bold = '\x02'       # ^B = bold


CTRL_REGEX = re.compile(r'(?:[%s%s%s])|(%s(?:\d{1,2}),?(?:\d{1,2})?)' % (
    IrcControlCode.reset.value,
    IrcControlCode.underline.value,
    IrcControlCode.bold.value,
    IrcControlCode.color.value))


class IrcLineType(Enum):
    message = re.compile(r'^<(?P<nick>\S+)> (?P<message>.*)$')
    join = re.compile(r'^\*\*\* Joins: .*$')
    part = re.compile(r'^\*\*\* Parts: .*$')
    quit = re.compile(r'^\*\*\* Quits: .*$')
    action = re.compile(r'^\* \S+ .*$')


class IrcLineState(
    namedtuple(
        'IrcLineState',
        ['fg_color', 'bg_color', 'is_bold', 'has_underline'])):

    @classmethod
    def default_state(cls):
        return cls(None, None, False, False)

    def reset(self):
        return self._replace(
            fg_color=None,
            bg_color=None,
            is_bold=False,
            has_underline=False,
        )

    def toggle_bold(self):
        return self._replace(is_bold=not self.is_bold)

    def toggle_underline(self):
        return self._replace(has_underline=not self.has_underline)

    def set_color(self, fg_color_id, bg_color_id=None):
        return self._replace(
            fg_color=fg_color_id,
            bg_color=bg_color_id,
        )


IrcLine = namedtuple('IrcLine',
                     ['timestamp', 'nick', 'type', 'message_fragments'])
IrcLineFragment = namedtuple('IrcLineFragment', ['state', 'text'])

def ctrl_to_color_ids(fragment_text):
    # the first character is CTRL_COLOR
    colors = fragment_text[1:].split(',')
    if colors[0].isdigit():
        fg_color_id = int(colors[0])
    else:
        fg_color_id = None
    if len(colors) == 1:
        bg_color_id = None
    else:
        bg_color_id = int(colors[1])
    return (fg_color_id, bg_color_id)


def tokenize_line(line):
    """
    Split text into fragments that are either plain text
    or a control code sequence.
    """
    line = CTRL_REGEX.sub("\n\g<0>\n", line)
    fragments = line.split("\n")
    return fragments


def split_on_timestamp(raw_line):
    """
    Splits a raw irc log line into 2 components: timestamp, and everything else
    """
    timestamp, line = raw_line.split(" ", 1)

    # remove the brackets [] around the timestamp
    timestamp = timestamp[1:-1]
    return timestamp, line


def split_on_nick(line):
    """
    If the input line has a "<nick>" element at the start, it returns
    (nick, rest of line), else it returns (None, original input line).

    The input to this should be the component of the line after the timestamp
    has already been removed.
    """
    match = IrcLineType.message.value.match(line)
    if match:
        nick, message = match.groups()
    else:
        nick, message = None, line
    return nick, message


def parse_irc_line(raw_line):
    raw_line = raw_line.strip()
    timestamp, line = split_on_timestamp(raw_line)
    nick = None
    message_fragments = list()

    if IrcLineType.join.value.match(line):
        line_type = "join"
    elif IrcLineType.part.value.match(line):
        line_type = "part"
    elif IrcLineType.quit.value.match(line):
        line_type = "quit"
    elif IrcLineType.action.value.match(line):
        line_type = "action"
    else:
        line_type = "message"

    line_state = IrcLineState.default_state()

    if line_type is not "message":
        fragment = IrcLineFragment(state=line_state,
                                   text=line)
        message_fragments.append(fragment)
    else:
        nick, line = split_on_nick(line)

        # the CTRL_RESET char at the end makes processing the last fragment
        # doable in the body of the 'for' loop
        raw_fragments = tokenize_line(line) + [IrcControlCode.reset.value]

        previous_state = line_state
        previous_text = None
        for raw_fragment in raw_fragments:
            if not raw_fragment:
                # blank fragments
                continue
            first_char = raw_fragment[0]

            was_control_code = True
            if first_char == IrcControlCode.color.value:
                (fg_color_id, bg_color_id) = ctrl_to_color_ids(raw_fragment)
                line_state = line_state.set_color(fg_color_id, bg_color_id)
            elif first_char == IrcControlCode.reset.value:
                line_state = line_state.reset()
            elif first_char == IrcControlCode.underline.value:
                line_state = line_state.toggle_underline()
            elif first_char == IrcControlCode.bold.value:
                line_state = line_state.toggle_bold()
            else:
                was_control_code = False

            if was_control_code:
                if previous_text:
                    fragment = IrcLineFragment(state=previous_state,
                                               text=previous_text)
                    message_fragments.append(fragment)
                previous_state = line_state
                previous_text = None
            else:
                previous_text = raw_fragment

    return IrcLine(timestamp=timestamp,
                   nick=nick,
                   type=line_type,
                   message_fragments=message_fragments)
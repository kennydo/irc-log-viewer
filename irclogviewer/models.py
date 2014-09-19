from sqlalchemy.orm import composite

from irclogviewer import db


class IrcUserChannel(object):
    def __init__(self, user, channel):
        self.user = user
        self.channel = channel

    def __composite_values__(self):
        return self.user, self.channel

    def __eq__(self, other):
        return self.user == other.user and self.channel == other.channel

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<IrcUserChannel user="{user}" channel="{channel}">'.format(
            user=self.user,
            channel=self.channel,
        )


class IrcLog(db.Model):
    __tablename__ = 'irclogs'

    user = db.Column(db.String(128), primary_key=True, nullable=False)
    channel = db.Column(db.String(128), primary_key=True, nullable=False)
    date = db.Column(db.Date(), primary_key=True, nullable=False)

    path = db.Column(db.String(256), nullable=False)
    last_modified = db.Column(db.DateTime(), nullable=False)

    user_channel = composite(IrcUserChannel, user, channel)

    def __repr__(self):
        return (
            '<IrcLog user="{user}" channel="{channel}" date={date} '
            'last_modified={last_modified}>'
        ).format(
            user=self.user,
            channel=self.channel,
            date=self.date,
            last_modified=self.last_modified,
        )

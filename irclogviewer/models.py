from irclogviewer import db


class IrcLog(db.Model):
    __tablename__ = 'irclogs'

    user = db.Column(db.String(128), primary_key=True, nullable=False)
    channel = db.Column(db.String(128), primary_key=True, nullable=False)
    date = db.Column(db.Date(), primary_key=True, nullable=False)
    last_modified = db.Column(db.DateTime(), nullable=False)
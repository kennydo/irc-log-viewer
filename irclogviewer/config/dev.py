"""
This single file contains the configuration for both gunicorn and flask.

Flask's config only uses the uppercase variables, and gunicorn has a
limited set of (lowercase) variables to configure, so there will never
be a name conflict.
"""
import sys
import os
# gunicorn config
bind = "127.0.0.1:25252"
workers = 4

# flask config
GOOGLE_CONSUMER_KEY = "REPLACE ME"
GOOGLE_CONSUMER_SECRET = "REPLACE ME"
SECRET_KEY = "Change this to an actually secret value"

CRAWLER_PID_FILE = os.path.join(sys.prefix, "crawler.pid")
SQLALCHEMY_DATABASE_URI = "sqlite:///{0}".format(os.path.join(sys.prefix,
                                                              "irc_logs.db"))

DEBUG = True
ZNC_DIRECTORY = '/replace/me/here/.znc'

OWNER_EMAIL = 'test@example.com'

# ACL rules are defined as tuples of (action, email_address, znc_user, channel)
# Use '*' when you want wildcards for email_address, znc_user, or channel.
# This app uses the action of the first rule that matches.
# This app requires that you must set at least 1 rule in ZNC_ACL.
# To allow everything for everyone, have this rule:
# ('allow', '*', '*', '*')
ZNC_ACL = [
    ('allow', OWNER_EMAIL, '*', '*'),
    ('deny', '*', '*', '*'),
]


# The number of channels per user you want to list by default.
NUM_TOP_CHANNELS_PER_USER = 6

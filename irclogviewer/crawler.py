import atexit
import logging
import sys
import os

import psutil

from irclogviewer import create_app, db
from irclogviewer.models import IrcLog
from irclogviewer.znc import ZncDirectory


logger = logging.getLogger(__name__)


def atexit_remove_pid_file(pid_file):
    def handler():
        if os.path.isfile(pid_file):
            logger.error(
                "Exit handler had to remove PID file {0}".format(pid_file)
            )
            os.remove(pid_file)
    return handler


def main():
    app = create_app()
    ctx = app.test_request_context()
    ctx.push()
    pid_file = app.config['CRAWLER_PID_FILE']

    if os.path.isfile(pid_file):
        with open(pid_file, 'r') as f:
            old_pid = int(f.read())
        if psutil.pid_exists(old_pid):
            logger.error(
                "PID {pid} written in PID file {pid_file} is still "
                "running. Crawl aborted.".format(pid=old_pid,
                                                 pid_file=pid_file)
            )
            sys.exit(1)
        else:
            os.remove(pid_file)
    else:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    atexit.register(atexit_remove_pid_file(pid_file))

    db.create_all()
    znc_directory = ZncDirectory(app.config['ZNC_DIRECTORY'])

    for user_directory in znc_directory.users.values():
        # Delete all the existing logs (because adding new IrcLog rows is
        # faster than merging existing entries).
        db.session.query(IrcLog)\
                  .filter(IrcLog.user == user_directory.name)\
                  .delete()

        db.session.commit()
        for log_file in user_directory.logs.all():
            irc_log = IrcLog(user=user_directory.name,
                             channel=log_file.channel,
                             date=log_file.date,
                             path=log_file.log_path,
                             last_modified=log_file.modified_time)
            print(irc_log)
            db.session.add(irc_log)
        db.session.commit()

    os.remove(pid_file)
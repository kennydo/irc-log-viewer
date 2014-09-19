#!/usr/bin/env python
"""
Starts and stops gunicorn with a given config file.

For this project, a config file is just a ``.py`` file that contains the
gunicorn and flask settings you want. We can safely mix the two configs into
a single file because gunicorn only has lowercase configuration variables and
flask only has uppercase configuration variables.
"""
import argparse
import os
import pipes
import psutil
import signal
import subprocess
import sys


APP_NAME = "irclogviewer"
BIN_DIR = os.path.abspath(os.path.join(sys.prefix, "bin"))
LOGS_DIR = os.path.abspath(os.path.join(sys.prefix, "logs"))


def load_python_config(filename):
    """Exec a given filename and return the locals defined within that file."""
    globals_dict = dict()
    locals_dict = dict()
    with open(filename) as config_file:
        exec(compile(config_file.read(), filename, 'exec'),
             globals_dict,
             locals_dict)
    return locals_dict


def gunicorn_config(filename=None):
    """Get the default gunicorn config, and then (optionally) update it with
    values from a given filename.
    """
    config = default_gunicorn_config()
    if filename:
        config.update(load_python_config(filename))
    return config


def default_gunicorn_config():
    """Return a default, typical gunicorn config with the basic variables
    defined.
    """
    config = {
        "bind": "0.0.0.0:8080",
        "pidfile": path_to_log("{0}.pid".format(APP_NAME)),
        "access_log": path_to_log("{0}_access.log".format(APP_NAME)),
        "error_log": path_to_log("{0}_error.log".format(APP_NAME)),
    }
    return config


def file_path_arg_type(relative_path):
    """Helper function for argparse arguments that require the absolute path to
    a file that exists.

    :param str relative_path: a path to a file
    :throw argparse.ArgumentTypeError: if the ``relative_path`` isn't a file or
                                       doesn't exist
    :returns: absolute path of ``relative_path``
    :rtype: str
    """
    absolute_path = os.path.abspath(relative_path)
    if not os.path.isfile(absolute_path):
        raise argparse.ArgumentTypeError(
            "{0} is not a valid file".format(relative_path))
    return absolute_path


def path_to_bin(filename):
    """Get the path to an executable filename within the bin directory."""
    return os.path.join(BIN_DIR, filename)


def path_to_log(filename):
    """Get the path to a file within the logs directory."""
    return os.path.join(LOGS_DIR, filename)


def command_start(args):
    """Run gunicorn and flask with the desired config file."""
    if not os.path.isdir(LOGS_DIR):
        os.mkdir(LOGS_DIR)

    config = gunicorn_config(args.config)

    # Consult http://docs.gunicorn.org/en/develop/configure.html for
    # gunicorn's CLI arguments and how they differ from the config
    # file variable names.
    cmd = [
        path_to_bin("gunicorn"),
        "{0}:create_app()".format(APP_NAME),
        "--bind", config["bind"],
        "--config", args.config,
        "--pid", config["pidfile"],
        "--access-logfile", config["access_log"],
        "--error-logfile", config["error_log"],
    ]

    print("Running the following command")
    print(" ".join(pipes.quote(c) for c in cmd))
    subprocess.Popen(cmd, env={
        "FLASK_SETTINGS": args.config,
    })


def command_stop(args):
    """Attempt to stop the gunicorn process."""
    config = gunicorn_config(args.config)
    pid_file = config["pidfile"]

    if os.path.isfile(pid_file):
        with open(pid_file, "r") as f:
            pid = int(f.read())
    else:
        pid = None

    if not pid:
        print("No PID file found")
        return

    if not psutil.pid_exists(pid):
        print("PID file says {0}, but it is not running".format(pid))
        os.unlink(pid_file)
        return

    process = psutil.Process(pid=pid)
    process.send_signal(signal.SIGTERM)
    print("Sent SIGTERM to PID {0}".format(pid))

    terminate_timeout = 10
    try:
        process.wait(timeout=terminate_timeout)
        print("PID {0} terminated".format(pid))
    except psutil.TimeoutExpired:
        print("PID {0} did not terminate, so sending SIGKILL".format(pid))
        process.send_signal(signal.SIGKILL)


def command_restart(args):
    """Restart gunicorn, for easy reloading of config"""
    command_stop(args)
    command_start(args)


def command_crawl(args):
    """Crawl the IRC log directory"""
    # We don't actually need "--config" in the command args.
    # I just like seeing it in `ps` so I can see where the config file is.
    cmd = [
        path_to_bin("crawl-irc-logs"),
        '--config', args.config,
    ]
    popen = subprocess.Popen(
        cmd,
        env={
            "FLASK_SETTINGS": args.config,
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out_data, err_data = popen.communicate()

    if out_data:
        print(out_data.decode("utf-8"), file=sys.stdout)
    if err_data:
        print(err_data.decode("utf-8"), file=sys.stderr)


def add_config_argument(parser, required=False):
    """Add the ``--config`` argument to the given ``parser``."""
    parser.add_argument(
        "--config",
        dest="config",
        required=required,
        type=file_path_arg_type,
        help="Path to the combined flask and gunicorn config .py file")


if __name__ == "__main__":
    description = "Controls the running and stopping of {0}".format(APP_NAME)
    parser = argparse.ArgumentParser(description=description)

    subparsers = parser.add_subparsers(title="command")

    start_parser = subparsers.add_parser("start", help="Start the app")
    add_config_argument(start_parser, required=True)
    start_parser.set_defaults(func=command_start)

    stop_parser = subparsers.add_parser("stop", help="Stop the app")
    # We only care about the config if the pidfile is not in the default
    # location.
    add_config_argument(stop_parser, required=False)
    stop_parser.set_defaults(func=command_stop)

    restart_parser = subparsers.add_parser("restart", help="Restart the app")
    add_config_argument(restart_parser, required=True)
    restart_parser.set_defaults(func=command_restart)

    crawl_parser = subparsers.add_parser("crawl", help="Crawl the IRC logs")
    add_config_argument(crawl_parser, required=True)
    crawl_parser.set_defaults(func=command_crawl)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)

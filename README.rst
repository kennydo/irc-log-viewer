IRC Log Viewer
==============
This is a simple web application to securely view ZNC IRC logs, designed to make it easy for users on mobile devices to view IRC logs while on the go. It uses Google OAuth for authentication, and the user specifies the access control in the config file.

This application is comprised of two components: the Flask frontend, and a daemon that continually crawls the ZNC log directory to update a SQLite database of logs.

Note that this application requires Python 3.4+.

Install
=======

#. ``git clone`` this repository.
#. Register an application on the `Google Developer Console <https://console.developers.google.com/>`_.
#. Under "API & auth" and then "Credentials", create a "Client ID".
#. Add the appropriate "Redirect URI" to the list of authroized redirect URIs. The scheme, hostname, and port will vary, but it should end in "/auth/login/authorized".
#. Copy ``irclogviewer/config/dev.py`` to somewhere safe, and update the configuration values. Paste in the "Client ID" and "Client Secret" from the Developer Console to the appropriate config values.
#. Install the dependencies (ideally, inside a virtual environment) with ``pip install -r requirements.txt``.

Run
===

#. First, start the crawling daemon with the following command: ``python manage.py --config path_to_your_config.py``
#. Then, start the web app with: ``python manage.py start --config path_to_your_config.py``

"restart" and "stop" are also supported commands.

For development, the "debug" command will run the Flask app in the foreground.

Icon
====
The icon is a cropped and slightly modified version of https://www.flickr.com/photos/pfly/1537122018, taken by pfly and shared under https://creativecommons.org/licenses/by-sa/2.0/


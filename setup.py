from setuptools import setup, find_packages


setup(
    name='irc-log-viewer',
    version='0.0.1',

    description='Simple app to view IRC logs',

    author='Kenny Do',
    author_email='chinesedewey@gmail.com',

    license='3-clause BSD',

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'crawl-irc-logs = irclogviewer.crawler:main'
        ]
    }
)

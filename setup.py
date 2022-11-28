#!/usr/bin/env python3

from distutils.core import setup
import sys

if sys.version_info != (3, ):
	print("rawdog requires Python 3.")
	sys.exit(1)

setup(name="rawdog",
	version="3.0",
	description="RSS Aggregator Without Delusions Of Grandeur - python3 port",
	author="echarlie",
	author_email="echarlie@vtluug.org",
	url="https://github.com/echarlie/rawdog-py3"
	scripts=['rawdog'],
	data_files=[('share/man/man1', ['rawdog.1'])],
	install_requires=['feedparser'],
	packages=['rawdoglib'],
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Environment :: Console",
		"License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
		"Operating System :: POSIX",
		"Programming Language :: Python :: 3",
		"Topic :: Internet :: WWW/HTTP",
	])

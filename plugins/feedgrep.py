r"""rawdog plugin to limit articles using regular expressions
Copyright 2005 Steve Atwell <atwell@uiuc.edu>

This rawdog plugin filters articles for a feed using Python's regular
expressions.  Only articles containing a match to the regular expression
are kept.  Both the title and the description are searched.  It adds a
"grep" feed option with the following syntax:

    grep [opts] regular expression

The following options are supported:

    -i   Perform case-insensitive matching.
    -s   Strip HTML tags and newlines.  Tags and newlines are converted
         to spaces, and multiple spaces are then condensed into a single
         space.
    -v   Invert the sense of matching so that only articles not containg
         a match are kept.

The regular expression should not be quoted.  Any characters after the
options are considered part of the regular expression, although trailing
spaces are trimmed.  Regular expressions that start with the "-"
character should start with "\-" instead.

Example Configuration:

    feed 1h http://www.mysite.com/myfeed.rdf
        grep -i dell monitor

    feed 1h http://www.mysite.com/myfeed2.rdf
        grep \b[Ii]nteresting\b|\bexciting\b

Limitations:

Only one regular expression can be specified per feed.

"""

import rawdoglib.rawdog
import rawdoglib.plugins
import re

__version__ = "1.0"
__author__ = "Steve Atwell <atwell@uiuc.edu>"
__date__ = "$Date: 2005-01-22 21:07:56 -0600 (Sat, 22 Jan 2005) $"

class _RECache:
	def __init__(self):
		self._cache = {}

	def compile(self, pattern, flags=0):
		try:
			return self._cache[(pattern, flags)]
		except KeyError:
			compiled = re.compile(pattern, flags)
			self._cache[(pattern, flags)] = compiled
			return compiled


cache = _RECache()
stripre = re.compile(r'<.*?>|\n')
spacere = re.compile(r' +')

def grep(rawdog, config, article, ignore):
	"""Handle new articles using the article_seen hook."""

	global cache, stripre, spacere

	ignore.value = False
	feedargs = rawdog.feeds[article.feed].args

	if "grep" in feedargs:
		reflags = re.U + re.S
		invert = False
		strip = False

		# Parse options
		grepline = feedargs["grep"].strip()
		while grepline[0] == "-":
			try:
				(opt, grepline) = grepline.split(None, 1)
			except ValueError:
				raise rawdoglib.rawdog.ConfigError("feedgrep: missing regex for feed %s" % (article.feed,))
			for o in opt[1:]:
				if o == "i":
					reflags += re.I
				elif o == "v":
					invert = True
				elif o == "s":
					strip = True
				else:
					raise rawdoglig.rawdog.ConfigError("feedgrep: bad option -%s for feed %s" % (o, article.feed))
			
		ignore.value = True
		grepre = cache.compile(grepline, reflags)

		# Copy the text we will search so that we can modify
		# it if the strip option is set
		text = []
		for piece in ["title", "summary"]:
			if (piece in article.entry_info):
				text.append(article.entry_info[piece])

		# Strip text.  First replace HTML tags and newlines with
		# spaces, and then condense multiples spaces into a
		# single space.
		if strip:
			for i in range(len(text)):
				text[i] = stripre.sub(' ', text[i])
				text[i] = spacere.sub(' ', text[i])
			
		for piece in text:
			if (grepre.search(piece)):
				ignore.value = False
				break

		if invert:
			ignore.value = not ignore.value

		# if we decided to ignore this, don't bother processing
		# it further
		return not ignore.value

	return True

rawdoglib.plugins.attach_hook("article_seen", grep)

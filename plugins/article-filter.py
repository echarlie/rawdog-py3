# rawdog plugin to filter articles on various criteria
# Copyright 2006, 2009, 2012, 2013 Adam Sampson <ats@offog.org>
#
# This is configured by giving a "filter" argument to the relevant feed, which
# contains a number of entries separated by spaces; each entry starts with
# "show" or "hide", then has a number of field-name/regexp pairs. All the
# expressions in an entry must match for it to be activated.
#
# The field names permitted are the fields of an "entry" in feedparser;
# see the sections called "entries[i].fieldname" in the feedparser manual at
# <http://pythonhosted.org/feedparser/> for more details. Some possibilities:
# title, summary, link, content, id, author...
#
# Some examples might make it clearer:
#
# # I don't want to see articles by Xeni or Cory -- well, except Cory's
# # articles about robots.
# feed 30m http://boingboing.net/rss.xml
#   filter hide author "^Xeni" ; hide author "^Cory" ; show author "^Cory" title "(?i)robot"
#
# # I only want to see articles by Mark.
# feed 30m http://boingboing.net/rss.xml
#   filter hide ; show author "^Mark"

import rawdoglib.plugins, sys, re

def parse_quoted(s):
	"""Parse a string that contains a number of space-separated items,
	which may optionally be surrounded by quotes, into a list of
	strings."""
	l = []
	i = 0
	while i < len(s):
		while s[i] == ' ':
			i += 1
		if s[i] == '"':
			b = i + 1
			e = s.find('"', i + 1)
		else:
			b = i
			e = s.find(' ', i + 1)
		if e == -1:
			e = len(s)
		l.append(s[b:e])
		i = e + 1
	return l

def match_article(rawdog, article):
	hide = False

	fargs = rawdog.feeds[article.feed].args
	if "filter" in fargs:
		filter = fargs["filter"]
		vs = parse_quoted(filter)
		i = 0
		while i < len(vs):
			if vs[i] not in ("show", "hide"):
				print("Expected show or hide but got " + vs[i] + " in filter: " + filter, file=sys.stderr)
				return True
			value = (vs[i] == "hide")
			matched = True
			i += 1
			while i < len(vs) and vs[i] != ";":
				info = article.entry_info
				if i + 1 >= len(vs):
					print("Expected regexp at end of filter: " + filter, file=sys.stderr)
					return True
				if not vs[i] in info:
					print("Bad field name " + vs[i] + " in filter: " + filter, file=sys.stderr)
					return True
				try:
					m = re.search(vs[i + 1], info[vs[i]])
					if m is None:
						matched = False
				except re.error:
					print("Bad regular expression " + vs[i + 1] + " in filter: " + filter, file=sys.stderr)
					return True
				i += 2
			if matched:
				hide = value
			if i < len(vs) and vs[i] == ";":
				i += 1

	return hide

def output_sorted_filter(rawdog, config, articles):
	orig = len(articles)
	config.log("article-filter: examining ", orig, " articles")
	for i in reversed(list(range(len(articles)))):
		if match_article(rawdog, articles[i]):
			del articles[i]
	config.log("article-filter: hid ", orig - len(articles), " articles")
	return True

rawdoglib.plugins.attach_hook("output_sorted_filter", output_sorted_filter)

# rawdog plugin to chop the "whatever: " prefix off Twitter messages.
# Copyright 2010, 2013 Adam Sampson <ats@offog.org>
#
# I wrote this a while ago, and it's probably not very useful now Twitter have
# essentially killed off their feeds, except as an example of how to mangle
# item content.

import rawdoglib.plugins
from rawdoglib.rawdog import parse_bool

def article_seen(rawdog, config, article, ignore):
	args = rawdog.feeds[article.feed].args
	if (article.feed.startswith("http://twitter.com/statuses/")
	    or parse_bool(args.get("detwit", "false"))):
		detail = article.entry_info["title_detail"]
		i = detail["value"].find(": ")
		if i != -1:
			detail["value"] = detail["value"][i + 2:]
	return True

rawdoglib.plugins.attach_hook("article_seen", article_seen)

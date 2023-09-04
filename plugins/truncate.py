# rawdog plugin to truncate article descriptions to N characters.
# Copyright 2006, 2013 Adam Sampson <ats@offog.org>
#
# To use this, give the feed you want to truncate a "truncate" argument:
# feed 30m http://offog.org/books/feed.rss
#   truncate 40
#
# To truncate all articles, make that a default option for all feeds:
# feeddefaults
#   truncate 40
#
# You can also remove all HTML tags from the descriptions before truncating
# them, which'll make the formatting a bit nicer if you're aiming for very
# short descriptions:
#   killtags true

import rawdoglib.plugins, re

def article_seen(rawdog, config, article, ignore):
	fargs = rawdog.feeds[article.feed].args
	n = int(fargs.get("truncate", "0"))
	killtags = fargs.get("killtags", False) == "true"

	def process(detail, n):
		v = detail["value"]
		if killtags:
			v = re.sub(r'<[^>]*>', ' ', v)
		if n != 0 and len(v) > n:
			# Don't break a tag in half.
			l = v.rfind("<", 0, n)
			r = v.rfind(">", 0, n)
			if l != -1 and r < l:
				n = l

			v = v[:n].rstrip() + "..."
		detail["value"] = v.strip()

	ei = article.entry_info
	if "content" in ei:
		for detail in ei["content"]:
			process(detail, n)
	if "summary_detail" in ei:
		process(ei["summary_detail"], n)

	return True

rawdoglib.plugins.attach_hook("article_seen", article_seen)

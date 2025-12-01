"""
feed grouping and indexing for rawdog
Copyright 2006 Zephaniah E. Hull <warp@aehallh.com>

Written and tested with rawdog 2.6, unknown if it works with older versions.

Writes out articles grouped by the define_group setting on feeds,
with an 'Other' group for articles from feeds without the setting.

Also generates a header with links to each group with articles.
"""

import os
import rawdoglib.plugins
from rawdoglib.rawdog import DayWriter, write_ascii, fill_template
from io import StringIO

def output_write_files(rawdog, config, articles, article_dates):
	f_hdr = StringIO()
	rawdoglib.plugins.call_hook("output_items_begin", rawdog, config, f_hdr)
	remaining = articles[:]
	groups = {}
	other_count = 0

	for url, feed in list(rawdog.feeds.items()):
		if ("define_group" in feed.args):
			group = feed.args["define_group"]
			group = group.replace("_", " ")
			if (group in groups):
				groups[group]["feeds"].append(feed)
			else:
				groups[group] = {"count" : 0, "feeds" : [feed]}

	f = StringIO()
	for (key, group) in list(groups.items()):
		dw = DayWriter(f, config)
		f.write("<hr>\n")
		f.write('<h1><a name="' + key + '">' + key + '</a></h1>\n')

		for article in remaining[:]:
			for feed in group["feeds"]:
				if article.feed == feed.url:
					if not rawdoglib.plugins.call_hook("output_items_heading", rawdog, config, f, article, article_dates[article]):
						dw.time(article_dates[article])

					rawdog.write_article(f, article, config)
					remaining.remove(article)
					group["count"] += 1
		dw.close()

	f.write("<hr>\n")
	if remaining:
		dw = DayWriter(f, config)
		f.write('<h1><a name="Other">Other</a></h1>\n')

		for article in remaining:
			if not rawdoglib.plugins.call_hook("output_items_heading", rawdog, config, f, article, article_dates[article]):
				dw.time(article_dates[article])

			rawdog.write_article(f, article, config)
			other_count += 1

	f_hdr.write("<ul>\n")
	for (key, group) in list(groups.items()):
		if group["count"]:
			f_hdr.write('<li><a href="#%(key)s">%(key)s (%(count)d items)</a></li>\n' % {'key' : key, 'count' : group["count"]})
	if other_count:
		f_hdr.write('<li><a href="#%(key)s">%(key)s (%(count)d items)</a></li>\n' % {'key' : 'Other', 'count' : other_count})
	f_hdr.write("</ul>\n")

	rawdoglib.plugins.call_hook("output_items_end", rawdog, config, f)

	bits = rawdog.get_main_template_bits(config)
	bits["items"] = f_hdr.getvalue() + f.getvalue()
	bits["num_items"] = str(len(rawdog.articles))
	rawdoglib.plugins.call_hook("output_bits", rawdog, config, bits)
	s = fill_template(rawdog.get_template(config), bits)
	outputfile = config["outputfile"]
	if outputfile == "-":
		write_ascii(sys.stdout, s, config)
	else:
		config.log("Writing output file: ", outputfile)
		f = open(outputfile + ".new", "w")
		write_ascii(f, s, config)
		f.close()
		os.rename(outputfile + ".new", outputfile)
	return False

rawdoglib.plugins.attach_hook("output_write_files", output_write_files)

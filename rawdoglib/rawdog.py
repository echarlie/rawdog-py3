# rawdog: RSS aggregator without delusions of grandeur.
# Copyright 2003 Adam Sampson <azz@us-lot.org>
#
# rawdog is free software; you can redistribute and/or modify it
# under the terms of that license as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# rawdog is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rawdog; see the file COPYING. If not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307 USA, or see http://www.gnu.org/.

VERSION = "1.9rc1"
import feedparser
from persister import Persistable, Persister
import os, time, sha, getopt, sys, re, urlparse, cgi
from StringIO import StringIO
import timeoutsocket

def format_time(secs, config):
	"""Format a time and date nicely."""
	t = time.localtime(secs)
	return time.strftime(config["timeformat"], t) + ", " + time.strftime(config["dayformat"], t)

def select_content(contents):
	"""Select the best content element from an Echo feed."""
	if type(contents) == str:
		return contents
	preferred = ["text/html", "application/xhtml+xml"]
	cs = []
	for c in contents:
		ctype = c["type"]
		if ctype in preferred:
			score = preferred.index(ctype)
			cs.append((score, c["value"]))
	cs.sort()
	if len(cs) == 0:
		return None
	else:
		return cs[0][1]

def encode_references(s):
	"""Encode characters in a Unicode string using HTML references."""
	r = StringIO()
	for c in s:
		n = ord(c)
		if n >= 128:
			r.write("&#" + str(n) + ";")
		else:
			r.write(c)
	v = r.getvalue()
	r.close()
	return v

def sanitise_html(html, inline = 0):
	"""Attempt to turn arbitrary feed-provided HTML into something
	suitable for safe inclusion into the rawdog output. The inline
	parameter says whether to expect a fragment of inline text, or a
	sequence of block-level elements."""
	if html is None:
		return None
	p = feedparser.HTMLSanitizer()
	p.feed(html)
	return p.output()

template_re = re.compile(r'__(.*?)__')
def fill_template(template, bits):
	"""Expand a template, replacing __x__ with bits["x"], and only
	including sections bracketed by __if_x__ .. __endif__ if bits["x"]
	is not "" (these cannot be nested). If not bits.has_key("x"),
	__x__ expands to ""."""
	f = StringIO()
	l = template_re.split(template)
	i = 0
	writing = 1
	while 1:
		if writing:
			f.write(l[i])
		i += 1
		if i == len(l):
			break
		key = l[i]
		if key.startswith("if_"):
			k = key[3:]
			if bits.has_key(k) and bits[k] != "":
				writing = 1
			else:
				writing = 0
		elif key == "endif":
			writing = 1
		elif bits.has_key(key):
			f.write(bits[key])
		i += 1
	return f.getvalue()

file_cache = {}
def load_file(name):
	"""Read the contents of a file, caching the result so we don't have to
	read the file multiple times."""
	if not file_cache.has_key(name):
		f = open(name)
		file_cache[name] = f.read()
		f.close()
	return file_cache[name]

def short_hash(s):
	"""Return a human-manipulatable 'short hash' of a string."""
	return sha.new(s).hexdigest()[-8:]

class Feed:
	"""An RSS feed."""

	def __init__(self, url):
		self.url = url
		self.period = 30
		self.args = {}
		self.etag = None
		self.modified = None
		self.title = None
		self.link = None
		self.last_update = 0

	def needs_update(self, now):
		"""Return 1 if it's time to update this feed, or 0 if its
		update period has not yet elapsed."""
		if (now - self.last_update) < (self.period * 60):
			return 0
		else:
			return 1
	
	def update(self, articles, now):
		"""Fetch articles from a feed and add them to the collection.
		Returns 1 if any articles were read, 0 otherwise."""

		if self.args.has_key("user") and self.args.has_key("password"):
			authinfo = (self.args["user"], self.args["password"])
		else:
			authinfo = None
		proxies = {}
		for key in self.args.keys():
			if key.endswith("_proxy"):
				proxies[key[:-6]] = self.args[key]
		if len(proxies.keys()) == 0:
			proxies = None

		feedparser.FeedParser.can_contain_dangerous_markup = []
		try:
			p = feedparser.parse(self.url, self.etag,
				self.modified,	"rawdog/" + VERSION,
				None, authinfo, proxies)
			status = p.get("status")
		except:
			p = None
			status = None

		error = None
		non_fatal = 0
		if p is None:
			error = "Error parsing feed."
		elif status is None:
			error = "Timeout while reading feed."
		elif status == 301:
			# Permanent redirect. The feed URL needs changing.
			error = "New URL:     " + p["url"] + "\n"
			error += "The feed has moved permanently to a new URL.\n"
			error += "You should update its entry in your config file."
			non_fatal = 1
		elif status in [403, 410]:
			# The feed is disallowed or gone. The feed should be unsubscribed.
			error = "The feed has gone.\n"
			error += "You should remove it from your config file."
		elif status / 100 in [4, 5]:
			# Some sort of client or server error. The feed may need unsubscribing.
			error = "The feed returned an error.\n"
			error += "If this condition persists, you should remove it from your config file."

		self.last_update = now

		if error is not None:
			print >>sys.stderr, "Feed:        " + self.url
			if status is not None:
				print >>sys.stderr, "HTTP Status: " + str(status)
			print >>sys.stderr, error
			print >>sys.stderr
			if not non_fatal:
				return 0

		self.etag = p.get("etag")
		self.modified = p.get("modified")
		# In the event that the feed hasn't changed, then both channel
		# and feed will be empty. In this case we return 0 so that
		# we know not to expire articles that came from this feed.

		self.encoding = p.get("encoding")
		if self.encoding is None:
			self.encoding = "utf-8"

		channel = p["channel"]
		if channel.has_key("title"):
			self.title = self.decode(channel["title"])
		if channel.has_key("link"):
			self.link = self.decode(channel["link"])

		feed = self.url
		seen_items = 0
		sequence = 0
		for item in p["items"]:
			title = self.decode(item.get("title"))
			link = self.decode(item.get("link"))

			date = item.get("date_parsed")
			if date is not None:
				date = time.mktime(date)

			description = None
			if description is None and item.has_key("content"):
				description = self.decode(select_content(item["content"]))
			if description is None:
				description = self.decode(item.get("description"))

			article = Article(feed, title, link, description,
				now, sequence, date)
			sequence += 1

			if articles.has_key(article.hash):
				articles[article.hash].last_seen = now
			else:
				articles[article.hash] = article
			seen_items = 1

		return seen_items

	def decode(self, s):
		"""Convert a string retrieved from the feed from its original
		encoding to our target encoding for HTML output."""
		if s is None:
			return None
		try:
			us = s.decode(self.encoding)
		except ValueError:
			# Badly-encoded string (or misguessed encoding).
			us = s
		except LookupError:
			# Unknown encoding.
			us = s
		return encode_references(us).encode("iso-8859-1")

	def get_html_name(self):
		if self.title is not None:
			return self.title
		elif self.link is not None:
			return self.link
		else:
			return self.url

	def get_html_link(self):
		s = self.get_html_name()
		if self.link is not None:
			return '<a href="' + self.link + '">' + s + '</a>'
		else:
			return s

class Article:
	"""An article retrieved from an RSS feed."""

	def __init__(self, feed, title, link, description, now, sequence, date):
		self.feed = feed
		self.title = title
		self.link = link
		self.description = description
		self.sequence = sequence
		self.date = date

		s = str(feed) + str(title) + str(link) + str(description)
		self.hash = sha.new(s).hexdigest()

		self.last_seen = now
		self.added = now

	def get_sequence(self):
		try:
			return self.sequence
		except AttributeError:
			# This Article came from an old state file.
			return 0

	def get_date(self):
		try:
			return self.date
		except AttributeError:
			# This Article came from an old state file.
			return None

	def can_expire(self, now):
		return ((now - self.last_seen) > (24 * 60 * 60))

class DayWriter:
	"""Utility class for writing day sections into a series of articles."""

	def __init__(self, file, config):
		self.lasttime = [-1, -1, -1, -1, -1]
		self.file = file
		self.counter = 0
		self.config = config

	def start_day(self, tm):
		print >>self.file, '<div class="day">'
		day = time.strftime(self.config["dayformat"], tm)
		print >>self.file, '<h2>' + day + '</h2>'
		self.counter += 1

	def start_time(self, tm):
		print >>self.file, '<div class="time">'
		clock = time.strftime(self.config["timeformat"], tm)
		print >>self.file, '<h3>' + clock + '</h3>'
		self.counter += 1

	def time(self, s):
		tm = time.localtime(s)
		if tm[:3] != self.lasttime[:3]:
			self.close(0)
			self.start_day(tm)
		if tm[:6] != self.lasttime[:6]:
			self.close(1)
			self.start_time(tm)
		self.lasttime = tm

	def close(self, n = 0):
		while self.counter > n:
			print >>self.file, "</div>"
			self.counter -= 1

class ConfigError(Exception): pass

class Config:
	"""The aggregator's configuration."""

	def __init__(self):
		self.config = {
			"feedslist" : [],
			"outputfile" : "output.html",
			"maxarticles" : 200,
			"maxage" : 0,
			"dayformat" : "%A, %d %B %Y",
			"timeformat" : "%I:%M %p",
			"userefresh" : 0,
			"showfeeds" : 1,
			"timeout" : 30,
			"template" : "default",
			"itemtemplate" : "default",
			"verbose" : 0,
			}

	def __getitem__(self, key): return self.config[key]
	def __setitem__(self, key, value): self.config[key] = value

	def load(self, filename):
		"""Load configuration from a config file."""
		try:
			f = open(filename, "r")
			lines = f.readlines()
			f.close()
		except IOError:
			raise ConfigError("Can't read config file: " + filename)
		for line in lines:
			self.load_line(line.strip())

	def load_line(self, line):
		"""Process a configuration line."""

		if line == "" or line[0] == "#":
			return

		l = line.split(None, 1)
		if len(l) != 2:
			raise ConfigError("Bad line in config: " + line)

		if l[0] == "feed":
			l = l[1].split(None)
			if len(l) < 2:
				raise ConfigError("Bad line in config: " + line)
			args = {}
			for a in l[2:]:
				as = a.split("=", 1)
				if len(as) != 2:
					raise ConfigError("Bad feed argument in config: " + a)
				args[as[0]] = as[1]
			self["feedslist"].append((l[1], int(l[0]), args))
		elif l[0] == "outputfile":
			self["outputfile"] = l[1]
		elif l[0] == "maxarticles":
			self["maxarticles"] = int(l[1])
		elif l[0] == "maxage":
			self["maxage"] = int(l[1])
		elif l[0] == "dayformat":
			self["dayformat"] = l[1]
		elif l[0] == "timeformat":
			self["timeformat"] = l[1]
		elif l[0] == "userefresh":
			self["userefresh"] = int(l[1])
		elif l[0] == "showfeeds":
			self["showfeeds"] = int(l[1])
		elif l[0] == "timeout":
			self["timeout"] = int(l[1])
		elif l[0] == "template":
			self["template"] = l[1]
		elif l[0] == "itemtemplate":
			self["itemtemplate"] = l[1]
		elif l[0] == "verbose":
			self["verbose"] = int(l[1])
		elif l[0] == "include":
			self.load(l[1])
		else:
			raise ConfigError("Unknown config command: " + l[0])

	def log(self, *args):
		"""If running in verbose mode, print a status message."""
		if self["verbose"]:
			print >>sys.stderr, "".join(map(str, args))

class Rawdog(Persistable):
	"""The aggregator itself."""

	def __init__(self):
		self.feeds = {}
		self.articles = {}

	def list(self):
		for url in self.feeds.keys():
			feed = self.feeds[url]
			print url
			print "  Hash:", short_hash(url)
			print "  Title:", feed.title
			print "  Link:", feed.link

	def update(self, config, feedurl = None):
		config.log("Starting update")
		now = time.time()

		timeoutsocket.setDefaultSocketTimeout(config["timeout"])

		seenfeeds = {}
		for (url, period, args) in config["feedslist"]:
			seenfeeds[url] = 1
			if not self.feeds.has_key(url):
				config.log("Adding new feed: ", url)
				self.feeds[url] = Feed(url)
			self.feeds[url].period = period
			self.feeds[url].args = args
		for url in self.feeds.keys():
			if not seenfeeds.has_key(url):
				config.log("Removing feed: ", url)
				del self.feeds[url]

		if feedurl is None:
			update_feeds = [url for url in self.feeds.keys()
			                    if self.feeds[url].needs_update(now)]
		elif self.feeds.has_key(feedurl):
			update_feeds = [feedurl]
		else:
			print "No such feed: " + feedurl
			update_feeds = []

		numfeeds = len(update_feeds)
		config.log("Will update ", numfeeds, " feeds")

		count = 0
		seen_some_items = {}
		for url in update_feeds:
			count += 1
			config.log("Updating feed ", count, " of " , numfeeds, ": ", url)
			if self.feeds[url].update(self.articles, now):
				seen_some_items[url] = 1

		count = 0
		for key in self.articles.keys():
			article = self.articles[key]
			if ((not self.feeds.has_key(article.feed))
			    or (seen_some_items.has_key(article.feed)
			        and article.can_expire(now))):
				count += 1
				del self.articles[key]
		config.log("Expired ", count, " articles, leaving ", len(self.articles.keys()))

		self.modified()
		config.log("Finished update")

	def get_template(self, config):
		if config["template"] != "default":
			return load_file(config["template"])

		template = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
"""
		if config["userefresh"]:
			template += """__refresh__
"""
		template += """    <link rel="stylesheet" href="style.css" type="text/css">
    <title>rawdog</title>
</head>
<body id="rawdog">
<div id="header">
<h1>rawdog</h1>
</div>
<div id="items">
__items__
</div>
"""
		if config["showfeeds"]:
			template += """<h2 id="feedstatsheader">Feeds</h2>
<div id="feedstats">
__feeds__
</div>
"""
		template += """<div id="footer">
<p id="aboutrawdog">Generated by
<a href="http://offog.org/code/rawdog.html">rawdog</a>
version __version__
by <a href="mailto:azz@us-lot.org">Adam Sampson</a>.</p>
</div>
</body>
</html>"""
		return template

	def get_itemtemplate(self, config):
		if config["itemtemplate"] != "default":
			return load_file(config["itemtemplate"])

		template = """<div class="item feed-__feed_hash__" id="item-__hash__">
<p class="itemheader">
<span class="itemtitle">__title__</span>
<span class="itemfrom">[__feed_title__]</span>
</p>
__if_description__<div class="itemdescription">
<p>__description__</p>
</div>__endif__
</div>

"""
		return template

	def show_template(self, config):
		print self.get_template(config)

	def show_itemtemplate(self, config):
		print self.get_itemtemplate(config)

	def write(self, config):
		outputfile = config["outputfile"]
		config.log("Starting write")
		now = time.time()

		bits = { "version" : VERSION }

		refresh = 24 * 60
		for feed in self.feeds.values():
			if feed.period < refresh: refresh = feed.period

		bits["refresh"] = """<meta http-equiv="Refresh" """ + 'content="' + str(refresh * 60) + '"' + """>"""

		articles = self.articles.values()
		numarticles = len(articles)
		def compare(a, b):
			"""Compare two articles to decide how they
			   should be sorted. Sort by added date, then
			   by feed, then by sequence, then by hash."""
			i = cmp(b.added, a.added)
			if i != 0:
				return i
			i = cmp(a.feed, b.feed)
			if i != 0:
				return i
			i = cmp(a.get_sequence(), b.get_sequence())
			if i != 0:
				return i
			return cmp(a.hash, b.hash)
		articles.sort(compare)
		if config["maxarticles"] != 0:
			articles = articles[:config["maxarticles"]]

		f = StringIO()
		itemtemplate = self.get_itemtemplate(config)
		dw = DayWriter(f, config)

		count = 0
		for article in articles:
			age = (now - article.added) / 60
			if config["maxage"] != 0 and age > config["maxage"]:
				break

			count += 1
			dw.time(article.added)

			itembits = {}

			feed = self.feeds[article.feed]
			title = sanitise_html(article.title, 1)
			if title == "":
				title = None
			link = article.link
			if link == "":
				link = None
			if feed.args.has_key("format") and feed.args["format"] == "text":
				description = "<pre>" + cgi.escape(article.description) + "</pre>"
			else:
				description = sanitise_html(article.description, 0)
			if description == "":
				description = None

			date = article.get_date()
			if title is None:
				if link is None:
					title = "Article"
				else:
					title = "Link"

			itembits["title_no_link"] = title
			if link is None:
				itembits["title"] = title
			else:
				itembits["title"] = '<a href="' + link + '">' + title + '</a>'

			itembits["feed_title_no_link"] = feed.title
			itembits["feed_title"] = feed.get_html_link()
			itembits["feed_url"] = feed.url
			itembits["feed_hash"] = short_hash(feed.url)
			itembits["hash"] = short_hash(article.hash)

			if description is not None:
				itembits["description"] = description
			else:
				itembits["description"] = ""

			itembits["added"] = format_time(article.added, config)
			if date is not None:
				itembits["date"] = format_time(date, config)
			else:
				itembits["date"] = ""

			f.write(fill_template(itemtemplate, itembits))

		dw.close()
		bits["items"] = f.getvalue()
		config.log("Selected ", count, " of ", numarticles, " articles to write")

		f = StringIO()
		print >>f, """<table id="feeds">
<tr id="feedsheader">
<th>Feed</th><th>RSS</th><th>Last update</th><th>Next update</th>
</tr>"""
		feeds = self.feeds.values()
		feeds.sort(lambda a, b: cmp(a.get_html_name().lower(), b.get_html_name().lower()))
		for feed in feeds:
			print >>f, '<tr class="feedsrow">'
			print >>f, '<td>' + feed.get_html_link() + '</td>'
			print >>f, '<td><a class="xmlbutton" href="' + feed.url + '">XML</a></td>'
			print >>f, '<td>' + format_time(feed.last_update, config) + '</td>'
			print >>f, '<td>' + format_time(feed.last_update + 60 * feed.period, config) + '</td>'
			print >>f, '</tr>'
		print >>f, """</table>"""
		bits["feeds"] = f.getvalue()

		s = fill_template(self.get_template(config), bits)
		if outputfile == "-":
			print s
		else:
			config.log("Writing output file: ", outputfile)
			f = open(outputfile + ".new", "w")
			print >>f, s
			f.close()
			os.rename(outputfile + ".new", outputfile)

		config.log("Finished write")

def usage():
	"""Display usage information."""
	print """rawdog, version """ + VERSION + """
Usage: rawdog [OPTION]...

General options (use only once):
-d|--dir DIR                 Use DIR instead of ~/.rawdog
-v, --verbose                Print more detailed status information
--help                       Display this help and exit

Actions (performed in order given):
-u, --update                 Fetch data from feeds and store it
-l, --list                   List feeds known at time of last update
-w, --write                  Write out HTML output
-f|--update-feed URL         Force an update on the single feed URL
-c|--config FILE             Read additional config file FILE
-t, --show-template          Print the template currently in use
-T, --show-itemtemplate      Print the item template currently in use

Report bugs to <azz@us-lot.org>."""

def main(argv):
	"""The command-line interface to the aggregator."""

	try:
		(optlist, args) = getopt.getopt(argv, "ulwf:c:tTd:v", ["update", "list", "write", "update-feed=", "help", "config=", "show-template", "dir=", "show-itemtemplate", "verbose"])
	except getopt.GetoptError, s:
		print s
		usage()
		return 1

	statedir = os.environ["HOME"] + "/.rawdog"
	for o, a in optlist:
		if o == "--help":
			usage()
			return 0
		elif o in ("-d", "--dir"):
			statedir = a

	# Support old option syntax.
	for action in args:
		if action in ("list", "update", "write"):
			optlist.append(("--" + action, None))
		else:
			optlist.append(("--update-feed", action))

	try:
		os.chdir(statedir)
	except OSError:
		print "No " + statedir + " directory"
		return 1

	config = Config()
	try:
		config.load("config")
	except ConfigError, err:
		print >>sys.stderr, "In config:"
		print >>sys.stderr, err
		return 1

	persister = Persister("state", Rawdog)
	try:
		rawdog = persister.load()
	except:
		print "An error occurred while reading state from " + statedir + "/state."
		print "This usually means the file is corrupt, and removing it will fix the problem."
		return 1

	for o, a in optlist:
		if o in ("-u", "--update"):
			rawdog.update(config)
		elif o in ("-l", "--list"):
			rawdog.list()
		elif o in ("-w", "--write"):
			rawdog.write(config)
		elif o in ("-f", "--update-feed"):
			rawdog.update(config, a)
		elif o in ("-c", "--config"):
			try:
				config.load(a)
			except ConfigError, err:
				print >>sys.stderr, "In " + a + ":"
				print >>sys.stderr, err
				return 1
		elif o in ("-t", "--show-template"):
			rawdog.show_template(config)
		elif o in ("-T", "--show-itemtemplate"):
			rawdog.show_itemtemplate(config)
		elif o in ("-v", "--verbose"):
			config["verbose"] = 1

	persister.save()

	return 0


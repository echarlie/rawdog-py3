# rawdog plugin to automatically download local copies of article links
# using wget.
# Copyright 2009, 2013 Adam Sampson <ats@offog.org>
#
# This plugin supports the following configuration options:
#
# downloaddir       Directory to download files to
# downloadurl       How to link to downloaddir in the generated HTML
#
# If it succeeds in downloading a local copy of an article, it'll add a
# "localcopy" bit to the item template for that article with the URL of the
# copy. You can then add something like this to your item template:
#   __if_localcopy__ (<a href="__localcopy__">local copy</a>)__endif__
#
# This is extremely simplistic. In particular, there's no expiry
# mechanism, and it won't ever try to redownload a file that's already
# there, so you'll probably want to use "find" to periodically remove
# old files from the cache.

import rawdoglib.plugins
from rawdoglib.rawdog import string_to_html
import subprocess, re

class Downloader:
	def __init__(self):
		self.options = {
			"downloaddir": "local-cache",
			"downloadurl": "local-cache",
		}

	def config_option(self, config, name, value):
		if name in self.options:
			self.options[name] = value
			return False
		else:
			return True

	def article_added(self, rawdog, config, article, now):
		self.download_article(config, article.entry_info)
		return True

	def download_article(self, config, entry_info):
		"""Download a local copy of an article."""

		# Find the link from the article.
		link = entry_info.get("link")
		if link == "" or link is None:
			# No link to follow.
			return

		# Build a wget command to download the link (and everything
		# one step away, so we get images, CSS, etc.).
		cmd = [
			"env",
			"LC_ALL=C",
			"wget",
			"-nc",
			"-np",
			"-r", "-l1",
			"-U", "rawdog-download-articles/1.0",
			"-P", self.options["downloaddir"],
			link
			]

		# Run wget, and parse its output to work out where it's saved
		# files to.
		p = subprocess.Popen(cmd, stderr = subprocess.PIPE)
		downloaded = []
		for l in p.stderr.readlines():
			l = l.rstrip()

			m = re.search(rb'- [`\'](.*)\' saved', l)
			if m is not None:
				downloaded.append(m.group(1))
			m = re.search(rb'^File [`\'](.*)\' already there', l)
			if m is not None:
				downloaded.append(m.group(1))
		p.wait()

		if downloaded == []:
			# It didn't suceed in downloading anything.
			return

		# The page we asked for will be the first one it mentioned.
		# Strip downloaddir off the start.
		local_copy = downloaded[0][len(self.options["downloaddir"]) + 1:]
		config.log("Downloaded: ", local_copy)

		# Add an attribute to the article to say where the local copy
		# is.
		entry_info["download_articles_local_copy"] = local_copy

	def output_item_bits(self, rawdog, config, feed, article, bits):
		# Retrieve the local copy attribute we saved above.
		local_copy = article.entry_info.get("download_articles_local_copy")
		if local_copy is None:
			# There isn't one.
			pass
		else:
			# Add a localcopy field to the template.
			bits["localcopy"] = string_to_html(self.options["downloadurl"] + "/" + local_copy, config)

		return True

downloader = Downloader()
rawdoglib.plugins.attach_hook("config_option", downloader.config_option)
rawdoglib.plugins.attach_hook("article_added", downloader.article_added)
rawdoglib.plugins.attach_hook("output_item_bits", downloader.output_item_bits)

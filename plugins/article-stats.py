# When rawdog shuts down, print some simple statistics about articles.
# Copyright 2005 Adam Sampson <ats@offog.org>

import rawdoglib.plugins

class Stats:
	"""Track counts of articles."""
	def __init__(self):
		self.added = 0
		self.updated = 0
		self.expired = 0

	def article_added(self, rawdog, config, article, now):
		self.added += 1
		return True

	def article_updated(self, rawdog, config, article, now):
		self.updated += 1
		return True

	def article_expired(self, rawdog, config, article, now):
		self.expired += 1
		return True

	def shutdown(self, rawdog, config):
		print(("%d %d %d %d" % (self.added, self.updated, self.expired, len(rawdog.articles))))
		return True

stats = Stats()
rawdoglib.plugins.attach_hook("article_added", stats.article_added)
rawdoglib.plugins.attach_hook("article_updated", stats.article_updated)
rawdoglib.plugins.attach_hook("article_expired", stats.article_expired)
rawdoglib.plugins.attach_hook("shutdown", stats.shutdown)


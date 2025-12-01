# Feedwise Plugin version 0.2+ats2 for Rawdog.
# Copyright 2005 Ian Glover <ian@manicai.net>
# Copyright 2006 Adam Sampson <ats@offog.org> (modified somewhat)
#
# Sort articles into chunks by feed rather than date.
#
# The article_per_feed option can be specified in the config file to set the
# maximum number of articles to show per feed.

import rawdoglib.plugins

class FeedwisePlugin:
    def __init__(self):
        self.last_feed = None

    # Scan the sorted list of articles and through away old ones to
    # so we don't exceed the configured limit.
    def limit_articles_per_feed(self, rawdog, config, articles):
        feed_counts = {}
        to_remove = []
        for i in range(len(articles)):
            feed = articles[i].feed
            if feed not in feed_counts:
                feed_counts[feed] = 1
            else:
                feed_counts[feed] = feed_counts[feed] + 1
            if feed_counts[feed] > config.config.get("articles_per_feed", 50):
                # We don't want to from the list whilst iterating through it.
                # So use None as a marker for deletion.
                to_remove.append(articles[i])
        for x in to_remove:
            articles.remove(x)
        return True

    # Sort the articles by feed and inside each feed by time.
    def sort_by_feed(self, rawdog, config, articles):
        def comparator(lhs, rhs):
            if cmp(lhs.feed, rhs.feed) != 0:
                return cmp(lhs.feed, rhs.feed)
            else:
                # Inverted as we want the most recent first.
                return -cmp(lhs.date, rhs.date)
        articles.sort(comparator)
        self.last_feed = None
        self.limit_articles_per_feed(rawdog, config, articles)
        return False

    # Split each feed into its own block.
    def write_divider(self, rawdog, config, f, article, date):
        feed = rawdog.feeds[article.feed]

        # Basic division header.
        basic_divider =  '''<div class="feeddisplay">
<h3 class="feedtitle">%s</h3>
<ul class="feedarticles">
''' % feed.get_html_link(config)

        if self.last_feed == None: # First feed.
            f.write(basic_divider)
        elif self.last_feed != feed: # A new feed. 
            f.write('</ul></div>\n' + basic_divider)
        self.last_feed = feed
        return False

    # All the items have been written but we have a couple of tags open so
    # close those.
    def write_end(self, rawdog, config, f):
        if self.last_feed != None:
            f.write('</ul></div>')
        return True

    # Handle the articles_per_feed configuration option
    def handle_config(self, config, name, value):
        if name == "articles_per_feed":
            config["articles_per_feed"] = int(value)
            return False
        return True


plugin = FeedwisePlugin()

rawdoglib.plugins.attach_hook("output_sort", plugin.sort_by_feed)
rawdoglib.plugins.attach_hook("output_items_heading", plugin.write_divider)
rawdoglib.plugins.attach_hook("output_items_end", plugin.write_end)
rawdoglib.plugins.attach_hook("config_option", plugin.handle_config)

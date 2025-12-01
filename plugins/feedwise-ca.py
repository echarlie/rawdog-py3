# Feedwise Plugin version 0.2 for Rawdog.
# Copyright 2005 Ian Glover <ian@manicai.net>
# Copyright 2005 Craig Allen
#
# Sort articles into chunks by feed rather than date.
# Craig Allen rawdog@knodal.com 2/24/2005:
# - sort by feed title, then article date
# - print more summary info if verbose command line switch is used
# Note: to see a heading for each feed, you must use an explicit template for the item
#  style.  For example, you could put the following just before the item header:
#   __if_divider__ 
#      __divider__
#   __endif__
import rawdoglib.plugins

class FeedwisePlugin:
    def __init__(self):
        last_feed = None

    def startup(self, rawdog, config):
        # Can't work if daysections or timesections is active.
        if config["daysections"]:
            if config['verbose']:
                print("Feedwise Plugin: Turning off daysections configuration option.")
            config["daysections"] = 0
        if config["timesections"]:
            if config['verbose']:
                print("Feedwise Plugin: Turning off timesections configuration option.")
            config["timesections"] = 0

    # Scan the sorted list of articles and through away old ones to
    # so we don't exceed the configured limit.
    def limit_articles_per_feed(self, rawdog, config, articles):
        #from mx.DateTime import Date
        feed_counts = {}
        to_remove = []
        prev_feed = None
        for i in range(len(articles)):
            feed = articles[i].feed
            if i == 0:
                prev_feed = feed
            if feed not in feed_counts:
                feed_counts[feed] = 1
                if (feed_counts[prev_feed] > config["articles_per_feed"]) and config['verbose']:
                    print(('removing %s oldest items from %s' % (feed_counts[prev_feed] - config["articles_per_feed"], prev_feed)))
                prev_feed = feed
            else:
                feed_counts[feed] = feed_counts[feed] + 1
            if feed_counts[feed] > config["articles_per_feed"]:
                # We don't want to from the list whilst iterating through it.
                # So use None as a marker for deletion.
                to_remove.append(articles[i])
        if config['verbose']:
            print('\nbefore articles removed due to limits in "articles_per_feed":')
            for fd in list(feed_counts.keys()):
                print((rawdog.feeds[fd].get_html_name(config), '\t', feed_counts[fd]))
        for x in to_remove:
            articles.remove(x)
        
    # Sort the articles by feed and inside each feed by time.
    def sort_by_feed(self, rawdog, config, articles):
        def comparator(lhs, rhs):
            if cmp(lhs.feed, rhs.feed) != 0:
                #sort by title of feed, not the URL (old way)
                return cmp(rawdog.feeds[lhs.feed].get_html_name(config).lower(), rawdog.feeds[rhs.feed].get_html_name(config).lower())
                #return cmp(lhs.feed, rhs.feed)
            else:
                # Inverted as we want the most recent first.
                return -cmp(lhs.date, rhs.date)
        articles.sort(comparator)
        self.last_feed = None
        self.limit_articles_per_feed(rawdog, config, articles)
    
    # Split each feed into its own block.
    def write_divider(self, rawdog, config, feed, article, bits):
        # Basic division header.
        basic_divider =  '''<div class="feeddisplay">
<h3 class="feedtitle">Feed: %s</h3><ul class="feedarticles">''' \
        % feed.get_html_link(config)
        if self.last_feed == None: # First feed.
            bits['divider'] = basic_divider
        elif self.last_feed != feed: # A new feed. 
            bits['divider'] = '</ul></div>\n' + basic_divider
        self.last_feed = feed
        return 
    
    # All the items have been written but we have a couple of tags open so
    # close those.
    def write_end(self, rawdog, config, f):
        f.write('</ul></div>')
    
    # Handle the articles_per_feed configuration option
    def handle_config(self, config, name, value):
        if name == "articles_per_feed":
            config["articles_per_feed"] = int(value)
            return 0
        return 1


plugin = FeedwisePlugin()

rawdoglib.plugins.attach_hook( "startup", plugin.startup )
rawdoglib.plugins.attach_hook( "output_sort", plugin.sort_by_feed )
rawdoglib.plugins.attach_hook( "output_item_bits", plugin.write_divider )
rawdoglib.plugins.attach_hook( "output_items_end", plugin.write_end )
rawdoglib.plugins.attach_hook( "config_option", plugin.handle_config )

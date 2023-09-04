# rawdog: RSS Aggregator Without Delusions Of Grandeur

 - Original work by Adam Sampson <ats@offog.org>
 - Python 3 porting by echarlie <echarlie@vtluug.org>
 - Plugin porting by blubeam <greenbeam@tutanota.com>

This is a very lazy Python 3 port of the original [rawdog](https://offog.org/code/rawdog/), 
and [plugins](https://offog.org/git/rawdog-plugins/) because pip for python2 isn't
available on Debian 11, and I wasn't going to be bothered to migrate my
newsfeed to a different tool. I ran 2to3, swapped `cgi.encode` for
`html.encode`, and fixed some of the abuse of string types and encodings that
are less-necessary as py3 is UTF-8-by-default. Things may work for you, or not;
I've not tested any plugins (they'd need to be ported to py3 as well), because
I don't use any.

I've haphazardly incremented the version to `3.0`. This seems appropriate.

---

rawdog is a feed aggregator, capable of producing a personal "river of
news" or a public "planet" page. It supports all common feed formats,
including all versions of RSS and Atom. By default, it is run from cron,
collects articles from a number of feeds, and generates a static HTML
page listing the newest articles in date order. It supports per-feed
customizable update times, and uses ETags, Last-Modified, gzip
compression, and RFC3229+feed to minimize network bandwidth usage. Its
behaviour is highly customisable using plugins written in Python.

rawdog has the following dependencies:

- Python 3
- feedparser 5.1.2, less than 6.0
- PyTidyLib 0.2.1 or later (optional but strongly recommended)

To install rawdog on your system, use setuptools -- `python setup.py
install`. This will install feedparser, the `rawdog` command, and the
`rawdoglib` Python module that it uses internally. (If you want to install to a
non-standard prefix, read the help provided by
`python setup.py install --help`.)

rawdog needs a config file to function. Make the directory `.rawdog` in
your $HOME directory, copy the provided file `config` into that
directory, and edit it to suit your preferences. Comments in that file
describe what each of the options does.

You should copy the provided file `style.css` into the same directory
that you've told rawdog to write its HTML output to. rawdog should be
usable from a browser that doesn't support CSS, but it won't be very
pretty.

When you invoke rawdog from the command line, you give it a series of
actions to perform -- for instance, `rawdog --update --write` tells it
to do the `--update` action (downloading articles from feeds), then the
`--write` action (writing the latest articles it knows about to the HTML
file).

For details of all rawdog's actions and command-line options, see the
rawdog(1) man page -- "man rawdog" after installation.

You will want to run `rawdog -uw` periodically to fetch data and write
the output file. The easiest way to do this is to add a crontab entry
that looks something like this:

0,10,20,30,40,50 * * * *        /path/to/rawdog -uw

(If you don't know how to use cron, then `man crontab` is probably a good
start.) This will run rawdog every ten minutes.

If you want rawdog to fetch URLs through a proxy server, then set your
`http_proxy` environment variable appropriately; depending on your
version of cron, putting something like:

    http_proxy=http://myproxy.mycompany.com:3128/

at the top of your crontab should be appropriate. (The http_proxy
variable will work for many other programs too.)

---

There are many plugins which are available, to install a plugin make sure 
that you have `plugindirs plugin` in your config file, and copy the plugin
into the `.rawdog/plugins directory`. 

Maintainers in the following table are most likely no longer active

Name|Maintainer|Purpose
---|---|---
archive|Adam Sampson|Write incoming articles in Atom format to a local archive (needs my atomwriter module)
article-filter|Adam Sampson|Filter articles on a per-feed basis using regular expressions
article-stats|Adam Sampson|Print counts of articles added, updated, expired and stored when rawdog exits
author-no-link|Stephan Manske|Provide author with HTML removed for templates
backwards|Adam Sampson|Example plugin: reverse the article sort order
dated-output|Adam Sampson|Split output into dated files
detwit|Adam Sampson|Remove prefixes from Twitter messages
digest-auth|Adam Sampson|Add HTTP digest authentication support
download-articles|Adam Sampson|Download copies of articles automatically
enclosure|Virgil Bucoci|Display links to article enclosures
feed-execute|Adam Sampson|Execute commands before or after fetching feeds
feedgrep|Steve Atwell|Filter articles by regular expression
feedgroup|Zephaniah E. Hull|Index articles by user-defined groups
feedwise|Virgil Bucoci|Group articles by feed rather than by date
imgstrip|Virgil Bucoci|Replace images with links
inline_link|Brian Jaress|Provide data: links to long article descriptions
links|TheCrypto|Add static links to rawdog's output
ljkludge|Adam Sampson|Work around a bug in LiveJournal digest authentication
paged-output|Adam Sampson|Split output into several smaller files (needs rawdog 2.5rc1 or later)
printnew|Ted T|Send new articles by email
rss|Jonathan Riddell|Export RSS, FOAF and OPML automatically for all feeds
select-feeds|Adam Sampson|Select feeds to include in the output
sidebarfeedwise|Gutemberg A. Vieira|Feed-grouped display with a sidebar
since-last|Adam Sampson|When writing, only include articles that haven't previously been written
slashdot|Virgil Bucoci|Display Slashdot's department lines in articles
status-log|Adam Sampson|Keep and display a log of errors when fetching feeds
tagcat|Decklin Foster|Organise feeds using user-defined tags
truncate|Adam Sampson|Truncate and/or strip HTML markup from articles
vellum-templates|Adam Sampson|Replace rawdog's templating system with the one from Vellum
xml_archiver|BAM|Write rawdog's article database out as XML for external processing

---

In the event that rawdog gets horribly confused (for instance, if your
system clock has a huge jump and it thinks it won't need to fetch
anything for the next thirty years), you can forcibly clear its state by
removing the `~/.rawdog/state` file (and the `~/.rawdog/feeds/*.state`
files, if you've got the "splitstate" option turned on).

If you don't like the appearance of rawdog, then customise the style.css
file. If you come up with one that looks much better than the existing
one, please send it to me!

This should, hopefully, be all you need to know. If rawdog breaks in
interesting ways, please tell me at the email address at the top of this
file.


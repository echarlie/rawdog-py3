# -*- coding: utf-8 -*-
#
# rawdog plugin to generate RSS, OPML and FOAF output
# Copyright 2008 Jonathan Riddell
# Copyright 2009 Adam Sampson <ats@offog.org>
#
# rawdog_rss is free software; you can redistribute and/or modify it
# under the terms of that license as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# rawdog_rss is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rawdog_rss; see the file COPYING. If not, write to the Free
# Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA, or see http://www.gnu.org/.
#
# ---
#
# This plugin supports the following configuration options:
#
# outputxml         RSS output filename
# outputfoaf        FOAF output filename
# outputopml        OPML output filename
# xmltitle          Feed title (e.g. "Planet Foo")
# xmllink           Feed link (e.g. "http://planet-foo.example.com/")
# xmllanguage       Feed language (e.g. "en")
# xmlurl            URL of the generated RSS (e.g. "http://planet-foo.example.com/rss20.xml")
# xmldescription    Feed description (e.g. "People who work on foo")
# xmlownername      Feed owner's name
# xmlowneremail     Feed owner's email address
# xmlmaxarticles    Maximum number of articles to include in the feed
#                   (defaults to maxarticles if not specified)
#
# If you're using rawdog to produce a planet page, you'll probably want to have
# "sortbyfeeddate true" in your config file too.

import os, time, cgi
import rawdoglib.plugins, rawdoglib.rawdog
import libxml2

from rawdoglib.rawdog import detail_to_html, string_to_html
from time import gmtime, strftime

def rfc822_date(tm):
    """Format a GMT timestamp as returned by time.gmtime() in RFC822 format.
    (This is insensitive to the current locale.)"""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % \
        (days[tm[6]], tm[2], months[tm[1] - 1], tm[0], tm[3], tm[4], tm[5])

class RSS_Feed:
    def __init__(self):
        self.options = {
            "outputxml": "rss20.xml",
            "outputfoaf": "foafroll.xml",
            "outputopml": "opml.xml",
            "xmltitle": "Planet KDE",
            "xmllink": "http://planetKDE.org/",
            "xmllanguage": "en",
            "xmlurl": "http://planetKDE.org/rss20.xml",
            "xmldescription": "Planet KDE - http://planetKDE.org/",
            "xmlownername": "Jonathan Riddell",
            "xmlowneremail": "",
            "xmlmaxarticles": "",
            }

    def config_option(self, config, name, value):
        if name in self.options:
            self.options[name] = value
            return False
        else:
            return True

    def feed_name(self, feed, config):
        """Return the label used for a feed. If it has a "name" define, use
        that; otherwise, use the feed title."""

        if "define_name" in feed.args:
            return feed.args["define_name"]
        else:
            return feed.get_html_name(config)

    def article_to_xml(self, xml_article, rawdog, config, article):
        entry_info = article.entry_info

        id = entry_info.get("id", self.options["xmlurl"] + "#id" + article.hash)
        guid = xml_article.newChild(None, 'guid', string_to_html(id, config))
        guid.setProp('isPermaLink', 'false')

        title = self.feed_name(rawdog.feeds[article.feed], config)
        s = detail_to_html(entry_info.get("title_detail"), True, config)
        if s is not None:
            title += ": " + s
        xml_article.newChild(None, 'title', title)

        if article.date is not None:
            date = rfc822_date(gmtime(article.date))
            xml_article.newChild(None, 'pubDate', date)

        s = entry_info.get("link")
        if s is not None and s != "":
            xml_article.newChild(None, 'link', string_to_html(s, config))

        for key in ["content", "summary_detail"]:
            s = detail_to_html(entry_info.get(key), False, config)
            if s is not None:
                xml_article.newChild(None, 'description', s)
                break

        return True

    def write_rss(self, rawdog, config, articles):
        doc = libxml2.newDoc("1.0")

        rss = doc.newChild(None, 'rss', None)
        rss.setProp('version', "2.0")
        rss.setProp('xmlns:dc', "http://purl.org/dc/elements/1.1/")
        rss.setProp('xmlns:atom', 'http://www.w3.org/2005/Atom')

        channel = rss.newChild(None, 'channel', None)
        channel.newChild(None, 'title', self.options["xmltitle"])
        channel.newChild(None, 'link', self.options["xmllink"])
        channel.newChild(None, 'language', self.options["xmllanguage"])
        channel.newChild(None, 'description', self.options["xmldescription"])

        atom_link = channel.newChild(None, 'atom:link', None)
        atom_link.setProp('href', self.options["xmlurl"])
        atom_link.setProp('rel', 'self')
        atom_link.setProp('type', 'application/rss+xml')

        try:
            maxarticles = int(self.options["xmlmaxarticles"])
        except ValueError:
            maxarticles = len(articles)
        for article in articles[:maxarticles]:
            xml_article = channel.newChild(None, 'item', None)
            self.article_to_xml(xml_article, rawdog, config, article)

        doc.saveFormatFile(self.options["outputxml"], 1)
        doc.freeDoc()

    def write_foaf(self, rawdog, config):
        doc = libxml2.newDoc("1.0")

        xml = doc.newChild(None, 'rdf:RDF', None)
        xml.setProp('xmlns:rdf', "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        xml.setProp('xmlns:rdfs', "http://www.w3.org/2000/01/rdf-schema#")
        xml.setProp('xmlns:foaf', "http://xmlns.com/foaf/0.1/")
        xml.setProp('xmlns:rss', "http://purl.org/rss/1.0/")
        xml.setProp('xmlns:dc', "http://purl.org/dc/elements/1.1/")

        group = xml.newChild(None, 'foaf:Group', None)
        group.newChild(None, 'foaf:name', self.options["xmltitle"])
        group.newChild(None, 'foaf:homepage', self.options["xmllink"])

        seeAlso = group.newChild(None, 'rdfs:seeAlso', None)
        seeAlso.setProp('rdf:resource', '')

        for url in sorted(rawdog.feeds.keys()):
            member = group.newChild(None, 'foaf:member', None)

            agent = member.newChild(None, 'foaf:Agent', None)
            agent.newChild(None, 'foaf:name', self.feed_name(rawdog.feeds[url], config))
            weblog = agent.newChild(None, 'foaf:weblog', None)
            document = weblog.newChild(None, 'foaf:Document', None)
            document.setProp('rdf:about', url)
            seealso = document.newChild(None, 'rdfs:seeAlso', None)
            channel = seealso.newChild(None, 'rss:channel', None)
            channel.setProp('rdf:about', '')

        doc.saveFormatFile(self.options["outputfoaf"], 1)
        doc.freeDoc()

    def write_opml(self, rawdog, config):
        doc = libxml2.newDoc("1.0")

        xml = doc.newChild(None, 'opml', None)
        xml.setProp('version', "1.1")

        head = xml.newChild(None, 'head', None)
        head.newChild(None, 'title', self.options["xmltitle"])
        now = rfc822_date(gmtime())
        head.newChild(None, 'dateCreated', now)
        head.newChild(None, 'dateModified', now)
        head.newChild(None, 'ownerName', self.options["xmlownername"])
        head.newChild(None, 'ownerEmail', self.options["xmlowneremail"])

        body = xml.newChild(None, 'body', None)
        for url in sorted(rawdog.feeds.keys()):
            outline = body.newChild(None, 'outline', None)
            outline.setProp('text', self.feed_name(rawdog.feeds[url], config))
            outline.setProp('xmlUrl', url)

        doc.saveFormatFile(self.options["outputopml"], 1)
        doc.freeDoc()

    def output_write(self, rawdog, config, articles):
        self.write_rss(rawdog, config, articles)
        self.write_foaf(rawdog, config)
        self.write_opml(rawdog, config)

        return True

rss_feed = RSS_Feed()
rawdoglib.plugins.attach_hook("config_option", rss_feed.config_option)
rawdoglib.plugins.attach_hook("output_write", rss_feed.output_write)

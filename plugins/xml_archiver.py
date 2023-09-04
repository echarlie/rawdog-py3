# Copyright 2005 BAM

import os, time, cgi
import rawdoglib.plugins, rawdoglib.rawdog
import libxml2

schema_xml = """
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="rawdog">
      <attribute name="last"/>
      <interleave>
	<zeroOrMore>
	  <ref name="itembit"/>
	</zeroOrMore>
	<ref name="feeds"/>
	<ref name="articles"/>
      </interleave>
    </element>
  </start>

  <define name="feeds">
    <element name="feeds">
      <zeroOrMore>
	<element name="feed">
	  <attribute name="title"/>
	  <attribute name="link"/>
	  <attribute name="id"/>
	  <!-- dateTime? -->
	  <attribute name="update_last"/>
	  <attribute name="update_next"/>
	  <attribute name="period"/>
	  <interleave>
	    <optional>
	      <ref name="describe"/>
	    </optional>
	    <zeroOrMore>
	      <ref name="itembit"/>
	    </zeroOrMore>
	  </interleave>
	</element>
      </zeroOrMore>
    </element>
  </define>

  <define name="articles">
    <element name="articles">
      <zeroOrMore>
	<element name="article">
	  <attribute name="id"/>
	  <attribute name="feed"/>
	  <optional><attribute name="title"/></optional>
	  <optional><attribute name="date"/></optional>
	  <optional><attribute name="last_seen"/></optional>
	  <optional><attribute name="added"/></optional>
	  <optional><attribute name="link"/></optional>
	  <interleave>
	    <optional>
	      <ref name="describe"/>
	    </optional>
	    <zeroOrMore>
	      <ref name="itembit"/>
	    </zeroOrMore>
	  </interleave>
	</element>
      </zeroOrMore>
    </element>
  </define>

  <define name="itembit">
    <element name="bit">
      <attribute name="name"/>
      <optional><text/></optional>
    </element>
  </define>

  <define name="describe">
    <element name="describe">
      <optional><text/></optional>
    </element>
  </define>

</grammar>
"""


class XML_Archiver_Exception(Exception): pass

class XML_Archiver:
    def __init__(self, rawdog, config):
        if 'outputxml' in config['defines']:
            self.out_file = config['defines']['outputxml']
        else:
            self.out_file = 'output.xml.gz'
        self.doc_open()

        self.xml_feeds = self.xml.xpathEval('/rawdog/feeds')[0]
        self.xml_articles = self.xml.xpathEval('/rawdog/articles')[0]

        self.xml.setProp('last', str(time.time()))
        self.sync_bits(self.xml, list(config['defines'].items()))

    def doc_open(self):
        if os.path.isfile(self.out_file):
            schema = libxml2.parseMemory(schema_xml, len(schema_xml))
            rngp = schema.relaxNGNewDocParserCtxt().relaxNGParse()
            ctxt = rngp.relaxNGNewValidCtxt()

            self.doc = libxml2.parseFile(self.out_file)
            if self.doc.relaxNGValidateDoc(ctxt) is 0:
                self.xml = self.doc.children
            else:
                raise XML_Archiver_Exception("Can't parse old XML: "
                                             + self.out_file)

        else:
            self.doc = libxml2.newDoc("1.0")
            self.xml = self.doc.newChild(None, 'rawdog', None)
            self.xml.newChild(None, 'feeds', None)
            self.xml.newChild(None, 'articles', None)

    def sync_bits(self, parent, items):
        for name, value in items:
            bit = parent.xpathEval('bit[@name="' + name + '"]')
            if len(bit) is 0:
                bit = parent.newChild(None, 'bit', None)
                bit.setProp('name', name)
            else:
                bit = bit[0]
            bit.setContent(value)
    def describe(self, parent, description):
        xml_d = parent.xpathEval('describe')
        if len(xml_d) is 0:
            xml_d = parent.newChild(None, 'describe', description)
        else:
            xml_d[0].setContent(description)


    def feed_sync(self, rawdog, config, feed, feed_data, error, non_fatal):
        feed_info = feed_data["feed"]
        xml_feed = self.xml_feeds.xpathEval('feed[@id="' +
                                            feed.get_id(config) + '"]')
        if len(xml_feed) is 0:
            xml_feed = self.xml_feeds.newChild(None, 'feed', None)
        else:
            xml_feed = xml_feed[0]

        if 'description' in feed_info:
            self.describe(xml_feed, feed_info['description'])
        else:
            self.describe(xml_feed, '')

        xml_feed.setProp('title', feed_info['title_detail']['value'])
        xml_feed.setProp('link', feed.url)
        xml_feed.setProp('id', feed.get_id(config))
        xml_feed.setProp('update_last', str(feed.last_update))
        xml_feed.setProp('update_next', str(feed.last_update + feed.period))
        xml_feed.setProp('period', str(feed.period))
        self.sync_bits(xml_feed, list(feed.args.items()))

        return True


    def article_add(self, rawdog, config, article, now):
        xml_article = self.xml_articles.newChild(None, 'article', None)
        self.__article_sync(xml_article, rawdog, config, article)

    def article_sync(self, rawdog, config, article, now):
        xml_article = self.xml_articles.xpathEval('article[@id="' +
                                                  article.hash + '"]')
        if len(xml_article) is 0:
            xml_article = self.xml_articles.newChild(None, 'article', None)
        else:
            xml_article = xml_article[0]
        self.__article_sync(xml_article, rawdog, config, article)
    def __article_sync(self, xml_article, rawdog, config, article):
        entry_info = article.entry_info
        xml_article.setProp('id', article.hash)
        xml_article.setProp('feed', rawdog.feeds[article.feed].get_id(config))
        xml_article.setProp('title', entry_info['title_raw'])
        xml_article.setProp('date', str(article.date))
        xml_article.setProp('last_seen', str(article.last_seen))
        xml_article.setProp('added', str(article.added))
        if 'link' in entry_info:
            xml_article.setProp('link', entry_info['link'])

        if 'content' in entry_info:
            for content in entry_info['content']:
                content = content['value']
        elif 'summary_detail' in entry_info:
            content = entry_info['summary_detail']['value']
        content = cgi.escape(content).encode('utf8', 'ignore')
        self.describe(xml_article, content)

        return True


    def __write(self):
        self.doc.setDocCompressMode(9)
        self.doc.saveFormatFile(self.out_file, 1)
        self.doc.freeDoc()
    def write(self, rawdog, config):
        self.__write()
        return True



xml_archiver = {}
def startup(rawdog, config):
    xml_archiver = XML_Archiver(rawdog, config)
    rawdoglib.plugins.attach_hook("feed_fetched", xml_archiver.feed_sync)
    rawdoglib.plugins.attach_hook("article_added", xml_archiver.article_add)
    rawdoglib.plugins.attach_hook("article_updated", xml_archiver.article_sync)
    rawdoglib.plugins.attach_hook("shutdown", xml_archiver.write)
    return True
rawdoglib.plugins.attach_hook("startup", startup)

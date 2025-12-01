"""
rawdog plugin to strip img tags from articles.
Copyright 2006 Virgil Bucoci

author Virgil Bucoci <vbucoci at acm.org>
version 0.3
license: GNU GPL v2.0 

This rawdog plugin strips img tags from feed articles.  More and more
feeds include web-bug and advertisement images these days, the most
notorious example being slashdot.

Having only a couple of tens of bugged articles in a rawdog page
really slows down the page reload (because each web-bug image has a
unique URL/name in every article, so they can trace each article, even
though the images are identical and quite small as images go :D),
taking all the fun away from aggregating the feeds locally and
exposing you to privacy invasion.

By default, images are replaced with the string IMG linked to the
image source, but can also be removed without a trace.

If the image is wrapped in a link, we replace the image with the text
'a' and then put a link to the image itself.

e.g.

   <a href="http://apache.org/">
      <img src="http://apache.org/pb_apache.gif">
   </a> 

is modified like this:

   <a href="http://apache.org/">a</a>
   <a class="imgbutton" href="http://apache.org/pb_apache.gif">IMG</a>


Configuration options:

  imgstrip link
     (default) img tags are replaced with the string IMG linked to the
     image source

  imgstrip none
     img tags are simply removed from the article

The generated link can be styled to be less obtrusive:

    .imgbutton {
            border: 1px solid;
            border-color: #FFF8DC #CDC8B1 #8B8878 #EEE8DC;
            padding: 0 3px;
            font: bold 10px sans-serif;
            color: gray;
            text-decoration: none;
            margin: 0;
    }


CHANGES
0.3
 vb, Tue Oct  3 02:02:41 EEST 2006
 * fixed a bug where an unbalanced end tag would throw a missing
   attribute exception and exit rawdog.  Parsers derived from
   SGMLParser should call SGMLParser.__init__(), or declare a verbose
   attribute, otherwise an unbalanced tag would exit the application

0.2
 Virgil Bucoci, Fri Sep  8 05:43:16 EEST 2006
 * changed regexp substitution with SGMLParser to handle correctly an
   image nested in a link
 * added styling to the generated link

0.1
 * initial release

TODO
  - make a per-feed setting, for feeds those images you want to see (flickr?)
  - something more general for stripping obnoxious tags: font, style,
    script/javascript (maybe tidy already does part of this?)
"""
import rawdoglib.plugins
from sgmllib import SGMLParser
import html.entities

class BaseHTMLProcessor(SGMLParser):
    """Base class for creating HTML processing modules

       This class is designed to take HTML as input and spit out
       equivalent HTML as output.  By itself it's not very
       interesting; you use it by subclassing it and providing the
       methods you need to create your HTML transformation.

       This program is part of 'Dive Into Python', a free Python book
       for experienced programmers.  Visit http://diveintopython.org/
       for the latest version.

       Author: Mark Pilgrim (mark@diveintopython.org)
       Revision: 1.2
       Copyright (c) 2001 Mark Pilgrim
       """
    def __init__(self, verbose=0):
        # XXX: SGMLParser.report_unbalanced() needs a verbose
        # attribute
        SGMLParser.__init__(self, verbose)
    def reset(self):
        # extend (called by SGMLParser.__init__)
        self.pieces = []
        SGMLParser.reset(self)

    def unknown_starttag(self, tag, attrs):
        # called for each start tag
        # attrs is a list of (attr, value) tuples
        # e.g. for <pre class="screen">, tag="pre", attrs=[("class", "screen")]
        # Ideally we would like to reconstruct original tag and attributes, but
        # we may end up quoting attribute values that weren't quoted in the source
        # document, or we may change the type of quotes around the attribute value
        # (single to double quotes).
        # Note that improperly embedded non-HTML code (like client-side Javascript)
        # may be parsed incorrectly by the ancestor, causing runtime script errors.
        # All non-HTML code must be enclosed in HTML comment tags (<!-- code -->)
        # to ensure that it will pass through this parser unaltered (in handle_comment).
        strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs])
        self.pieces.append("<%(tag)s%(strattrs)s>" % locals())

    def unknown_endtag(self, tag):
        # called for each end tag, e.g. for </pre>, tag will be "pre"
        # Reconstruct the original end tag.
        self.pieces.append("</%(tag)s>" % locals())

    def handle_charref(self, ref):
        # called for each character reference, e.g. for "&#160;", ref will be "160"
        # Reconstruct the original character reference.
        self.pieces.append("&#%(ref)s;" % locals())

    def handle_entityref(self, ref):
        # called for each entity reference, e.g. for "&copy;", ref will be "copy"
        # Reconstruct the original entity reference.
        self.pieces.append("&%(ref)s" % locals())
        # standard HTML entities are closed with a semicolon; other entities are not
        if ref in html.entities.entitydefs:
            self.pieces.append(";")

    def handle_data(self, text):
        # called for each block of plain text, i.e. outside of any tag and
        # not containing any character or entity references
        # Store the original text verbatim.
        self.pieces.append(text)

    def handle_comment(self, text):
        # called for each HTML comment, e.g. <!-- insert Javascript code here -->
        # Reconstruct the original comment.
        # It is especially important that the source document enclose client-side
        # code (like Javascript) within comments so it can pass through this
        # processor undisturbed; see comments in unknown_starttag for details.
        self.pieces.append("<!--%(text)s-->" % locals())

    def handle_pi(self, text):
        # called for each processing instruction, e.g. <?instruction>
        # Reconstruct original processing instruction.
        self.pieces.append("<?%(text)s>" % locals())

    def handle_decl(self, text):
        # called for the DOCTYPE, if present, e.g.
        # <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        #        "http://www.w3.org/TR/html4/loose.dtd">
        # Reconstruct original DOCTYPE
        self.pieces.append("<!%(text)s>" % locals())

    def output(self):
        """Return processed HTML as a single string"""
        return "".join(self.pieces)


class StripParser(BaseHTMLProcessor):
    "Replace img tags with links or remove them."
    def __init__(self, strip="link", verbose=0):
        self.strip = strip
        BaseHTMLProcessor.__init__(self, verbose)
    def reset(self):
        self.a = False
        self.img = False
        BaseHTMLProcessor.reset(self)
    def start_a(self, attrs):
        self.a = True
        self.img = False
        self.unknown_starttag("a", attrs)
    def end_a(self):
        self.a = False
        if not self.img:
            self.unknown_endtag("a")
    def do_img(self, attrs):
        if self.strip == 'none':
            return
        self.img = True
        if self.a:
            # we are wrapped in an <a> tag, so we close it
            self.pieces.append("a</a>")
        src = [v for k, v in attrs if k=='src'][0]
        self.pieces.append('<a class="imgbutton" href="%s">IMG</a>' % src)


parser = StripParser(verbose=1)
class ImgStripPlugin:
    """
    Strip img tags from articles.

    The image is replaced by default with a link to the image, but can
    also be only removed with the "imgstrip none" option.
    """
    def imgstrip(self, config, html, baseurl, inline):
        """
        Strip <img> tags from the feed HTML.
        """
        #html.value = self.img.sub(self.repl, html.value)
        parser.reset()
        parser.feed(html.value)
        parser.close()
        html.value = parser.output()

    def config_option(self, config, name, value):
        """
        Configures the stripping through the config file.

        name  - the option name, 'imgstrip'
        value - 'none': simply remove the img tag
                'link': replace the image with a link to image's source.
                        This is the default.
                anything else: raise ValueError
        """
        global parser
        if name == 'imgstrip':
            if value in ('none', 'link'):
                parser = StripParser(value)
                return False
            else:
            	raise ValueError("imgstrip error: option '%s' has invalid value '%s'" \
                      % (name, value))
        return True

istrip = ImgStripPlugin()
rawdoglib.plugins.attach_hook("clean_html", istrip.imgstrip)
rawdoglib.plugins.attach_hook('config_option', istrip.config_option)

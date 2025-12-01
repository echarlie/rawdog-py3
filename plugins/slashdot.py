"""
Copyright 2005 BAM
Copyright 2006 Virgil Bucoci
Copyright 2013 Adam Sampson <ats@offog.org>

Wed Sep  6 16:59:06 EEST 2006
Modified by Virgil Bucoci <vbucoci at acm.org>

Add support for 'from the ... dept.' and section lines to the Slashdot
articles (found in the feed as slash:department and slash:section).

Add the following lines to the item template.  You have to use a file
template, this won't work with the default template.  See the README
and the config files that come with rawdog.

__if_slash-section__
<br /><span class="slash-section">Category <em>__slash-section__</em></span>
__endif__


__if_slash-department__
<br /><span class="slash-dept">from the <em>__slash-department__</em> dept.</spa
n>
__endif__

"""
import rawdoglib.plugins
from rawdoglib.rawdog import string_to_html

class Slashdot:
    def output(self, rawdog, config, feed, article, itembits):
        try:
            itembits["slash-department"] = string_to_html(article.entry_info['slash_department'], config)
            itembits["slash-section"] = string_to_html(article.entry_info['slash_section'], config)
        except KeyError:
            pass
        return True

rawdoglib.plugins.attach_hook("output_item_bits", Slashdot().output)

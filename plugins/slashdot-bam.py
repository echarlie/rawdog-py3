"""
Add the "from the ... dept." lines to the descriptions of Slashdot
articles (found in the feed as slash:department).

Copyright 2006 BAM
Coypright 2013 Adam Sampson <ats@offog.org>
"""
import rawdoglib.plugins
from rawdoglib.rawdog import string_to_html

class Slashdot:
    html = '%s\n<p style="font-size:x-small">from the %s dept.</p>'
    def output(self, rawdog, config, feed, article, itembits):
        if 'slash_department' not in article.entry_info:
            return True

        dept = string_to_html(article.entry_info['slash_department'], config)
        itembits["description"] = self.html % (itembits["description"], dept)
        return True

rawdoglib.plugins.attach_hook("output_item_bits", Slashdot().output)

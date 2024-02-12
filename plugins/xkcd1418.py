# rawdog plugin to implement the text transformation from XKCD 1418
# (mostly as an example of how to apply regexps to feed descriptions)
# Copyright 2017 Adam Sampson <ats@offog.org>

import rawdoglib.plugins
import re

def match_case(old, new):
    """Adjust the case of letters in new to match old.
    e.g. match_case("XyZ", "abc") == "AbC"
    """
    return "".join(new[i].upper() if old[i].isupper() else new[i]
                   for i in range(len(old)))

def output_item_bits(rawdog, config, feed, article, bits):
    def func(m):
        return match_case(m.group(0), "horse")
    bits["description"] = re.sub(r'force', func, bits["description"])

rawdoglib.plugins.attach_hook("output_item_bits", output_item_bits)

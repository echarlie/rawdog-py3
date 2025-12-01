# rawdog plugin to add author_no_link template item, equivalent to author but
# with HTML removed.
# Copyright 2006 Stephan Manske
# Copyright 2006 Adam Sampson <ats@offog.org>

import rawdoglib.plugins, re

def output_item_bits(rawdog, config, feed, article, bits):
	bits["author_no_link"] = re.sub(r'<[^>]*>', '', bits["author"])
	return True

rawdoglib.plugins.attach_hook("output_item_bits", output_item_bits)

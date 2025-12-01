"""
rawdog plugin to work around a LiveJournal digest auth bug.
Copyright 2005 Adam Sampson <ats@offog.org>

This is a kludge. The problem is described at:
https://sourceforge.net/tracker/?func=detail&atid=305470&aid=1143695&group_id=5470
This should work around the problem without needing to patch urllib2, although
it's not guaranteed to continue to work in the future. (It's also an example of
a plugin that doesn't need to import rawdoglib.plugins!)
"""

import urllib.request, urllib.error, urllib.parse

orig_get_authorization = urllib.request.AbstractDigestAuthHandler.get_authorization
def my_get_authorization(self, req, chal):
	base = orig_get_authorization(self, req, chal)
	if base.find('algorithm=') == -1:
		base += ', algorithm=MD5'
	return base
urllib.request.AbstractDigestAuthHandler.get_authorization = my_get_authorization


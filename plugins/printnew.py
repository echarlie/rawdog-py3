# printnew.py: email new entries to ourselves (or anyone we want)
# Copyright 2005, 2009 Ted T <http://perljam.net/>

import rawdoglib.rawdog
import rawdoglib.plugins

from rawdoglib.rawdog import encode_references

import smtplib
import datetime

from email.MIMEText import MIMEText

class Mailer:
	"""email new articles"""
	def __init__(self):
		self.mailto = ''
		self.mailfrom = ''
		self.mail_str = ''

	def article_added(self, rawdog, config, article, now):
		"""Handle new articles using the article_seen hook."""

		if (not self.mailto):
			return True

		feed = rawdog.feeds[article.feed]

		if 'link' in article.entry_info:
			self.mail_str += '<a href="' + article.entry_info['link'] + '">'
		if 'title' in article.entry_info:
			self.mail_str += article.entry_info['title']
		if 'link' in article.entry_info:
			self.mail_str += '</a>'

		self.mail_str += ' [' + feed.get_html_link(config) + ']'

		if 'description' in article.entry_info:
			self.mail_str += "<br>\n" + article.entry_info['description']
		# finish up the entry. I like a <hr> between each entry with some spacing.
		self.mail_str += "<p><hr><br clear=\"all\">\n"

		return True

	# send mail with the shutdown hook.
	def shutdown(self, rawdog, config):

		if (not self.mailto):
			return True

		if (self.mail_str == ''):
			return True


		msg = MIMEText(encode_references(self.mail_str + "\n\n.\n\n"), "html")
		msg['Subject'] = "rawdog"
		msg['To'] = self.mailto
		msg['From'] = self.mailfrom

		if (not msg['From'] or not msg['To']):
			return True


		# Experience says that 'sendmail' is the easiest/most reliable
		# way to send this mail out. YMMV, and it certainly isn't
		# portable. Leaving the previous version of the code in place.
		#smtp = smtplib.SMTP('localhost')
		#smtp.set_debuglevel(1)
		##smtp.connect('smtp-host.net')
		##smtp.connect('localhost')
		#smtp.sendmail(msg['From'], msg['To'], msg.as_string())
		##smtp.close()
		#smtp.quit()

  		SENDMAIL = "/usr/sbin/sendmail" # sendmail location
  		import os
  		p = os.popen("%s -t" % SENDMAIL, "w")
  		#p.write("To: " + msg['To'] + "\n")
  		#p.write("Subject: rawdog cmdline\n")
  		#p.write("\n") # blank line separating headers from body
  		p.write(msg.as_string())
  		sts = p.close()
  		#if sts != 0:
      		#  print "Sendmail exit status", sts

		return True

	# We expect 'mailto' and 'mailfrom' to be in the config now.
	def config(self, config, name, value):
		if name == 'mailto':
			self.mailto = value
			return False
		elif name == 'mailfrom':
			self.mailfrom = value
			return False
		else:
			return True

mailer = Mailer()

# actually attach our hooks now.
rawdoglib.plugins.attach_hook("article_added", mailer.article_added)
rawdoglib.plugins.attach_hook("shutdown", mailer.shutdown)

rawdoglib.plugins.attach_hook("config_option", mailer.config)



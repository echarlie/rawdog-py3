"""
dated-output plugin for rawdog
Copyright 2009 Adam Sampson <ats@offog.org>

Needs rawdog 2.5rc1 or later, and Python 2.5.

Rather than writing a single output file, this plugin splits the output
into several files by date. The "pagedateformat" strftime format is used
to generate the filenames; it'll switch to a new output file when the
date that produces changes. The newest output file will get the default name,
and older ones will have a "-date" suffix inserted before the last ".".

Various template bits are produced for navigation between the generated pages:

- __dated_output_pages__ is a simple unordered list, in the same format as the
  paged-output plugin.

- __dated_output_calendar__ is a calendar for the current month.

- __dated_output_calendars__ is a series of calendars for all months that
  contain at least one page.

These configuration options are understood:

- "pagedateformat" is the strftime format used to generate filenames.

- "calendarmonthformat" is the strftime format used for month headers in
  calendars.

- "calendardayformat" is the strftime format used for day-name headers in
  calendars.

- "calendardateformat" is the strftime format used for dates in calendars.

It is assumed that you're using rawdog's default article sorting mechanism.
If you're using another plugin that orders the articles differently, this
will not work very well.
"""

import os, time, datetime, calendar
import rawdoglib.plugins
from rawdoglib.rawdog import DayWriter, write_ascii, format_time, fill_template, safe_ftime, encode_references, get_system_encoding
from io import StringIO

def safe_strftime(obj, format):
	"""Call the strftime method on an object, and convert the result to
	ASCII-encoded HTML."""
	u = str(obj.strftime(format), get_system_encoding())
	return encode_references(u)

class DatedOutput:
	def __init__(self):
		self.page_date_format = "%Y-%m-%d"
		self.calendar_month_format = "%B %Y"
		self.calendar_day_format = "%a"
		self.calendar_date_format = "%d"

		self.output_files = {}
		self.current_date = None
		self.current_fn = None
		self.f = None
		self.dw = None

	def config_option(self, config, name, value):
		if name == "pagedateformat":
			self.page_date_format = value
			return False
		elif name == "calendarmonthformat":
			self.calendar_month_format = value
			return False
		elif name == "calendardayformat":
			self.calendar_day_format = value
			return False
		elif name == "calendardateformat":
			self.calendar_date_format = value
			return False
		else:
			return True

	def generate_list(self):
		"""Generate the list of pages."""

		f = StringIO()

		# Sort and reverse the list of dates, so we have the newest
		# first.
		dates = list(self.output_files.keys())
		dates.sort()
		dates.reverse()

		f.write('<ul class="paged_output_pages">\n')
		for date in dates:
			fn = self.output_files[date]

			f.write('<li>')
			if fn != self.current_fn:
				f.write('<a href="' + os.path.basename(fn) + '">')
			f.write(date)
			if fn != self.current_fn:
				f.write('</a>')
			f.write('</li>\n')
		f.write('</ul>\n')

		return f.getvalue()

	def generate_calendar(self):
		"""Generate a calendar for the month containing the current
		date."""

		t = time.strptime(self.current_date, self.page_date_format)
		this_month = datetime.date(t.tm_year, t.tm_mon, 1)

		# Find links to the previous and next months, if they exist.
		prev_date = None
		next_date = None
		dates = list(self.output_files.keys())
		dates.sort()
		for date in dates:
			t = time.strptime(date, self.page_date_format)
			that_month = datetime.date(t.tm_year, t.tm_mon, 1)

			if that_month < this_month:
				prev_date = date
			if that_month > this_month:
				next_date = date
				break

		f = StringIO()
		self.generate_one_calendar(f, this_month, prev_date, next_date)
		return f.getvalue()

	def generate_calendars(self):
		"""Generate calendars for all months."""

		f = StringIO()

		last_month = None
		dates = list(self.output_files.keys())
		dates.sort()
		dates.reverse()
		for date in dates:
			t = time.strptime(date, self.page_date_format)
			month = datetime.date(t.tm_year, t.tm_mon, 1)

			if month == last_month:
				continue
			last_month = month

			self.generate_one_calendar(f, month, None, None)
			f.write('\n')

		return f.getvalue()

	def generate_one_calendar(self, f, this_month, prev_date, next_date):
		"""Generate a calendar for a given month."""

		cal = calendar.Calendar()

		f.write('<table class="calendar">\n')

		# Print the previous/month name/next bar.
		f.write('<tr class="cal-head">\n')
		f.write('<td class="cal-prev">')
		if prev_date is not None:
			f.write('<a href="%s">&lt;</a>' % os.path.basename(self.output_files[prev_date]))
		f.write('</td>\n')
		f.write('<td class="cal-month" colspan="5">%s</td>\n' % safe_strftime(this_month, self.calendar_month_format))
		f.write('<td class="cal-next">')
		if next_date is not None:
			f.write('<a href="%s">&gt;</a>' % os.path.basename(self.output_files[next_date]))
		f.write('</td>\n')
		f.write('</tr>\n')

		# Print the day-names bar.
		f.write('<tr class="cal-days">\n')
		for day in cal.iterweekdays():
			# Find a date that corresponds to the day number we
			# want to print. I don't see a better way to do this
			# in datetime...
			date = datetime.date(1981, 9, 25)
			while date.weekday() != day:
				date += datetime.timedelta(days = 1)

			f.write('<th>%s</th>' % safe_strftime(date, self.calendar_day_format))
		f.write('</tr>\n')

		# Print the weeks of the month.
		for week in cal.monthdatescalendar(this_month.year, this_month.month):
			f.write('<tr class="cal-week">\n')
			for day in week:
				date = safe_strftime(day, self.page_date_format)

				f.write('<td class="cal-day">')
				if day.month != this_month.month:
					f.write('<em class="cal-othermonth">')
					after = '</em>'
				elif date == self.current_date:
					f.write('<strong class="cal-current">')
					after = '</strong>'
				elif date in self.output_files:
					f.write('<a class="cal-link" href="' + os.path.basename(self.output_files[date]) + '">')
					after = '</a>'
				else:
					after = ''
				f.write(safe_strftime(day, self.calendar_date_format))
				f.write(after)
				f.write('</td>')
			f.write('</tr>\n')

		f.write('</table>\n')

	def write_output(self, rawdog, config):
		"""Write out the current output file."""

		bits = rawdog.get_main_template_bits(config)
		bits["items"] = self.f.getvalue()
		bits["num_items"] = str(len(list(rawdog.articles.values())))
		bits["dated_output_pages"] = self.generate_list()
		bits["dated_output_calendar"] = self.generate_calendar()
		bits["dated_output_calendars"] = self.generate_calendars()

		s = fill_template(rawdog.get_template(config), bits)
		fn = self.current_fn
		config.log("dated-output writing output file: ", fn)
		f = open(fn + ".new", "w")
		write_ascii(f, s, config)
		f.close()
		os.rename(fn + ".new", fn)

	def set_filename(self, rawdog, config, fn):
		"""Set the output filename. If it changes, switch to a new
		output file. If set to None, close the current output file."""

		if fn == self.current_fn:
			return

		if self.current_fn is not None:
			self.dw.close()
			self.write_output(rawdog, config)

		if fn is not None:
			self.f = StringIO()
			self.dw = DayWriter(self.f, config)

		self.current_fn = fn

	def output_write_files(self, rawdog, config, articles, article_dates):
		config.log("dated-output starting")

		# Extract the prefix and suffix from the configured outputfile.
		outputfile = config["outputfile"]
		i = outputfile.rfind('.')
		if i != -1:
			prefix = outputfile[:i]
			suffix = outputfile[i:]
		else:
			prefix = outputfile
			suffix = ""

		# Figure out the output filename date for each article.
		article_fn_dates = {}
		self.output_files = {}
		for article in articles:
			tm = time.localtime(article_dates[article])
			date = safe_ftime(self.page_date_format, tm)
			article_fn_dates[article] = date

			if date in self.output_files:
				pass
			elif self.output_files == {}:
				# First output file: use the configured name.
				self.output_files[date] = outputfile
			else:
				# Otherwise use a dated name.
				self.output_files[date] = "%s-%s%s" % (prefix, date, suffix)

		# Write out each article.
		for article in articles:
			date = article_fn_dates[article]
			self.set_filename(rawdog, config, self.output_files[date])
			self.current_date = date

			self.dw.time(article_dates[article])
			rawdog.write_article(self.f, article, config)

		self.set_filename(rawdog, config, None)

		config.log("dated-output done")
		return False

p = DatedOutput()
rawdoglib.plugins.attach_hook("config_option", p.config_option)
rawdoglib.plugins.attach_hook("output_write_files", p.output_write_files)

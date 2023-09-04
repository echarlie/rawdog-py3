"""
vellum-templates.py: rawdog plugin to support Vellum's template syntax

Adapted from templateParser.py from Vellum 1.0a5:
  http://www.kryogenix.org/code/vellum/

Copyright 2002, 2003 Stuart Langridge (original code)
Copyright 2004, 2013 Adam Sampson <ats@offog.org> (rawdog glue)

Vellum is free software; you can redistribute and/or modify it
under the terms of that license as published by the Free Software
Foundation; either version 2 of the License, or (at your option)
any later version.

Vellum is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vellum; see the file COPYING. If not, write to the Free
Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA, or see http://www.gnu.org/.
"""

import rawdoglib.plugins

import re, sys, traceback
try:
	import io as StringIO
except:
	import io

class TemplateParser:
	def __init__(self):
		self.reg = re.compile('(<%=|<%|%>)')

	def fill_template(self, data, dict, result):
		fields = self.reg.split(data)
		fields = [x for x in fields if len(x) != 0]

		in_code = 0
		in_var = 0
		lines = []

		for f in fields:
			if f == '<%':
				in_code = 1
			elif f == '<%=':
				in_var = 1
			elif f == '%>':
				in_code = 0
				in_var = 0
			else:
				if in_code:
					for line in f.split('\n'):
						lines.append(line.strip() + '\n')
				elif in_var:
					lines.append("print >>sys.stdout," + f.strip() + ",\n")
					lines.append("sys.stdout.softspace = 0")
				else:
					lines.append('print >>sys.stdout,"""' + f.replace('"','\\"') + '""",\n')
					lines.append("sys.stdout.softspace = 0")

		indent = 0
		code = ''
		for line in lines:
			if line.strip() == '':
				continue
			if line.strip() == 'end':
				indent -= 1
				continue
			code += ('\t' * indent) + line + '\n'
			if line.rstrip()[-1] == ':':
				indent += 1

		output = io.StringIO()
		stdout = sys.stdout
		sys.stdout = output
		if "sys" not in list(dict.keys()):
			dict["sys"] = sys
		try:
			exec(code, dict)
		except:
			print("Python exception while expanding template:", file=sys.stderr)
			traceback.print_exc()
			sys.exit(1)
		sys.stdout = stdout
		result.value = output.getvalue()
		return False

rawdoglib.plugins.attach_hook("fill_template", TemplateParser().fill_template)


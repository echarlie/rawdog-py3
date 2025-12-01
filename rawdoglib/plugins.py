# plugins: handle add-on modules for rawdog.
# Copyright 2004, 2005, 2013, 2016 Adam Sampson <ats@offog.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# The design of rawdog's plugin API was inspired by Stuart Langridge's
# Vellum weblog system:
#   http://www.kryogenix.org/code/vellum/

from importlib.machinery import SOURCE_SUFFIXES
from importlib.util import spec_from_file_location, module_from_spec
import sys
import os

class Box:
	"""Utility class that holds a mutable value. Useful for passing
	immutable types by reference."""
	def __init__(self, value=None):
		self.value = value

plugin_count = 0

def load_plugins(dir, config):
	global plugin_count

	try:
		files = os.listdir(dir)
	except OSError:
		# Ignore directories that can't be read.
		return

	for file in files:
		if file == "" or file[0] == ".":
			continue

		desc = None
		for d in SOURCE_SUFFIXES:
			if file.endswith(d):
				desc = d
		if desc is None:
			continue

		fn = os.path.join(dir, file)
		config.log("Loading plugin ", fn)

		# See https://docs.python.org/3.11/library/importlib.html#approximating-importlib-import-module
		module_name = f"plugin{plugin_count}"
		spec = spec_from_file_location(module_name, fn)
		if spec is None or spec.loader is None:
			config.log(f"There was a problem loading {fn}, skipping...")
			continue

		module = module_from_spec(spec)
		sys.modules[module_name] = module
		spec.loader.exec_module(module)

		plugin_count += 1

attached = {}

def attach_hook(hookname, func):
	"""Attach a function to a hook. The function should take the
	appropriate arguments for the hook, and should return either True or
	False to indicate whether further functions should be processed."""
	attached.setdefault(hookname, []).append(func)

def call_hook(hookname, *args):
	"""Call all the functions attached to a hook with the given
	arguments, in the order they were added, stopping if a hook function
	returns False. Returns True if any hook function returned False (i.e.
	returns True if any hook function handled the request)."""
	for func in attached.get(hookname, []):
		if not func(*args):
			return True
	return False

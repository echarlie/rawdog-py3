"""
Copyright 2005 TheCrypto
Copyright 2013 Adam Sampson <ats@offog.org>

This plugin adds a list of links that you can put into your rawdog template for those sites that you just can't quite RSS yet.

In the config files use lines of the form

link <url> <name>

These will be turned into links.

In your template use the tag __links__ to have replaced with all the links.

Version 0.1
TheCrypto
"""
import rawdoglib.plugins
from rawdoglib.rawdog import string_to_html

def links_config(config, name, value):
	if 'links' not in config.config:
		config['links'] = []
	if name == "link":
		config['links'].append(value.split(None, 1))
		return False
	else:
		return True

def links_output_bits(rawdog, config, bits):
	links = ""
	for link in config['links']:
		links += '<a href="' + string_to_html(link[0], config) + '">' + string_to_html(link[1], config) + '</a>\n'
	bits['links'] = links

rawdoglib.plugins.attach_hook('config_option', links_config)
rawdoglib.plugins.attach_hook('output_bits', links_output_bits)

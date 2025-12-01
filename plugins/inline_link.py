"""inline-link ver 0.1
Copyright 2006 Brian Jaress

This plugin is for when you want to handle all your feeds in a
consistent way, but they all use the 'description' field differently.
Some of them use it to describe the article, some use it to repeat the
whole article, some make up it up as they go, etc.

This adds an '__inline_link__' for use in the item template.  What you get
is the first N non-html characters of the description, turned into an
inline link of the whole description.  See
http://en.wikipedia.org/wiki/Data:_URL for an explanation of that.

You can set 'inline_charset' and 'inline_length' as feed arguments.  You
probably want to set the default inline_charset to match the encoding
you use for the rawdog template.

Brian Jaress
"""

import rawdoglib.plugins
from re import sub

def inline_link(rawdog, config, feed, article, itembits):
  parts = {}
  args = rawdog.feeds[article.feed].args

  try: parts['title'] = article.entry_info["title"]
  except: parts['title'] = '(no title)'

  try: parts['desc'] = article.entry_info["description"]
  except: parts['desc'] = ''

  try: parts['link'] = article.entry_info["link"]
  except: parts['link'] = ''

  try: inline_length = int(args['inline_length'])
  except: inline_length = 30

  try: inline_charset = args['inline_charset']
  except: inline_charset = 'utf-8'

  parts['short'] = sub('<[^>]*>', '', parts['desc'])[:inline_length]

  parts['html'] = """
  <html><head><title>%(title)s</title></head>
  <body>%(desc)s<br/>
  <a href="%(link)s">[full]</a> 
  </body></html>
  """
  parts['uri'] = 'data:text/html;base64,%(html)s'

  parts['anchor'] = '<a href="%(uri)s">%(short)s</a>'

  for k in parts: parts[k] = str(parts[k]).encode(inline_charset)
  parts['html'] = (parts['html'] % parts).encode('base64')
  for k in ('uri', 'anchor'):
    parts[k] = (parts[k] % parts)

  itembits['inline_link'] = parts['anchor']
  
  return True

rawdoglib.plugins.attach_hook("output_item_bits", inline_link)

"""enclosure.py - rawdog plugin that makes a link for enclosures
Copyright 2006 Virgil Bucoci
Copyright 2013 Adam Sampson (fixed for newer feedparser, escape URLs)

Author: Virgil Bucoci <vbucoci at acm.org>
License: GNU GPL v2.0
Date: Thu Sep  7 03:13:08 EEST 2006

This plugin makes enclosure-href, enclosure-length and
enclosure-type template parameters for the articles with enclosures.

Add the enclosure info to the item template:

    __if_enclosure-href__<div class="enclosure">
    <a href="__enclosure-href__">Enclosure</a> __endif__
    __if_enclosure-type__ __enclosure-type__ __endif__
    __if_enclosure-length__ (__enclosure-length__ bytes) __endif__
    __if_enclosure-href__</div>__endif__

And optionally some formatting, in style.css:

    .enclosure {
            color: gray;
            font-size: small;
            #border-top: 1px solid gray;
            margin: 0;
            padding: 6px;        
    }

"""
import rawdoglib.plugins
from rawdoglib.rawdog import string_to_html

def enclosure(rawdog, config, feed, article, itembits):
    """Adds enclosure-href, enclosure-length and enclosure-type
    template parameters.
    """
    for link in article.entry_info.get("links", []):
        if link["rel"] != "enclosure":
            continue
        for key in ("href", "length", "type", "title"):
            if key in link:
                itembits["enclosure-" + key] = string_to_html(link[key], config)
    return True

rawdoglib.plugins.attach_hook("output_item_bits", enclosure)

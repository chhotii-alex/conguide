#!/usr/bin/env python

# Copyright (c) 2014-2015, Paul Selkirk
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all
# copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
# PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

""" Find participants who might be sorted out of order. """

import csv
import difflib
import re

import cfgparse
import config
import session

cfgparse.parseConfig(config.CFG)

ps = []
config.filereader.read(config.filenames['schedule', 'input'])
for p in sorted(config.participants.values()):
    ps.append(p.name)

def read(fn):
    if config.PY3:
        f = open(fn, 'rt', encoding='utf-8', newline='')
    else:
        f = open(fn, 'rb')
    reader = csv.DictReader(f)
    rows = []
    for row in reader:
        if not config.PY3:
            for key in row:
                row[key] = row[key].decode('utf-8')
        rows.append(row)
    return rows

pb = []
for p in read(config.filenames['bios', 'input']):
    pubsname = p['pubsname']
    pubsname = re.sub('\s+', ' ', pubsname)
    pubsname = re.sub('^\s+', '', pubsname)
    pubsname = re.sub('\s+$', '', pubsname)
    if pubsname in config.chname:
        pubsname = config.chname[pubsname]
    pb.append(pubsname)

for line in difflib.unified_diff(pb, ps):
    print(line)

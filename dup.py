#!/usr/bin/env python

""" Find repeated sessions. Output is formatted for arisia.cfg. """

import argparse

import config

title = {}
descr = {}
dup_t = {}
dup_d = {}

debug = False
verbose = False

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', dest='cfg', default=config.CFG,
                    help='config file (default "%s")' % config.CFG)
parser.add_argument('-d', '--debug', action='store_true',
                    help='add debugging/trace information')
parser.add_argument('-q', '--quiet', action='store_true',
                    help='don\t print warning messages')
parser.add_argument('files', nargs=argparse.REMAINDER,
                    help='one or two snapshots of program data')
args = parser.parse_args()
config.debug = args.debug
config.quiet = args.quiet
config.parseConfig(args.cfg)

config.filereader.read(config.filenames['schedule', 'input'])

for s in config.sessions:
    if s.title in title:
        dup_t[s] = title[s.title]
    else:
        title[s.title] = s

    if s.description:
        if s.description in descr:
            dup_d[s] = descr[s.description]
        else:
            descr[s.description] = s

if dup_t:
    print('# by title')
    for s in sorted(dup_t):
        print('%s = %s\t# %s' % (s.sessionid, title[s.title].sessionid,
                                 s.title))

if dup_d:
    print('# by description')
    for s in sorted(dup_d):
        print('%s = %s\t# %s' % (s.sessionid, descr[s.description].sessionid,
                                 s.title))

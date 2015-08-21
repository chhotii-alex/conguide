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

import copy
import re

import config
import pocketprogram
from room import Room
import session

class Output(pocketprogram.Output):

    def __init__(self, fn, fd=None):
        pocketprogram.Output.__init__(self, fn, fd)
        self.__readconfig()

    def __readconfig(self):
        Output.__readconfig = lambda x: None
        Output.template = {}
        try:
            for key, value in config.items('tracks template'):
                Output.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass
        Output.classifiers = []
        try:
            for area, expr in config.items('tracks classifier'):
                expr = expr.replace('track', 'session.track')
                expr = expr.replace('type', 'session.type')
                expr = re.sub(r'room == (\'\w+\')',
                              r'session.room == Room.rooms[\1]', expr)
                area = area.replace(' - ', u'\u2014')
                Output.classifiers.append((area, expr))
        except config.NoSectionError:
            pass

    def writeTrackNames(self, tracks):
        self.f.write(self.strTrackNames(tracks))

    def writeTrack(self, track):
        self.f.write(self.strTrack(track))

    def writeSession(self, session):
        s = session
        # remove redundant title info
        (title, n) = re.subn(u'^(Autograph\u2014|Reading: )', '', s.title)
        if n:
            title = re.sub(r', ?&', ',', title)
            title = re.sub(r' &', ',', title)
            title = re.sub(r', and ', ', ', title)
            s = copy.copy(s)
            s.title = title
        self.f.write(self.strIndex(s))
        self.f.write(self.strTitle(s))

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__readconfig()

    def __readconfig(self):
        TextOutput.__readconfig = lambda x: None
        TextOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('tracks template text'):
                TextOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

    def cleanup(self, text):
        # convert italics
        return re.sub(r'</?i>', '*', text)

    def strTrackNames(self, tracks):
        return ''

    def strTrack(self, track):
        return '\n%s\n----------------\n' % track

    def strIndex(self, session):
        return '%s\t' % session.sessionid

    def strTitle(self, session):
        return '%s\n' % self.cleanup(session.title)

class HtmlOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__readconfig()
        title = Output.convention + ' Schedule, by Area'
        self.f.write(config.html_header % (title, '', title,
                                           config.source_date))

    def __readconfig(self):
        HtmlOutput.__readconfig = lambda x: None
        HtmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('tracks template html'):
                HtmlOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</dl></body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strTrackNames(self, tracks):
        str = '<ul>\n'
        for t in tracks:
            str += '<li><a href="#%s">%s</a></li>\n' % \
                   (re.sub(r'\W', '', t), self.cleanup(t))
        str += '</ul>\n<dl>'
        return str

    def strTrack(self, track):
        return '</dl><p><a name="%s"></a></p>\n<hr /><h2>%s</h2><dl>\n' % \
            (re.sub(r'\W', '', track), self.cleanup(track))

    def strIndex(self, session):
        return '<dd>%s %s\t' % (session.time.day.shortname, session.time)

    def strTitle(self, session):
        return '<a href="%s#%s">%s</a></dd>\n' % \
            (config.get('output files html', 'schedule'), session.sessionid,
             self.cleanup(session.title))

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self.__readconfig()
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<tracks>')

    def __readconfig(self):
        XmlOutput.__readconfig = lambda x: None
        XmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('tracks template xml'):
                XmlOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</tracks>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strTrack(self, track):
        return '<track>%s</track>\n' % self.cleanup(track)

    def strTrackNames(self, tracks):
        return ''

    def strIndex(self, session):
        return '<tr-session><tr-index>%d</tr-index>\t' % session.index

    def strTitle(self, session):
        return '<tr-title>%s</tr-title></tr-session>\n' % \
            self.cleanup(session.title)

def write(output, sessions):
    track = {}
    for session in sessions:
        t = session.track
        for k, v in Output.classifiers:
            if eval(v):
                t = k
                break
        if config.debug:
            print('%s: %s' % (t, session.title))
        try:
            track[t].append(session)
        except KeyError:
            track[t] = [session]

    output.writeTrackNames(sorted(track))

    for k, v in sorted(track.items()):
        if k:
            output.writeTrack(k)
            for s in v:
                output.writeSession(s)

if __name__ == '__main__':
    import cmdline

    args = cmdline.cmdline(io=True)
    (sessions, participants) = session.read(config.get('input files', 'schedule'))

    for mode in ('text', 'html', 'xml'):
        if eval('args.' + mode):
            output = eval('%sOutput' % mode.capitalize())
            if args.outfile:
                write(output(args.outfile), sessions)
            else:
                try:
                    write(output(config.get('output files ' + mode, 'tracks')),
                          sessions)
                except config.NoOptionError:
                    pass

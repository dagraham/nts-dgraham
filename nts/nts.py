import os, fnmatch
import sys
from pprint import pprint
from anytree import Node, RenderTree #, search
from base64 import b64encode, b64decode
import base64
import re
from prompt_toolkit import prompt, search
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, SearchToolbar
from prompt_toolkit.application import Application
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D

from prompt_toolkit import PromptSession
from prompt_toolkit import shortcuts
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.filters import Condition
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.styles.named_colors import NAMED_COLORS

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign, ConditionalContainer

import subprocess
import requests

from prompt_toolkit import print_formatted_text
import textwrap

import shutil
import logging
import logging.config

import argparse

import nts.__version__ as version
nts_version = version.version

note_regex = re.compile(r'^[\+#]\s+([^\(]+)\s*(\(([^\)]*)\))?\s*$')

separator = os.path.sep


help_notes = [
'h              show this help message.',
'q              quit.',
'v              compare the installed version of nts with the latest version on GitHub (requires an internet connection).',
'p              display path view.',
't              display tags view.',
'l              toggle showing leaves in the outline views.',
'b              toggle showing branches in the outline views.',
'm INTEGER      limit the diplay of nodes in the outline views to INTEGER levels below the starting node. Use INTEGER = 0 to display all levels.',
'/|? STRING     start a case-insensitive, incremental search forward (/) or backward (?) for STRING. When the search is active, press "n" to continue the search in the same or "N" reverse direction, ",," (two commas successively) to clear the search or ".." to apply the search to the complete notes of the active view.',
'f STRING       display complete notes that contain a match in the title, tags or body for the case-insensitive regular expression STRING.',
'g STRING       display note titles that contain a match in the branch nodes leading to the note for the case-insensitive regular expression STRING.',
'j JOIN         display note titles for notes with tags satisfying JOIN. E.g. if JOIN = "red", then notes containing the tag "RED" would be displayed. If JOIN = "| red, blue" then notes with _either_ the tag "red" _or_ the tag "blue" would be displayed. Finally, if JOIN = "& red, blue", then notes with _both_ the tags "red" _and_ "blue" would be displayed. In general JOIN = [|&] comma-separated list of case-insensitive regular expressions.',
'i IDENT        if IDENT is the 2-number line identifier for a note, then display the contents of that note. Else if IDENT is the identifier for a ".txt" file, then display the contents of that file. Otherwise limit the display to that part of the outline which starts from the corresponding node. Use IDENT = 0 to start from the root node.',
'e IDENT        if IDENT corresponds to either a note or a ".txt" file, then open that file for editing and, in the case of a note, scroll to the beginning line of the note.',
'a IDENT [NAME] if IDENT corresponds to either a note or a ".txt" file, then open that file for appending a new note. Otherwise, if IDENT corresponds to a directory and NAME is provided, add a child called NAME to that node. If NAME ends with ".txt", a new note file will be created and opened for editing. Otherwise, a new subdirectory called NAME will be added to the node directory. Use "0" as the IDENT to add to the root (data) node.',
]


def check_update():
    url = "https://raw.githubusercontent.com/dagraham/nts-dgraham/master/nts/__version__.py"
    try:
        r = requests.get(url)
        t = r.text.strip()
        # t will be something like "version = '4.7.2'"
        url_version = t.split(' ')[-1][1:-1]
        # split(' ')[-1] will give "'4.7.2'" and url_version will then be '4.7.2'
    except:
        url_version = None
    if url_version is None:
        res = "update information is unavailable"
    else:
        if url_version > nts_version:
            res = f"An update is available from {nts_version} (installed) to {url_version}"
        else:
            res = f"The installed version of nts, {nts_version}, is the latest available."

    return res


def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def mypathsort(items):
    return sorted(items, key=lambda item: item.name)


def mytagsort(items):
    return sorted(items, key=lambda item: tag_sort.get(item.name.split(' ')[0], item.name.split(' ')[0]) + ' '.join(item.name.split(' ')[1:]))


_to_esc = re.compile(r'\s')

def _esc_char(match):
    return r"\ "

def myescape(name):
    # escape spaces in file/path names
    return _to_esc.sub(_esc_char, name)


def myprint(tokenlines, color=None):
    print_formatted_text(FormattedText(tokenlines), style=style_obj)


def show_message(msg):
    shortcuts.clear()
    # print(f"\n{msg}\n")
    empty_line = ('class:plain', '\n')
    msg_line = ('class:message', f"{msg}\n")
    line = ('class:prompt',
            'To restore the previous display, press "return" with nothing entered\nat the prompt.')
    print_formatted_text(FormattedText([empty_line, msg_line, empty_line, line]), style=style_obj)


def getnotes(filepath):
    notes = []
    with open(filepath, 'r') as fo:
        lines = fo.readlines()

    note = [] # [title, [tags], linenum, [body]]
    body = []
    linenum = -1
    for line in lines:
        linenum += 1
        if line and line[0] == "+" and not note_regex.match(line):
            print(f"Error failed to match: '{line}'\nin filepath: '{filepath}'")
        if note_regex.match(line):
            if note:
                if body and not body[-1]:
                    body = body[:-1]
                note.append(body)
                notes.append(note)
            note = []
            body = []
            m = note_regex.match(line)
            title = m.group(1).strip() if m and m.group(1) else line.strip()
            tags = [x.strip() for x in m.group(3).split(',')] if m and m.group(3) else []

            note_begin = linenum
            note = [title, tags, linenum]
        else:
            body.append(line.rstrip())
    if note:
        if body and not body[-1]:
            body = body[:-1]
        note.append(body)
        notes.append(note)
        note = []
        body = []
    return notes


class NodeData(object):

    def __init__(self, rootdir):
        self.rootdir = rootdir

        self.pathnodes = {} # nodeid -> node for path tree
        # nodeid = relative filepath to directory or file
        # nodes corresponding to files have a lines attribute
        # where the lines are tuples (title, tags, linenum)
        # and the filepath is implicitly given by the nodeid.
        # rows in the tree display have consecutively numbered
        # treeid's with the format "#" for directories and files and
        # the format "#-#" for lines (notes)

        self.tagnodes = {}  # nodeid -> node for tag tree
        # for tags, the tree has the form
        #    tag X -> [notes containing tag X]
        # and thus has only two levels. Here the nodeid is
        # the name of the tag for the top level and a tuple
        # (relative file path, linenumber) for the child note.

        self.id2info = {} # lineid ->
        #       (filepath, linenum) for note lines
        #       (node id, None) for node lines
        # populated when showNode generates tree

        self.nodelines = [] # tree display lines
        # populated when showNode generates tree

        self.notelines = [] # leaf display lines
        # populated with showNotes generates lines

        self.findlines = [] # find display lines
        # populated with find() generates lines

        self.notedetails = {}
        self.shownotes = True
        self.shownodes = True
        self.sessionMode = False
        self.get = None  # regular expression
        self.getstr = ""
        self.join = None # regular expressions joined by 'and' or 'or'
        self.joinstr = ""
        self.startstr = ""

        self.setStart()
        self.setMaxLevel()
        self.getNodes()

        self.mode = 'path'
        self.showingNodes = True


    def setlimits(self):
        msg = []
        if self.start != '.':
            msg.append('i')
        if self.get:
            msg.append('g')
        if self.join:
            msg.append('j')
        if self.maxlevel not in [None, 0]:
            msg.append('m')
        if not self.shownotes:
            msg.append('l')
        if not self.shownodes:
            msg.append('b')

        self.limits = msg


    def setGet(self, get=None):
        if get is None:
            return (False, "required argument missing")
        get = get.strip()
        getstr = f'notes for {self.mode} view branches matching "{get}"'
        self.getstr = f"{getstr}\n{'-'*len(getstr)}"
        self.get = re.compile(r'%s' % get, re.IGNORECASE) if get else None
        # self.showNodes()


    def setJoin(self, join=None):
        if join is None:
            return (False, "required argument missing")
        join = join.strip()
        joinstr = f'notes with tags matching "{join}"'
        self.joinstr = f"{joinstr}\n{'-'*len(joinstr)}"
        if join.startswith('&'):
            mode = 'and'
            join = join[1:]
        elif join.startswith('|'):
            mode = 'or'
            join = join[1:]
        else:
            mode = None
        if mode:
            joinlst = [x.strip() for x in join.split(', ')]
        elif join:
            joinlst = [join]
        self.join = (mode, [re.compile(r'%s' % x, re.IGNORECASE) for x in joinlst]) if join else None
        # sef.showNodes()


    def setMaxLevel(self, maxlevel=None):
        self.maxlevel = None if maxlevel in [0, str(0), None] else maxlevel
        if self.maxlevel is not None:
            try:
                self.maxlevel = int(self.maxlevel)
            except Exception as e:
                self.maxlevel = None


    def toggleShowLeaves(self):
        self.shownotes = not self.shownotes
        # if notes are hidden, make sure nodes are not hidden
        if not self.shownotes:
            self.shownodes = True


    def toggleShowBranches(self):
        self.shownodes = not self.shownodes
        # if nodes are hidden, make sure notes are not hidden
        if not self.shownodes:
            self.shownotes = True


    def setMode(self, mode):
        if mode not in ['path', 'tags']:
            print(f"error: bad mode {mode}")
            return
        self.mode = 'path' if mode == 'path' else "tags"
        self.nodes = self.pathnodes if mode == 'path' else self.tagnodes


    def setStart(self, start='.'):
        self.start = start


    def getNodes(self):
        """
        Create node trees for pathnodes and tagnodes.
        """
        taghash = {}
        self.pathnodes = {}
        self.tagnodes = {}
        self.notedetails = {}
        for root, dirs, files in os.walk(self.rootdir):
            relroot = splitall(os.path.relpath(root, self.rootdir))
            if relroot[0] != '.':
                relroot.insert(0, '.')
            parent = separator.join(relroot[:-1])
            child = relroot[-1]
            key = separator.join(relroot)
            if parent:
                self.pathnodes[key] = Node(child, parent=self.pathnodes[parent])
            else:
                self.pathnodes[key] = Node(child)
            files = [x for x in files if fnmatch.fnmatch(x, "[!.]*.txt")]
            for file in files:
                key = separator.join(relroot)
                filepath = os.path.join(root, file)
                self.pathnodes[f"{key}{separator}{file}"] = Node(file, self.pathnodes[key])
                tmp = f"{key}{separator}{file}"
                notes = getnotes(filepath)
                if notes:
                    notelines = []
                    for x in notes:
                        #  x: [title, [tags], linenum, [body]]
                        titlestr = f"+ {x[0]}"
                        tagstr = f" ({', '.join(x[1])})" if x[1] else ""
                        tmp = [f"{titlestr}{tagstr}"]
                        tmp.extend(x[3])
                        self.notedetails[(filepath, x[2])] = tmp
                        notelines.append([titlestr, tagstr,  (filepath, x[2])])
                        if x[1]:
                            for tag in x[1]:
                                taghash.setdefault(tag, []).append([titlestr, tagstr, (filepath, x[2])])
                        else:
                            # assign the no-tag tag '~'
                            taghash.setdefault('~', []).append([titlestr, tagstr, (filepath, x[2])])
                    self.pathnodes[f"{key}{separator}{file}{separator}notes"] = Node('notes', self.pathnodes[f"{key}{separator}{file}"], lines=notelines)


        self.tagnodes['.'] = Node('.')
        for key, values in taghash.items():
            self.tagnodes[f".{separator}{key}"] = Node(key, self.tagnodes['.'])
            self.tagnodes[f".{separator}{key}{separator}notes"] = Node('notes',
                    self.tagnodes[f".{separator}{key}"], lines=[x for x in values])


    def showNodes(self):
        self.columns, self.rows = shutil.get_terminal_size()
        column_adjust = 2 if self.sessionMode else 1
        self.setlimits()
        id = 0
        id2info = {}
        linenum = 0
        linenum2node = {}
        output_lines = []

        if self.startstr:
            output_lines.insert(0, self.startstr)
        if self.join:
            mode, regxs = self.join
            output_lines.append(self.joinstr)
        if self.get:
            output_lines.append(self.getstr)

        start = self.nodes.get(self.start, self.nodes['.'])
        showlevel = self.maxlevel + 1 if self.maxlevel else None
        thissort = mypathsort if self.mode == 'path' else mytagsort

        for pre, fill, node in RenderTree(start, childiter=thissort, maxlevel=showlevel):
            # node with lines are only used for notes
            if node.name != '.' and not hasattr(node, 'lines'):
                id += 1
            idstr = f" {id}"
            path = [x.name for x in node.path]
            pathstr = separator.join(path)
            if self.get or self.join:
                pre = fill = ""

            if self.get and not self.get.search(pathstr):
                continue


            if node.name.endswith('.txt'):
                pathstr = os.path.join(self.rootdir, pathstr[2:])

            if self.shownotes:
                notenum = 0
                if hasattr(node, 'lines') and node.lines:
                    for line in node.lines:
                        # titlestr, tagstring,  (filepath, linenum)
                        ### join ###
                        if self.join:
                            if not line[1]:
                                continue
                            pre = fill = ""
                            # ok = True
                            for r in regxs:
                                if r.search(line[1]):
                                    logger.debug(f"match in {line[1]}")
                                    ok = True
                                    if mode in ['or', None]:
                                        break
                                    else: # and
                                        continue
                                else: # no match
                                    ok = False
                                    if mode in ['and', None]:
                                        break
                                    else: # or
                                        continue
                            if not ok:
                                continue
                        ### join ###

                        notenum += 1
                        title = line[0]
                        if self.shownodes:
                            excess = len(f"{fill}{title}{line[1]} {id}-{notenum}") + column_adjust - self.columns
                            if excess >= 0:
                                width = len(title) - excess - column_adjust
                                title = textwrap.shorten(title, width=width)
                            output_lines.append(f"{fill}{title}{line[1]} {id}-{notenum}")
                        else:
                            excess = len(f"{title}{line[1]} {id}-{notenum}") + column_adjust - self.columns
                            if excess >= 0:
                                width = len(title) - excess - column_adjust
                                title = textwrap.shorten(title, width=width)
                            output_lines.append(f"{title}{line[1]} {id}-{notenum}")
                        id2info[(id, notenum)] = line[2]
                else:
                    id2info[(id,)] = (pathstr, None)

                    if id > 0 and self.shownodes and not self.get and not self.join:
                        output_lines.append(f"{pre}{node.name}{idstr}")
            else:
                if hasattr(node, 'lines'):
                    linenum -= 1

                else:
                    # id2info[id] = pathstr
                    id2info[(id,)] = (pathstr, None)
                    if id > 0 and self.shownodes:
                        output_lines.append(f"{pre}{node.name}{idstr}")

        self.id2info = id2info
        self.nodelines = output_lines


    def showNotes(self, filepath, linenum=None):
        """display the contens of filepath starting with linenum"""

        selfcolumns, self.rows = shutil.get_terminal_size()
        column_adjust = 2 if self.sessionMode else 1
        output_lines = []
        if self.startstr:
            output_lines.insert(0, self.startstr)
        with open(filepath, 'r') as fo:
            lines = fo.readlines()
        if linenum is None:
            for line in lines:
                line = line.rstrip()
                if line:
                    output_lines.extend(textwrap.wrap(line, width=self.columns-column_adjust, subsequent_indent="  ", initial_indent="  "))
                else:
                    output_lines.append("")
        else:
            output_lines.append(lines[linenum].rstrip())
            for line in lines[linenum+1:]:
                # textwrap will return and empty list if passed a line with only white space characters
                line = line.rstrip()
                if line.startswith('+'):
                    if not output_lines[-1]:
                        # skip the last empty line
                        output_lines = output_lines[:-1]
                    break
                if line:
                    output_lines.extend(textwrap.wrap(line, width=self.columns-column_adjust, subsequent_indent="  ", initial_indent="  "))
                else:
                    output_lines.append("")

        self.notelines = output_lines


    # def tags(self, tag=None):
    #     if tag:
    #         regex = re.compile(r'%s' % tag, re.IGNORECASE)


    def find(self, find=None):
        matching_keys = []
        output_lines = []
        self.find_lines = []
        column_adjust = 4 if self.sessionMode else 2
        find = find.strip()
        if not find:
            return output_lines
        markers = True
        if find.startswith('!'):
            markers = False
            find = find[1:].lstrip()
        regex = re.compile(r'%s' % find, re.IGNORECASE)
        for key, lines in self.notedetails.items():
            match = False
            for line in lines:
                match = regex.search(line)
                if match:
                    logger.debug(f"match: {match}")
                    break
            if match:
                matching_keys.append(key)
        if matching_keys:
            self.columns, rows = shutil.get_terminal_size()
            for identifier, key in self.id2info.items():
                if key in matching_keys:
                    lines = self.notedetails.get(key, [])
                    idstr = "-".join([str(x) for x in identifier])
                    output_lines.append(f"{lines[0]} {idstr}")
                    for line in lines[1:]:
                        line.rstrip()
                        if line:
                            output_lines.extend(textwrap.wrap(line, width=self.columns-column_adjust,
                                subsequent_indent="  ", initial_indent="  "))
                        else:
                            output_lines.append('')
                    output_lines.append('')
            if output_lines and not output_lines[-1]:
                output_lines = output_lines[:-1]

        if markers:
            width = self.columns-column_adjust
            marker = "-"
            header = f'lines matching "{find}" marked with {marker}'
            self.findlines = [header, "-"*len(header)]
            for line in output_lines:
                text = line.rstrip()
                match = regex.search(text)
                if match:
                    text = f"{text : <{width}}{marker : >2}"
                self.findlines.append(text)
        else:
            self.findlines = output_lines


    def showID(self, idstr=None):
        self.showNodes()
        if idstr in [0, "0", '', None]:
            info = ('.', )
            self.startstr = ""
        else:
            try:
                idtup = tuple([int(x) for x in idstr.split('-')])
            except:
                return([False, f"Bad IDENT '{idstr}'"])
            if idtup in self.id2info:
                info = self.id2info[idtup]
            else:
                return([False, f"Bad IDENT '{idstr}'"])

        # info: (key, line)
        if info[0] in self.nodes:
            # we have a starting node
            self.showingNodes = True
            self.setStart(info[0])
            if info[0] != '.':
                startstr = f'starting from {idstr} {info[0]}'
                self.startstr = f"{startstr}\n{'-'*len(startstr)}"
            self.showNodes()
            if not self.sessionMode:
                for line in self.nodelines:
                    print(line)
            return [True, "printed nodelines"]
        elif os.path.isfile(info[0]):
            # we have a filename and linenumber
            self.showingNodes = False
            startstr = info[0].split('data/')[1]
            startstr = f'showing {idstr} ./{startstr}'
            self.startstr = f"{startstr}\n{'-'*len(startstr)}"
            filepath, linenum = info
            self.showNotes(filepath, linenum)
            if not self.sessionMode:
                for line in self.notelines:
                    print(line)
            return [True, "printed notelines"]
        else:
            # shouldn't get here
            return([False, f"Bad IDENT {idstr}"])


    def editID(self, idstr):
        idtup = tuple([int(x) for x in idstr.split('-')])
        info = self.id2info.get(idtup, ('.', ))
        if not os.path.isfile(info[0]):
            return (False, f"Bad IDENT {idstr}")
        info = list(info)
        if len(info) < 2 or not info[1]:
            info[1] = 0
        else:
            info[1] += 1
        filepath, linenum = info
        # hsh = {'filepath': filepath, 'linenum': linenum}
        hsh = {'filepath': myescape(filepath), 'linenum': linenum}
        if self.sessionMode:
            editcmd = session_edit.format(**hsh)
        else:
            editcmd = command_edit.format(**hsh)
        editcmd = [x.strip() for x in editcmd.split(" ") if x.strip()]
        subprocess.call(editcmd)
        return (True, f"Called {editcmd}")


    def addID(self, idstr, text=None):
        retval = ""
        if not self.mode == 'path':
            # only works for nodes in path mode
            return (False, "cancelled: must be in path mode")

        idtup = tuple([int(x) for x in idstr.split('-')])
        if idtup not in self.id2info:
            return (False, f"Bad IDENT: {idstr}")
        info = self.id2info[idtup]
        info = list(info)

        if info[0] in self.nodes:
            # we have a starting node
            path = os.path.join(self.rootdir, info[0][2:])
            if not os.path.isdir(path):
                return (False, f"error: bad path {path}")
            if not text:
                text = prompt(
                        f"directory or filename (ending in '.txt') to add as a child of\n {path}\n> ")
                text = text.strip()
                if not text:
                    return (False, "cancelled")
            child = os.path.join(path, f"{text}")
            root, ext = os.path.splitext(child)
            if ext:
                # adding a new note file
                if ext != ".txt":
                    return (False, f"bad file extension {ext}; '.txt' is required")
                hsh = {'filepath':  myescape(child)}
                if self.sessionMode:
                    editcmd = session_add.format(**hsh)
                else:
                    editcmd = command_add.format(**hsh)
                editcmd = [x.strip() for x in editcmd.split(" ") if x.strip()]
                subprocess.call(editcmd)
            else:
                # adding a new node
                if os.path.isdir(child):
                    return (False, f"'{child}' already exists")
                os.mkdir(child)
                return (True, f"created '{child}'")

            return (True, f"adding root {root} with extension {ext}")

        elif os.path.isfile(info[0]):
            # we have a filename
            filepath, linenum = info
            hsh = {'filepath': myescape(filepath)}
            if self.sessionMode:
                editcmd = session_add.format(**hsh)
            else:
                editcmd = command_add.format(**hsh)
            editcmd = [x.strip() for x in editcmd.split(" ") if x.strip()]
            subprocess.call(editcmd)
        else:
            return (False, f"error: bad index {info}")
        # return


def session():
    columns, rows = shutil.get_terminal_size()
    Data.sessionMode = True

    active_key = 'start'

    def get_statusbar_text():
        lst = [
            ('class:status', ' nts'),
            ('class:status.key', f' {Data.mode[0]}'),
            ('class:status', f'){Data.mode[1:]} view'),
            # ('class:status', ' - Press '),
        ]
        return lst

    def get_statusbar_center_text():
        lst = []
        if Data.limits:
            lst.append(('class:status', 'limits: '))
            for key in Data.limits[:-1]:
                lst.extend([
                    ('class:status.key', f'{key}'),
                    ('class:status', ', '),
                    ]
                    )
            lst.append(('class:status.key', f'{Data.limits[-1]}'))
        return lst

    def get_statusbar_right_text():
        lst = [
            # ('class:status', 'Press '),
            ('class:status.key', 'h'),
            ('class:status', ')elp '),
        ]
        return lst
    status_area = VSplit([
                Window(FormattedTextControl(get_statusbar_text), style='class:status', width=15),
                Window(FormattedTextControl(get_statusbar_center_text),
                    style='class:status', align=WindowAlign.CENTER),
                Window(FormattedTextControl(get_statusbar_right_text),
                    style='class:status', width=15, align=WindowAlign.RIGHT),
            ], height=1)



    search_field = SearchToolbar(text_if_not_searching=[
        ('class:not-searching', "Press '/' to start searching.")], ignore_case=True)


    @Condition
    def is_querying():
        return get_app().layout.has_focus(entry_area)


    @Condition
    def is_not_searching():
        return not get_app().layout.has_focus(search_field)


    @Condition
    def is_not_typing():
        return not (get_app().layout.has_focus(search_field) or
                get_app().layout.has_focus(entry_area)
                )

    text_area = TextArea(
        text="",
        read_only=True,
        scrollbar=True,
        search_field=search_field
        )


    def set_text(txt, row=0):
        text_area.text = txt

    msg_buffer = Buffer()

    msg_window = Window(BufferControl(buffer=msg_buffer, focusable=False), height=1, style='class:status')



    ask_buffer = Buffer()

    ask_window = Window(BufferControl(buffer=ask_buffer, focusable=False), height=1, style='class:status')

    query_window = TextArea(
        style='class:status',
        multiline=False,
        focusable=True,
        height=1,
        wrap_lines=False,
        prompt='> ',
        )


    def accept(buf):
        global active_key
        arg = query_window.text
        ret = dispatch[active_key][1](arg)
        if ret and not ret[0]:
            set_text(f"\n {ret[1]} ")
        else:
            if active_key == 'f':
                text = "\n".join(Data.findlines)
            else:
                if Data.showingNodes:
                    text = "\n".join(Data.nodelines)
                else:
                    text = "\n".join(Data.notelines)
            set_text(text)
        show_entry_area = False
        application.layout.focus(text_area)


    query_window.accept_handler = accept

    entry_area = HSplit([
        ask_window,
        query_window,
        ], style='class:entry')


    root_container = HSplit([
        # The top toolbar.
        status_area,
        # The main content.
        text_area,
        #command description and entry
        ConditionalContainer(
            content=entry_area,
            filter=is_querying),
        search_field,
    ])


    def show_find(regex):
        Data.find(regex)
        logger.debug(f"findlines: {Data.findlines}")
        text = "\n".join(Data.findlines)
        set_text(text)
        # logger.debug(f"search: {search.__dict__.keys()}")
        # logger.debug(f"search_field.search_buffer: {search_field.search_buffer.__dict__.keys()}")

        # logger.debug(f"search.get_app: {search.get_app().__dict__.keys()}")
        # search_field.search_buffer._set_text(regex)
        # search_field.search_buffer.accept_handler
        # layout = search.get_app().layout
        # search_control = layout.current_control
        # search_control.buffer._set_text(regex)
        # search.do_incremental_search("FORWARD")
        # logger.debug(f"search.is_searching: {search.is_searching()}")
        # search_state = get_app().current_search_state
        # search_state.text = regex
        # search.start_search()
        # direction = search_state.direction


    def set_max(level):
        Data.setMaxLevel(level)
        Data.getNodes()
        Data.showNodes()


    def set_get(get):
        Data.setGet(get)
        Data.showingNodes = True
        Data.showNodes()


    def set_join(join):
        Data.setJoin(join)
        Data.showingNodes = True
        Data.showNodes()


    def edit_ident(idstr):
        if not idstr:
            return
        orig_mode = Data.mode
        Data.editID(idstr)
        # Data.getNodes()
        Data.setMode(orig_mode)
        Data.showID(idstr)
        Data.getNodes()
        Data.showNodes()


    def add_ident(entry):
        if not entry:
            return
        orig_mode = Data.mode
        tmp, *child = entry.split(" ")
        idstr = tmp.split('-')[0]
        if child:
            child = '_'.join(child)
        ok, res = Data.addID(idstr, child)
        if ok:
            Data.getNodes()
            Data.setMode(orig_mode)
            Data.showID(idstr)
        else:
            return (ok, res)


    def show_ident(ident):
        ok, res = Data.showID(ident)
        if ok:
            Data.getNodes()
            Data.showNodes()
        else:
            return (ok, res)

    # Key bindings.
    bindings = KeyBindings()

    dispatch = {
            'm': [
                'show at most MAX nodes in branches. Use MAX = 0 for all',
                set_max
                ],
            'f': ['show notes matching REGEX',
                show_find
                ],
            'g': [
                'show notes in branches matching REGEX - enter nothing to clear',
                set_get
                ],
            'j': [
                'show notes with tags matching JOIN - enter nothing to clear',
                set_join
                ],
            'i': [
                'inspect the node/leaf corresponding to IDENT - enter 0 to clear',
                show_ident
                ],
            'e': [
                'edit the note corresponding to IDENT',
                edit_ident
                ],
            'a': [
                'add to the node/leaf corresponding to IDENT [NAME]',
                add_ident,
                ]
            }


    def show_help():
        current_version = f"Note Taking Simplified {nts_version}"
        version_indent = " "*((columns - len(current_version))//2)
        note_lines = [f"{version_indent}{current_version}", ""]
        for line in help_notes:
            if line:
                note_lines.extend(textwrap.wrap(line, width=columns-3, subsequent_indent="                ", initial_indent=" "))
            else:
                note_lines.append('')
        txt = "\n".join(note_lines) + "\n"
        set_text(txt)


    def show_limits():
        txt = "\n".join(Data.limits)
        set_text(txt)


    def show_path():
        Data.setMode('path')
        Data.showNodes()
        lines =  Data.nodelines
        set_text("\n".join(lines))



    def show_tags():
        Data.setMode('tags')
        Data.showNodes()
        lines =  Data.nodelines
        set_text("\n".join(lines))


    def toggle_leaves():
        Data.toggleShowLeaves()
        Data.showNodes()
        set_text("\n".join(Data.nodelines))


    def toggle_branches():
        Data.toggleShowBranches()
        Data.showNodes()
        set_text("\n".join(Data.nodelines))


    def show_update_info():
        set_text(check_update())

    execute = {
            'h': show_help,
            'p': show_path,
            't': show_tags,
            'l': toggle_leaves,
            'b': toggle_branches,
            'v': show_update_info,
            'r': show_limits
            }

    # for commands without an argument
    @bindings.add('h', filter=is_not_typing)
    @bindings.add('p', filter=is_not_typing)
    @bindings.add('t', filter=is_not_typing)
    @bindings.add('l', filter=is_not_typing)
    @bindings.add('b', filter=is_not_typing)
    @bindings.add('v', filter=is_not_typing)
    @bindings.add('r', filter=is_not_typing)
    def _(event):
        key = event.key_sequence[0].key
        execute[key]()


    # for commands that need an argument
    @bindings.add('m', filter=is_not_typing)
    @bindings.add('f', filter=is_not_typing)
    @bindings.add('g', filter=is_not_typing)
    @bindings.add('j', filter=is_not_typing)
    @bindings.add('i', filter=is_not_typing)
    @bindings.add('e', filter=is_not_typing)
    @bindings.add('a', filter=is_not_typing)
    def _(event):
        global active_key
        "toggle entry_area"
        key = event.key_sequence[0].key
        active_key = key
        instruction, command = dispatch.get(key, (None, None))
        if instruction:
            ask_buffer.text = instruction
            application.layout.focus(entry_area)
        else:
            set_text(f"'{key}' is an unrecognized command")


    @bindings.add('q', filter=is_not_typing)
    @bindings.add('f8')
    def _(event):
        " Quit. "
        event.app.exit()

    @bindings.add(',', ',', filter=is_not_typing)
    def _(event):
        search_state = get_app().current_search_state
        search_state.text = ''

    @bindings.add('.', '.', filter=is_not_typing)
    def _(event):
        search_state = get_app().current_search_state
        text = search_state.text
        if not text:
            return
        Data.find(text)
        set_text("\n".join(Data.findlines))

    # start with path view
    show_path()

    # create application.
    application = Application(
        layout=Layout(
            root_container,
            focused_element=text_area,
        ),
        key_bindings=bindings,
        enable_page_navigation_bindings=True,
        mouse_support=True,
        style=style_obj,
        full_screen=True)


    application.run()


def main():
    columns, rows = shutil.get_terminal_size()
    parser = argparse.ArgumentParser(
            description=f"Note Taking Simplified {nts_version}",
            # formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog='nts')

    parser.add_argument("-s",  "--session", help="begin an interactive session", action="store_true")

    parser.add_argument("-l",  "--leaves", help="hide leaves",
                        action="store_true")

    parser.add_argument("-b",  "--branches", help="hide branches",
                        action="store_true")


    parser.add_argument("-p", "--path",
                    help="view path", action="store_true")

    parser.add_argument("-t", "--tags",
                    help="view tags", action="store_true")


    parser.add_argument("-m", "--max", type=int, help="display at most MAX levels of outlines. Use MAX = 0 to show all levels.")

    parser.add_argument("-f", "--find", type=str, help='show notes in the current view whose content contains a match for the case-insensitive regex FIND. Mark matching lines with an "-" in the rightmost column unless FIND is preceeded by an "!".')

    parser.add_argument("-g", "--get", type=str, help="show note titles whose branches in the active view contain a match for the case-insensitive regex GET")

    parser.add_argument("-j", "--join", type=str, help='display note titles for notes with tags satisfying JOIN. E.g. if JOIN = "red", then notes containing the tag "RED" would be displayed. If JOIN = "| red, blue" then notes with either the tag "red" or the tag "blue" would be displayed. Finally, if JOIN = "& red, blue", then notes with both the tags "red" and "blue" would be displayed. In general JOIN = [|&] comma-separated list of case-insensitive regular expressions.')

    parser.add_argument("-i", "--id", type=str, help="inspect the node/leaf corresponding to ID in the active view")

    parser.add_argument("-e", "--edit", type=str, help="edit the node/leaf corresponding to EDIT in the active view")

    parser.add_argument("-a", "--add", type=str, help="add to the node/leaf corresponding to ADD in the active view")

    parser.add_argument("-v",  "--version", help="check for an update to a later nts version",
                        action="store_true")


    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    mode = 'tags' if args.tags else 'path'
    Data.setMode(mode)
    Data.showNodes()

    if args.session:
        Data.sessionMode = True
        Data.showID()
        session()

    else:

        showing_details = args.find or args.add or args.edit or args.id

        if args.id:
            ok, res = Data.showID(args.id)
            if not ok:
                print(res)

        if args.find:
            Data.showNodes()
            Data.find(args.find)
            if not (args.add or args.edit or args.id):
                for line in Data.findlines:
                    print(line)
                print("_"*columns)
                return

        if args.get:
            Data.setGet(args.get)
            # print(Data.getstr)
            # print("-"*len(Data.getstr))
            Data.showNodes()

        if args.join:
            Data.setJoin(args.join)
            Data.showNodes()

        if args.version:
            res = check_update()
            print(res)
            return

        if args.max:
            Data.setMaxLevel(args.max)

        if args.leaves:
            Data.toggleShowLeaves()

        if args.branches:
            Data.toggleShowBranches()

        if args.path:
            Data.setMode('path')
            Data.showNodes()
            if not showing_details:
                # print('path view')
                for line in Data.nodelines:
                    print(line)
                print('')

        if args.tags:
            Data.setMode('tags')
            Data.showNodes()
            if not showing_details:
                # print('tags view')
                for line in Data.nodelines:
                    print(line)
                print('')

        if args.add:
            tmp, *child = args.add.split(" ")
            idstr = tmp.split('-')[0]
            if child:
                child = '_'.join(child)
            Data.addID(idstr, child)

        if args.edit:
            ok, res = Data.editID(args.edit)
            if not ok:
                print(res)



if __name__ == "__main__":
    MIN_PYTHON = (3, 7, 3)
    if sys.version_info < MIN_PYTHON:
        mv = ".".join([str(x) for x in MIN_PYTHON])
        sys.exit(f"Python {mv} or later is required.\n")

    columns, rows = shutil.get_terminal_size()
    rootdir = os.path.join(os.path.expanduser('~'), 'nts', 'data')
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logger = logging.getLogger()
    ntsdir = os.path.join(os.path.expanduser('~'), 'nts')
    logdir = os.path.normpath(os.path.join(ntsdir, 'logs'))
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    loglevel = 2 # info
    setup_logging(loglevel, logdir)
    # print(f"rootdir: {rootdir}, python version: {sys.version_info}")

    Data = NodeData(rootdir, logger)

    main()



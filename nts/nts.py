import os, fnmatch
import sys
from pprint import pprint
from anytree import Node, RenderTree, search
from base64 import b64encode, b64decode
import base64
import re
from prompt_toolkit import prompt
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
from prompt_toolkit.layout.containers import HSplit, Window, ConditionalContainer

import subprocess
import requests

from prompt_toolkit import print_formatted_text
# from prompt_toolkit.styles.named_colors import NAMED_COLORS
import textwrap

import shutil
import logging
import logging.config

import argparse

import nts.__version__ as version
nts_version = version.version

note_regex = re.compile(r'^[\+#]\s+([^\(]+)\s*(\(([^\)]*)\))?\s*$')

separator = os.path.sep

help_table = f"""\
             nts: Note Taking Simplified version {nts_version}

        Action          | Command Mode | Session Mode | Notes
        ----------------|--------------|--------------|------
        help            |  -h          |  h           |  ~
        begin session   |  -s          |  ~           |  ~
        end session     |   ~          |  q           |  ~
        path view       |  -p          |  p           |  ~
        tags view       |  -t          |  t           |  ~
        hide leaves     |  -l          |  l           |  l
        hide branches   |  -b          |  b           |  b
        set max levels  |  -m MAX      |  m MAX       |  m
        search          |              |  / REGEX     |  /
        find REGEX      |  -f REGEX    |  f REGEX     |  f
        get REGEX       |  -g REGEX    |  g REGEX     |  g
        inspect IDENT   |  -i IDENT    |  i IDENT     |  i
        edit IDENT      |  -e IDENT    |  e IDENT     |  e
        add to IDENT    |  -a IDENT    |  a IDENT     |  a
        version check   |  -v          |  v           |  v

"""

help_notes = [
'l. Suppress showing leaves in the outline. In session mode toggle the display of leaves off and on.',
'b. Suppress showing branches in the outline, i.e., display only the leaves. In session mode toggle the display of the branches off and on.',
'm. Limit the diplay of nodes in the branches to the integer MAX levels. Use MAX = 0 to display all levels.',
'/. Incrementally search for matches for the case-insensitive regular expression REGEX in the current display.',
'f. Display complete notes that contain a match in the title, tags or body for the case-insensitive regular expression REGEX.',
'g. Display note titles that contain a match in the branch nodes leading to the note for the case-insensitive regular expression REGEX.',
'i. If IDENT is the 2-number identifier for a note, then display the contents of that note. Else if IDENT is the identifier for a ".txt" file, then display the contents of that file. Otherwise limit the display to that part of the outline which starts from the corresponding node. Use IDENT = 0 to start from the root node.',
'e. If IDENT corresponds to either a note or a ".txt" file, then open that file for editing and, in the case of a note, scroll to the beginning line of the note.',
'a. If IDENT corresponds to either a note or a ".txt" file, then open that file for appending a new note. Otherwise, if IDENT corresponds to a directory, then prompt for the name of a child to add to that node. If the name entered ends with ".txt", a new note file will be created and opened for editing. Otherwise, a new subdirectory will be added to the node directory using the name provided. Use "0" as the IDENT to add to the root (data) node.',
'v. Compare the installed version of nts with the latest version on GitHub (requires internet connection) and report the result.',
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
        self.get = None
        self.getstr = ''

        self.setStart()
        self.setMaxLevel(0)
        self.getNodes()

        self.mode = 'path'
        self.showingNodes = True

    def setRestrictions(self):
        # startmsg = "" if self.start == '.' else f'showing branches starting from "{self.start}" - press "i" and enter 0 to show all branches'
        # getmsg = f'showing notes in branches matching "{self.getstr}" - press "g" and enter nothing to clear' if self.getstr else ""
        # maxmsg = "" if self.maxlevel in [None, 0] else f'displaying at most {self.maxlevel} levels - press "m" and enter 0 to show all levels'
        # leafmsg = "" if self.shownotes else 'hiding leaves - press "l" to display them'
        # branchmsg = "" if self.shownodes else 'hiding branches - press "b" to display them'
        # msglist = []
        msg = []
        if self.start != '.':
            msg.append('i')
        if self.getstr:
            msg.append('g')
        if self.maxlevel not in [None, 0]:
            msg.append('m')
        if not self.shownotes:
            msg.append('l')
        if not self.shownodes:
            msg.append('b')

        # for msg in [startmsg, getmsg, maxmsg, leafmsg, branchmsg]:
        #     if msg:
        #         msglist.append(msg)
        self.restrictions = msg
        logger.debug(f"restrictions: '{self.restrictions}'")


    def setGet(self, get=None):
        get = get.strip()
        logger.debug(f"getstr: {get}")
        self.getstr = get if get else ''
        self.get = re.compile(r'%s' % get, re.IGNORECASE) if self.getstr else None
        self.showNodes()

    def setMaxLevel(self, maxlevel=0):
        self.maxlevel = None if maxlevel == 0 else maxlevel
        try:
            self.maxlevel = int(self.maxlevel)
        except Exception as e:
            logger.debug(f"exception: {e}")
            self.maxlevel = None
        logger.debug(f"set maxlevel: {self.maxlevel}")


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
        logger.debug(f"start: {start}")
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
                notelines = []
                for x in notes:
                    #  x: [title, [tags], linenum, [body]]
                    titlestr = f"+ {x[0]}"
                    tagstr = f" ({', '.join(x[1])})" if x[1] else ""
                    tmp = [f"{titlestr}{tagstr}"]
                    tmp.extend(x[3])
                    self.notedetails[(filepath, x[2])] = tmp
                    notelines.append([titlestr, tagstr,  (filepath, x[2])])
                    for tag in x[1]:
                        taghash.setdefault(tag, []).append([titlestr, tagstr, (filepath, x[2])])
                self.pathnodes[f"{key}{separator}{file}{separator}notes"] = Node('notes', self.pathnodes[f"{key}{separator}{file}"], lines=notelines)


        self.tagnodes['.'] = Node('.')
        for key, values in taghash.items():
            self.tagnodes[f".{separator}{key}"] = Node(key, self.tagnodes['.'])
            self.tagnodes[f".{separator}{key}{separator}notes"] = Node('notes',
                    self.tagnodes[f".{separator}{key}"], lines=[x for x in values])


    def showNodes(self):
        self.columns, self.rows = shutil.get_terminal_size()
        column_adjust = 3 if self.sessionMode else 1
        getnodes = self.get
        self.setRestrictions()
        id = 0
        id2info = {}
        linenum = 0
        linenum2node = {}
        output_lines = []
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
            if getnodes:
                pre = fill = ""
                if not getnodes.search(pathstr):
                    continue
            if node.name.endswith('.txt'):
                pathstr = os.path.join(self.rootdir, pathstr[2:])

            if self.shownotes:
                notenum = 0
                if hasattr(node, 'lines') and node.lines:
                    for line in node.lines:
                        # titlestr, tagstring,  (filepath, linenum)
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

                    if id > 0 and self.shownodes and not getnodes:
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
        output_lines = []
        with open(filepath, 'r') as fo:
            lines = fo.readlines()
        if linenum is None:
            for line in lines:
                line = line.rstrip()
                if line:
                    output_lines.extend(textwrap.wrap(line, width=self.columns-4, subsequent_indent="  ", initial_indent="  "))
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
                    output_lines.extend(textwrap.wrap(line, width=self.columns-4, subsequent_indent="  ", initial_indent="  "))
                else:
                    output_lines.append("")

        self.notelines = output_lines

    def tags(self, tag=None):
        if tag:
            regex = re.compile(r'%s' % tag, re.IGNORECASE)


    def find(self, find=None):
        matching_keys = []
        output_lines = []
        self.find_lines = []
        if not find:
            return output_lines
        regex = re.compile(r'%s' % find, re.IGNORECASE)
        logger.debug(f"find: {regex}")
        for key, lines in self.notedetails.items():
            match = False
            for line in lines:
                match = regex.search(line)
                if match:
                    break
            if match:
                matching_keys.append(key)
        if matching_keys:
            self.columns, rows = shutil.get_terminal_size()
            for identifier, key in self.id2info.items():
                if key in matching_keys:
                    lines = self.notedetails.get(key, [])
                    idstr = "-".join([str(x) for x in identifier])
                    # output_lines.append(f"IDENT: {idstr}\n{lines[0]} {idstr}")
                    output_lines.append(f"{lines[0]} {idstr}")
                    for line in lines[1:]:
                        line.rstrip()
                        if line:
                            output_lines.extend(textwrap.wrap(line, width=self.columns-4,
                                subsequent_indent="  ", initial_indent="  "))
                        else:
                            output_lines.append('')
                    output_lines.append('')
            if output_lines and not output_lines[-1]:
                output_lines = output_lines[:-1]
        self.findlines = output_lines
        logger.debug(f"findlines: {self.findlines}")

    def showID(self, idstr="0"):
        self.showNodes()
        if idstr == "0":
            info = ('.', )
        else:
            try:
                idtup = tuple([int(x) for x in idstr.split('-')])
            except:
                return([False, f"Bad IDENT {idstr}"])
            if idtup in self.id2info:
                info = self.id2info[idtup]
            else:
                return([False, f"Bad IDENT {idstr}"])

        # info: (key, line)
        if info[0] in self.nodes:
            # we have a starting node
            self.showingNodes = True
            self.setStart(info[0])
            self.showNodes()
            if not self.sessionMode:
                for line in self.nodelines:
                    print(line)
            return [True, "printed nodelines"]
        elif os.path.isfile(info[0]):
            # we have a filename and linenumber
            self.showingNodes = False
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
            return
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
        return


    def addID(self, idstr, text=None):
        idtup = tuple([int(x) for x in idstr.split('-')])
        info = self.id2info.get(idtup, ('.', ))
        info = list(info)
        retval = ""

        if info[0] in self.nodes:
            # we have a starting node
            if not self.mode == 'path':
                # only works for nodes in path mode
                return "cancelled: must be in path mode"
            path = os.path.join(self.rootdir, info[0][2:])
            if not os.path.isdir(path):
                return f"error: bad path {path}"
            if not text:
                text = prompt(
                        f"directory or filename (ending in '.txt') to add as a child of\n {path}\n> ")
                text = text.strip()
                if not text:
                    return "cancelled"
            child = os.path.join(path, f"{text}")
            root, ext = os.path.splitext(child)
            if ext:
                # adding a new note file
                if ext != ".txt":
                    return f"bad file extension {ext}; '.txt' is required"
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
                    return f"'child' already exists"
                os.mkdir(child)
                return f"created '{child}'"


            return  "adding root {root} with extension {ext}"

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
            print(f"error: bad index {info}")
            pprint(self.nodes.keys())
        return

def session():
    columns, rows = shutil.get_terminal_size()
    Data.sessionMode = True

    active_key = 'start'

    def get_statusbar_text():
        lst = [
            ('class:status', ' nts'),
            ('class:status', f' {Data.mode} view'),
            ('class:status', ' - Press '),
            ('class:status.key', 'h'),
            ('class:status', ' for help'),
        ]
        if Data.restrictions:
            lst.append(('class:status', ' - restrictions in effect: '))
            for key in Data.restrictions[:-1]:
                lst.extend([
                    ('class:status.key', f'{key}'),
                    ('class:status', ', '),
                    ]
                    )
            lst.append(('class:status.key', f'{Data.restrictions[-1]}'))
        return lst


    # def get_message_text():
    #     return Data.restrictions

    search_field = SearchToolbar(text_if_not_searching=[
        ('class:not-searching', "Press '/' to start searching.")], ignore_case=True)


    @Condition
    def is_querying():
        return get_app().layout.has_focus(entry_area)

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
        logger.debug(f"key: {active_key}; arg: {arg} dispatch: {dispatch[active_key][1]}")
        dispatch[active_key][1](arg)
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
        Window(
            content=FormattedTextControl(
            get_statusbar_text),
            height=D.exact(1),
            style='class:status'),

        # The main content.
        text_area,
        ConditionalContainer(
            content=entry_area,
            filter=is_querying),
        search_field,
    ])


    def show_find(regex):
        Data.find(regex)
        set_text("\n".join(Data.findlines))

    def set_max(level):
        Data.setMaxLevel(level)
        Data.getNodes()
        Data.showNodes()

    def edit_ident(idstr):
        if not idstr:
            return
        orig_mode = Data.mode
        Data.editID(idstr)
        Data.getNodes()
        Data.setMode(orig_mode)
        Data.showID(idstr)

    def add_ident(entry):
        if not entry:
            return
        orig_mode = Data.mode
        tmp, *child = entry.split(" ")
        idstr = tmp.split('-')[0]
        if child:
            child = '_'.join(child)
        Data.addID(idstr, child)
        Data.getNodes()
        Data.setMode(orig_mode)
        Data.showID(idstr)


    def show_ident(ident):
        Data.showID(ident)
        Data.getNodes()
        Data.showNodes()

    # Key bindings.
    bindings = KeyBindings()

    dispatch = {
            'm': [
                'show at most MAX nodes in branches. Use MAX = 0 for all',
                set_max
                ],
            'f': ['show notes matching REGEX',
                Data.find
                ],
            'g': [
                'show notes in branches matching REGEX - enter nothing to clear',
                Data.setGet
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
                'add to the node/leaf corresponding to IDENT',
                add_ident,
                ]
            }

    def show_help():
        note_lines = []
        for line in help_notes:
            note_lines.extend(textwrap.wrap(line, width=columns-3, subsequent_indent="    ", initial_indent=" "))
        txt = help_table + "\n".join(note_lines)
        set_text(txt)

    def show_restrictions():
        txt = "\n".join(Data.restrictions)
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
            'r': show_restrictions
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
    @bindings.add('i', filter=is_not_typing)
    @bindings.add('e', filter=is_not_typing)
    @bindings.add('a', filter=is_not_typing)
    def _(event):
        global active_key
        "toggle entry_area"
        # show_entry_area = True
        # set_text("\n".join([x for x in event.__dict__.keys()]))
        # set_text(f"{TextArea.__dict__.keys()}")
        # set_text(f"{event.key_sequence[0].key}")
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

    style = Style.from_dict({
        'status': f'{NAMED_COLORS["White"]} bg:{NAMED_COLORS["DimGrey"]}',
        'message': '#fff86f',
        'status.position': '#aaaa00',
        'status.key': '#ffaa00',
        'not-searching': '#888888',
    })


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
        style=style,
        full_screen=True)


    application.run()


def main():
    columns, rows = shutil.get_terminal_size()
    parser = argparse.ArgumentParser(description=f"nts: Note Taking Simplified version {nts_version}")

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

    parser.add_argument("-f", "--find", type=str, help="show notes whose content contains a match for the case-insensitive regex FIND")

    parser.add_argument("-g", "--get", type=str, help="show note titles whose branches contain a match for the case-insensitive regex GET")

    parser.add_argument("-i", "--id", type=str, help="inspect the node/leaf corresponding to ID")

    parser.add_argument("-e", "--edit", type=str, help="edit the node/leaf corresponding to EDIT")

    parser.add_argument("-a", "--add", type=str, help="add to the node/leaf corresponding to ADD")

    parser.add_argument("-v",  "--version", help="check for an update to a later nts version",
                        action="store_true")


    args = parser.parse_args()
    mode = 'path' if args.path else 'tags'
    Data.setMode(mode)

    if args.session:
        Data.sessionMode = True
        Data.showID()
        session()

    else:

        if args.find:
            Data.showNodes()
            Data.find(args.find)
            for line in Data.findlines:
                print(line)
            print("_"*columns)
            return

        if args.get:
            Data.setGet(args.get)
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
            print('path view')
            Data.setMode('path')
            Data.showNodes()
            for line in Data.nodelines:
                print(line)
            print('')

        if args.tags:
            print('tags view')
            Data.setMode('tags')
            Data.showNodes()
            for line in Data.nodelines:
                print(line)
            print('')

        if args.add:
            logger.debug(f"args.add: {args.add}")
            Data.addID(args.add)

        if args.edit:
            logger.debug(f"args.edit: {args.edit}")
            Data.editID(args.edit)

        elif args.id:
            Data.showID(args.id)


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



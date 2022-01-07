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

help = f"""\
       nts: Note Taking Simplified version {nts_version}

Command Summary
    Action          | Command Mode | Session Mode | Notes
    ----------------|--------------|--------------|------
    help            |  -h          |  h           |   ~
    begin session   |  -s          |  ~           |   ~
    end session     |   ~          |  q           |   ~
    path view       |  -p          |  p           |   ~
    tags view       |  -t          |  t           |   ~
    hide leaves     |  -l          |  l           |   1
    hide branches   |  -b          |  b           |   2
    set max levels  |  -m MAX      |  m MAX       |   3
    highlight REGEX |              |  / REGEX     |   4
    find REGEX      |  -f REGEX    |  f REGEX     |   5
    get REGEX       |  -g REGEX    |  g REGEX     |   6
    inspect IDENT   |  -i IDENT    |  i IDENT     |   7
    revert          |   ~          |  r           |   8
    edit IDENT      |  -e IDENT    |  e IDENT     |   9
    add to IDENT    |  -a IDENT    |  a IDENT     |  10
    update check    |  -u          |  u           |  11


1. Suppress showing leaves in the outline. In session mode
this toggles the display of leaves off and on.

2. Suppress showing branches in the outline, i.e., display
only the leaves. In session mode this toggles the display
of the branches off and on.

3. Limit the diplay of nodes in the branches to the integer
MAX levels. Use MAX = 0 to display all levels.

4. Highlight displayed lines that contain a match for the
case-insensitive regular expression REGEX. Enter an empty
REGEX to clear highlighting.

5. Display complete notes that contain a match in the
title, tags or body for the case-insensitive regular
expression REGEX.

6. If IDENT is the 2-number identifier for a note, then
display the contents of that note. Else if IDENT is the
identifier for a ".txt" file, then display the contents of
that file. Otherwise limit the display to that part of the
outline which starts from the corresponding node. Use
IDENT = 0 to start from the root node.

7. In session mode, switch back and forth between the two
most recent displays.

8. If IDENT corresponds to either a note or a ".txt" file,
then open that file for editing and, in the case of a
note, scroll to the beginning line of the note.

9. If IDENT corresponds to either a note or a ".txt" file,
then open that file for appending a new note. Otherwise,
if IDENT corresponds to a directory, then prompt for the
name of a child to add to that node. If the name entered
ends with ".txt", a new note file will be created and
opened for editing. Otherwise, a new subdirectory will be
added to the node directory using the name provided. Use
"0" as the IDENT to add to the root (data) node.

10. Compare the installed version of nts with the latest
version on GitHub (requires internet connection) and
report the result.\
"""


helplines = help.split("\n")


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


class ListView(object):

    def __init__(self, lines=[], style_class='class:plain'):
        self.columns, rows = shutil.get_terminal_size()
        self.rows = rows - 4 # integer number of allowed display rows
        self.find = None
        self.regx = None
        self.lines = lines
        self.style_class = style_class
        self.pages = {}
        self.page_numbers = []
        self.current_page = None
        self.set_pages(lines)


    def set_find(self, find):
        if find:
            self.find = find
            self.regx = re.compile(r'%s' % find , re.IGNORECASE)
        else:
            self.find = None
            self.regx = None
        self.set_lines(self.lines)


    def set_lines(self, lines):
        """
        Format the lines according to whether or not they match the find regex
        """
        self.lines = []
        if self.regx:
            for line in lines:
                if isinstance(line, (tuple, list)):
                    text = line[1].rstrip()
                else:
                    text = line.rstrip()
                if self.regx.search(text):
                    line = ('class:highlight', f"{text} \n")
                elif text.startswith('IDENT:'):
                    line = ('class:prompt', f"{text} \n")
                else:
                    line = (self.style_class, f"{text} \n")
                self.lines.append(line)
        else:
            for line in lines:
                if isinstance(line, (tuple, list)):
                    text = line[1].rstrip()
                else:
                    text = line.rstrip()
                if text.startswith('IDENT:'):
                    line = ('class:prompt', f"{text} \n")
                else:
                    line = (self.style_class, f"{text} \n")
                self.lines.append(line)


    def set_pages(self, lines):
        """
        Break lines into pages satisfying the available number of rows
        """
        self.set_lines(lines)
        self.pages = {}
        page_num = 0
        while True:
            page_num += 1
            beg_line = (page_num - 1) * (self.rows )
            page_lines = self.lines[beg_line:beg_line + self.rows]
            if page_lines:
                self.pages[str(page_num)] = page_lines
            else:
                break

        self.page_numbers = [x for x in self.pages.keys()]
        self.num_pages = len(self.page_numbers)
        self.current_page = 0 # current page number = self.page_numbers[0] = 1

    def get_page_footer(self):
        if self.num_pages < 2:
            return [('class:prompt', f"{self.columns*'_'}")]
        page_num = self.page_numbers[self.current_page]
        prompt = "Use up and down cursor keys to change pages"
        return [('class:prompt', f"{self.columns*'_'}\n"),
                ('class:prompt', f"Page {page_num}/{self.num_pages}. {prompt}.")]

    def show_page(self):
        if not self.page_numbers:
            return
        page_num = self.page_numbers[self.current_page]
        lines = [x for x in self.pages[page_num]]
        page_footer = self.get_page_footer()
        if page_footer:
            lines.extend(page_footer)
        myprint(lines)

    def set_page(self, page_index):
        self.current_page = page_index


    def scroll_up(self):
        if self.current_page > 0:
            self.current_page -= 1
            shortcuts.clear()
            self.show_page()

    def scroll_down(self):
        if self.current_page < self.num_pages - 1:
            self.current_page += 1
            shortcuts.clear()
            self.show_page()


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
        # self.pathfind = None
        # self.tagsfind = None
        self.get = None

        self.setStart()
        self.setMaxLevel(None)
        self.getNodes()
        # for key, value in self.pathnodes.items():
        #     print(f"{key}:", value)
        # for key, value in self.tagnodes.items():
        #     print(f"{key}:", value)

        self.mode = 'path'
        self.showingNodes = True

    def setGet(self, get=None):
        logger.debug(f"setGet: {get}")
        self.get = re.compile(r'%s' % get.strip(), re.IGNORECASE) if get else None
        self.showNodes()

    def setMaxLevel(self, maxlevel=0):
        try:
            self.maxlevel = int(maxlevel)
        except:
            self.maxlevel = 0


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
        logger.debug(f"1. getnodes: {getnodes}")
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
        # print(f"matching_keys: {matching_keys}")
        # print(self.id2info.keys())
        if matching_keys:
            self.columns, rows = shutil.get_terminal_size()
            for identifier, key in self.id2info.items():
                # print(f"checking identifier: {identifier}; keys: {keys}")
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
        # return


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

def session_app():
    columns, rows = shutil.get_terminal_size()
    Data.sessionMode = True

    active_key = 'start'

    def get_statusbar_text():
        return [
            ('class:status', pendulum.now().format(" h:mmA ddd MMM D") + ": "),
            ('class:status', '{}'.format(
                text_area.document.cursor_position_row + 1)),
            ('class:status', ' - Press '),
            ('class:status.key', 'q'),
            ('class:status', ' to exit, '),
            ('class:status.key', '/'),
            ('class:status', ' to search'),
        ]


    search_field = SearchToolbar(text_if_not_searching=[
        ('class:not-searching', "Press '/' to start searching.")], ignore_case=True)

    @Condition
    def is_querying():
        return get_app().layout.has_focus(query_area)

    @Condition
    def is_not_typing():
        return not (get_app().layout.has_focus(search_field) or
                get_app().layout.has_focus(query_area)
                )
    text_area = TextArea(
        text="",
        read_only=True,
        scrollbar=True,
        search_field=search_field
        )

    def set_text(txt, row=0):
        text_area.text = txt

    # for testing
    Data.setMode('path')
    Data.showNodes()
    text = "\n".join(Data.nodelines)

    set_text(text)

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
        show_query_area = False
        application.layout.focus(text_area)


    query_window.accept_handler = accept

    query_area = HSplit([
        ask_window,
        query_window,
        ], style='class:entry')


    root_container = HSplit([
        # The top toolbar.
        # Window(
        #     content=FormattedTextControl(
        #     get_statusbar_text),
        #     height=D.exact(1),
        #     style='class:status'),

        # The main content.
        text_area,
        ConditionalContainer(
            content=query_area,
            filter=is_querying),
        search_field,
    ])


    def show_find(regex):
        Data.find(regex)
        set_text("\n".join(Data.findlines))


    # Key bindings.
    bindings = KeyBindings()

    dispatch = {
            'm': [
                'show at most MAX nodes in branches. Use MAX = 0 for all',
                Data.setMaxLevel
                ],
            'f': ['show notes matching REGEX',
                Data.find
                ],
            'g': [
                'show branches matching REGEX',
                Data.setGet
                ],
            'i': [
                'inspect the node/leaf corresponding to IDENT',
                Data.showID
                ],
            'e': [
                'edit the note corresponding to IDENT',
                None
                ],
            'a': [
                'add to the node/leaf corresponding to IDENT',
                None,
                ]
            }

    def show_help():
        set_text(help)

    def show_path():
        Data.setMode('path')
        Data.showNodes()
        set_text("\n".join(Data.nodelines))


    def show_tags():
        Data.setMode('tags')
        Data.showNodes()
        set_text("\n".join(Data.nodelines))

    def toggle_leaves():
        Data.toggleShowLeaves()
        Data.showNodes()
        set_text("\n".join(Data.nodelines))

    def toggle_branches():
        Data.toggleShowBranches()
        Data.showNodes()
        set_text("\n".join(Data.nodelines))

    def show_update_info():
        set_text(check_update)

    execute = {
            'h': show_help,
            'p': show_path,
            't': show_tags,
            'l': toggle_leaves,
            'b': toggle_branches,
            'v': show_update_info,
            }

    # for commands without an argument
    @bindings.add('h', filter=is_not_typing)
    @bindings.add('p', filter=is_not_typing)
    @bindings.add('t', filter=is_not_typing)
    @bindings.add('l', filter=is_not_typing)
    @bindings.add('b', filter=is_not_typing)
    @bindings.add('v', filter=is_not_typing)
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
        "toggle query_area"
        # show_query_area = True
        # set_text("\n".join([x for x in event.__dict__.keys()]))
        # set_text(f"{TextArea.__dict__.keys()}")
        # set_text(f"{event.key_sequence[0].key}")
        key = event.key_sequence[0].key
        active_key = key
        instruction, command = dispatch.get(key, (None, None))
        if instruction:
            ask_buffer.text = instruction
            application.layout.focus(query_area)
        else:
            set_text(f"'{key}' is an unrecognized command")



    @bindings.add('q')
    @bindings.add('f8')
    def _(event):
        " Quit. "
        event.app.exit()

    style = Style.from_dict({
        'status': '{} bg:{}'.format(NAMED_COLORS['White'], NAMED_COLORS['DimGrey']),
        'status.position': '#aaaa00',
        'status.key': '#ffaa00',
        'not-searching': '#888888',
    })


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



def session():
    columns, rows = shutil.get_terminal_size()
    Data.sessionMode = True
    bindings = KeyBindings()
    session = PromptSession(key_bindings=bindings)
    path_list_view = ListView()
    path_list_index = 0
    tags_list_view = ListView()
    tags_list_index = 0
    help_view = ListView(helplines, 'class:message')
    leaf_view = ListView()
    leaf_index = 0
    find_view = ListView()
    find_index = 0
    current_view = ''
    previous_view = ''
    logger.debug("Opened session")

    def prompt_continuation(width, line_number, is_soft_wrap):
        return f"{'.'*(width-1)} "

    @Condition
    def entry_not_active():
        return not myValidator.entryactive

    @Condition
    def is_showing_path():
        return current_view == 'path_list'

    @Condition
    def is_showing_tags():
        return current_view == 'tags_list'

    @Condition
    def is_showing_help():
        return current_view == 'help'

    @Condition
    def is_showing_leaf():
        return current_view == 'leaf'

    @Condition
    def is_showing_find():
        return current_view == 'find'

    @bindings.add('down', filter=is_showing_leaf)
    def _(event):
        def down():
            leaf_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('up', filter=is_showing_leaf)
    def _(event):
        def up():
            leaf_view.scroll_up()
        run_in_terminal(up)

    @bindings.add('down', filter=is_showing_path)
    def _(event):
        def down():
            path_list_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('up', filter=is_showing_path)
    def _(event):
        def up():
            path_list_view.scroll_up()
        run_in_terminal(up)

    @bindings.add('down', filter=is_showing_tags)
    def _(event):
        def down():
            tags_list_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('up', filter=is_showing_tags)
    def _(event):
        def up():
            tags_list_view.scroll_up()
        run_in_terminal(up)

    @bindings.add('down', filter=is_showing_help)
    def _(event):
        def down():
            help_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('up', filter=is_showing_help)
    def _(event):
        def up():
            help_view.scroll_up()
        run_in_terminal(up)

    @bindings.add('down', filter=is_showing_find)
    def _(event):
        def down():
            find_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('up', filter=is_showing_find)
    def _(event):
        def up():
            find_view.scroll_up()
        run_in_terminal(up)

    shortcuts.clear()
    message = [("class:prompt", 'Enter ? or other command and press "return"')]
    regx = ""
    myprint(message)

    run = True
    while run:
        message_parts = []
        highlight = f'highlighting "{regx.strip()}" - enter "/" to clear highlighting' if regx else ""
        if highlight:
            message_parts.append(highlight)
        if Data.shownodes:
            hidden = "" if Data.shownotes else 'notes hidden - enter "n" to display them'
        else:
            hidden = 'nodes hidden - enter "N" to display them'
        if hidden:
            message_parts.append(hidden)
        level = f'limiting levels to {Data.maxlevel} - enter "m 0" to display all levels' if  Data.maxlevel else ""
        if level:
            message_parts.append(level)
        if message_parts:
            message_str = "; ".join(message_parts) + " "
        else:
            message_str = ""

        if message_str:
            msg_lines = textwrap.wrap(message_str, width=columns-2)
            message_str = "\n".join(msg_lines)

        message =  [("class:prompt", f"{message_str}\n> ")] if message_str else [("class:prompt", f"> ")]

        text = session.prompt(message, style=style_obj,
                prompt_continuation=prompt_continuation)
        text = text.strip()

        if text == 'q':
            shortcuts.clear()
            break

        elif text in ['?', 'h']:
            if current_view != 'help':
                previous_view = current_view
                current_view = 'help'
            shortcuts.clear()
            help_view.show_page()

        elif text == 'p':
            if current_view != 'path_list':
                previous_view = current_view
                current_view = 'path_list'
            shortcuts.clear()
            Data.setMode('path')
            ok, msg = Data.showID()
            if ok:
                lines = Data.nodelines if Data.showingNodes else Data.notelines
                path_list_view.set_pages(lines)
                path_list_view.show_page()
            else:
                myprint(msg)

        elif text == 't':
            shortcuts.clear()
            if current_view != 'tags_list':
                previous_view = current_view
                current_view = 'tags_list'
            Data.setMode('tags')
            ok, msg = Data.showID()
            if ok:
                lines = Data.nodelines if Data.showingNodes else Data.notelines
                tags_list_view.set_pages(lines)
                tags_list_view.show_page()
            else:
                myprint(msg)

        elif text.startswith('m'):
            # if current_view not in ['path_list_view', 'tags_list_view']:
            #     return
            msg = ""
            level = text[1:] if len(text) > 1 else 0
            try:
                level = int(level.strip())
            except:
                level = None
            if level is not None:
                Data.setMaxLevel(level)
                ok, msg = Data.showID()
                lines = Data.nodelines if Data.showingNodes else Data.notelines
                if current_view == 'path_list':
                    path_list_view.set_pages(lines)
                    path_list_view.show_page()
                elif current_view == 'tags_list':
                    tags_list_view.set_pages(lines)
                    tags_list_view.show_page()
            else:
                show_message("an integer LEVEL argument was either missing or invalid")

        elif text == 'r':
            logger.debug(f"current_view: {current_view}; previous_view: {previous_view}")
            shortcuts.clear()
            if previous_view and current_view:
                tmp = previous_view
                previous_view = current_view
                current_view = tmp
                if current_view == 'help':
                    help_view.show_page()
                elif current_view == 'find':
                    find_view.show_page()
                elif current_view == 'leaf':
                    leaf_view.show_page()
                elif current_view == 'path_list':
                    path_list_view.show_page()
                elif current_view == 'tags_list':
                    tags_list_view.show_page()


        elif text.startswith('/'):
            shortcuts.clear()
            arg = text[1:]
            regx = arg if arg else None
            path_list_view.set_find(regx)
            tags_list_view.set_find(regx)
            leaf_view.set_find(regx)
            if Data.showingNodes:
                lines = Data.nodelines
                if current_view == 'path_list':
                    path_list_view.set_pages(lines)
                    path_list_view.set_page(path_list_index)
                    path_list_view.show_page()
                elif current_view == 'tags_list':
                    tags_list_view.set_pages(lines)
                    tags_list_view.set_page(tags_list_index)
                    tags_list_view.show_page()
            else:
                lines = Data.notelines
                leaf_view.set_pages(lines)
                leaf_view.set_page(leaf_index)
                leaf_view.show_page()


        elif text.startswith('g'):
            find = text[1:].strip()
            getnodes = find if find else None
            logger.debug(f"2. getnodes: {getnodes}")
            Data.setGet(getnodes)
            Data.showNodes()
            Data.showID()
            if getnodes:
                shortcuts.clear()
                if Data.showingNodes:
                    lines = Data.nodelines
                    if current_view == 'path_list':
                        path_list_view.set_pages(lines)
                        path_list_view.show_page()
                    elif current_view == 'tags_list':
                        tags_list_view.set_pages(lines)
                        tags_list_view.show_page()
                else:
                    lines = Data.notelines
                    leaf_view.set_pages(lines)
                    leaf_view.show_page()
            Data.setGet()


        elif text.startswith('f'):
            if current_view != 'find':
                previous_view = current_view
                current_view = 'find'
            find = text[1:].strip()
            regex = find if find else None
            path_list_view.set_find(find)
            tags_list_view.set_find(find)
            find_view.set_find(find)
            if regex:
                shortcuts.clear()
                Data.find(find)
                lines = Data.findlines
                logger.debug(f"find: {find}; lines: {lines}")
                if lines:
                    find_view.set_pages(lines)
                    find_view.set_page(find_index)
                    find_view.show_page()
                else:
                    print(f"nothing found matching '{find}'")
            else:
                # clear
                shortcuts.clear()
                if Data.showingNodes:
                    lines = Data.nodelines
                    if current_view == 'path_list':
                        path_list_view.set_pages(lines)
                        path_list_view.set_page(path_list_index)
                        path_list_view.show_page()
                    elif current_view == 'tags_list':
                        tags_list_view.set_pages(lines)
                        tags_list_view.set_page(tags_list_index)
                        tags_list_view.show_page()
                    elif current_view == 'find':
                        find_view.set_pages(lines)
                        find_view.set_page(tags_list_index)
                        find_view.show_page()
                else:
                    lines = Data.notelines
                    leaf_view.set_pages(lines)
                    leaf_view.set_page(leaf_index)
                    leaf_view.show_page()


        elif text.startswith("i"):
            shortcuts.clear()
            idstr = text[1:].strip()
            if idstr:
                ok, msg = Data.showID(idstr)
                if ok:
                    if Data.showingNodes:
                        if current_view == 'path_list':
                            path_list_index = path_list_view.current_page
                            lines = Data.nodelines
                            path_list_view.set_pages(lines)
                            path_list_view.show_page()
                        elif current_view == 'tags_list':
                            tags_list_index = tags_list_view.current_page
                            lines = Data.nodelines
                            tags_list_view.set_pages(lines)
                            tags_list_view.show_page()
                    else:
                        previous_view = current_view
                        current_view = 'leaf'
                        leaf_index = leaf_view.current_page
                        lines = Data.notelines
                        lines.insert(0, f"IDENT: {idstr}")
                        leaf_view.set_pages(lines)
                        leaf_view.show_page()
                else: # not ok
                    show_message(msg)
            else:
                show_message("an IDENT argument is required but missing")

        elif text.startswith("e"):
            shortcuts.clear()
            idstr = text[1:].strip()
            if idstr:
                orig_mode = Data.mode
                Data.editID(idstr)
                Data.getNodes()
                Data.setMode(orig_mode)
                Data.showID(idstr)
                logger.debug(f"edit done; current_view: {current_view}; showingNodes: {Data.showingNodes}")
                # new_mode = Data.mode
                # if Data.showingNodes:
                if current_view == 'path_list':
                    path_list_index = path_list_view.current_page
                    lines = Data.nodelines
                    path_list_view.set_pages(lines)
                    path_list_view.show_page()
                elif current_view == 'tags_list':
                    tags_list_index = tags_list_view.current_page
                    lines = Data.nodelines
                    tags_list_view.set_pages(lines)
                    tags_list_view.show_page()
                elif current_view == 'find':
                    Data.find(find_view.find)
                    lines = Data.findlines
                    logger.debug(f"find: {find_view.find}; lines: {lines}")
                    find_view.set_pages(lines)
                    find_view.show_page()
                else:
                    leaf_index = leaf_view.current_page
                    lines = Data.notelines
                    logger.debug(f"leaf IDENT: {idstr}; notelines: {lines}")
                    lines.insert(0, f"IDENT: {idstr}")
                    leaf_view.set_pages(lines)
                    leaf_view.show_page()

            else:
                show_message("an IDENT argument is required but missing")


        elif text.startswith("a"):
            shortcuts.clear()
            entry = text[1:].strip()
            if entry:
                tmp, *child = entry.split(" ")
                idstr = tmp.split('-')[0]
                logger.debug(f"tmp: {tmp}; idstr: {idstr}")
                if child:
                    child = '_'.join(child)
                Data.addID(idstr, child)
                Data.getNodes()
                Data.showID(idstr)
                # if Data.showingNodes:
                if current_view == 'path_list':
                    path_list_index = path_list_view.current_page
                    lines = Data.nodelines
                    path_list_view.set_pages(lines)
                    path_list_view.show_page()
                elif current_view == 'tags_list':
                    tags_list_index = tags_list_view.current_page
                    lines = Data.nodelines
                    tags_list_view.set_pages(lines)
                    tags_list_view.show_page()
                elif current_view == 'find':
                    Data.find(find_view.find)
                    lines = Data.findlines
                    logger.debug(f"find: {find_view.find}; lines: {lines}")
                    find_view.set_pages(lines)
                    find_view.show_page()
                else:
                    leaf_index = leaf_view.current_page
                    lines = Data.notelines
                    logger.debug(f"leaf IDENT: {idstr}; notelines: {lines}")
                    leaf_view.set_pages(lines)
                    leaf_view.show_page()
            else:
                show_message("an IDENT argument is required but missing")


        elif text == 'l':
            shortcuts.clear()
            Data.toggleShowLeaves()
            Data.showID()
            if Data.showingNodes:
                lines = Data.nodelines
                if current_view == 'path_list':
                    path_list_view.set_pages(lines)
                    path_list_view.show_page()
                elif current_view == 'tags_list':
                    tags_list_view.set_pages(lines)
                    tags_list_view.show_page()
            else:
                lines = Data.notelines
                leaf_view.set_pages(lines)
                leaf_view.show_page()

        elif text == 'b':
            shortcuts.clear()
            Data.toggleShowBranches()
            Data.showID()
            if Data.showingNodes:
                lines = Data.nodelines
                if current_view == 'path_list':
                    path_list_view.set_pages(lines)
                    path_list_view.show_page()
                elif current_view == 'tags_list':
                    tags_list_view.set_pages(lines)
                    tags_list_view.show_page()
            else:
                lines = Data.notelines
                leaf_view.set_pages(lines)
                leaf_view.show_page()


        elif text == 'u':
            shortcuts.clear()
            res = check_update()
            show_message(res)

        elif text:
            shortcuts.clear()
            print(f"unrecognized command: '{text}'")

        else:
            shortcuts.clear()
            if Data.showingNodes:
                if current_view == 'path_list':
                    path_list_view.show_page()
                elif current_view == 'tags_list':
                    tags_list_view.show_page()
                elif current_view == 'find':
                    find_view.show_page()
                elif current_view == 'help':
                    help_view.show_page()
            else:
                leaf_view.show_page()


def main():
    columns, rows = shutil.get_terminal_size()
    parser = argparse.ArgumentParser(description=f"nts: Note Taking Simplified version {nts_version}")

    parser.add_argument("-s",  "--session", help="begin an interactive session", action="store_true")

    parser.add_argument("-l",  "--leaves", help="hide leaves",
                        action="store_true")

    parser.add_argument("-b",  "--branches", help="hide branches",
                        action="store_true")

    # parser.add_argument("-v", "--view", type=str, choices=['p', 't'],
    #                 help="view path or tags", default='p')

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
        session_app()

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
            print('args.path')
            Data.setMode('path')
            Data.showNodes()
            for line in Data.nodelines:
                print(line)
            print('')

        if args.tags:
            print('args.tags')
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



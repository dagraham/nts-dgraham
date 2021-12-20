import os, fnmatch
import sys
from pprint import pprint
from anytree import Node, RenderTree, render
from base64 import b64encode, b64decode
import base64
import re
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from prompt_toolkit import PromptSession
from prompt_toolkit import shortcuts
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.filters import Condition

from prompt_toolkit import print_formatted_text
# from prompt_toolkit.styles.named_colors import NAMED_COLORS
import textwrap

import shutil
import logging
import logging.config

import argparse

nts_version = "1.0.0"


note_regex = re.compile(r'^\+\s*([^\(]+)\s*(\(([^\)]*)\))?\s*$')

separator = os.path.sep

help = f"""\
NTS: Note Taking Simplified {nts_version}

Suppose, for example, that the nts "data" directory has a single
subdirectory "parent" which contains a single subdirectory "child"
which contains a single file "~/nts/data/parent/child/grandchild.txt"
with these lines:

    + note a (red, blue)
        The body of note a goes here

    + note b (blue, green)
        The body of note b here

    + note c (red, green)
        And the body of note c here

nts provides two views of this data directory.

Path View:

    └── parent 1
        └── child 2
            └── grandchild.txt 3
                    + note a (red, green) 3-1
                    + note b (blue, green) 3-2
                    + note c (red, blue) 3-3

Tag View:

    ├── blue 1
    │       + note b (blue, green) 1-1
    │       + note c (red, blue) 1-2
    ├── green 2
    │       + note a (red, green) 2-1
    │       + note b (blue, green) 2-2
    └── red 3
            + note a (red, green) 3-1
            + note c (red, blue) 3-2

    when the display contains more lines than will fit in the terminal
    window, the "left" and "right" cursor keys can be used to change pages.

interacting with nts uses the following commands. in each case, enter
the command up to the ")" at the ">" prompt and then press "return".

? or H) toogle this help/info display

q) quit

p) show path view

t) show tag view

i IDENTIFIER) inspect the item corresponding to "IDENTIFIER"

    nts provides the "identifiers" at the end of each line of the display,
    e.g., in the path view the "2" after "child" and the "3-2" after
    "+ note c (red, blue)". These identifiers can be used inspect the
    relevant item.

    In the tag view example, entering "i 1" at the prompt would display
    this PATH view:

        red 1
            + note a (red, blue) 1-1
            + note c (red, green) 1-2

    while entering "i 3-2" at the prompt would display this LEAF view

        + note c (red, green)
            And the body of note c here

    In path view, entering "i 3", on the other hand, would display the
    entire "grandchiid.tex" file again as a LEAF view.

    The term LEAF view is used in the last two cases because the display
    shows either a part or the entirety of a file rather than an outline.

s) switch between the most recent PATH and LEAF views

e IDENTIFIER) edit the item corresponding to "IDENTIFIER"

    This works similarly but only for IDENTIFIERs corresponding to txt
    files or notes. In the former case, the relevant file is opened in
    the external editor specified in the nts configuration file and, in
    the later case, the file is opened at the line corresponding to the
    note.

n) toggle displaying/hiding notes

In the tag view example, entering "n" would hide the notes from the
original display

    ├── blue 1
    ├── green 2
    ├── red 3

and entering "n" again would restore them.

/ REGEX) highlight lines matching REGEX

Set a case-insensitive regular expression. Lines containing a
match will be highlighted. Enter an empty value for REGEX to
clear highlighting.
"""


helplines = help.split("\n")

# The style sheet.
style = Style.from_dict({
    'plain':        '#fffafa',
    'inbox':        '#ff00ff',
    'pastdue':      '#87ceeb',
    'match':        '#ffff00',
    'record':       '#daa520',
    'prompt':       '#FFFF00',
    'available':    '#1e90ff',
    'waiting':      '#6495ed',
    'finished':     '#191970',
    'background': 'bg:#FFFF00 #000000',
})

def setup_logging(level, ntsdir, file=None):
    """
    Setup logging configuration. Override root:level in
    logging.yaml with default_level.
    """

    if not os.path.isdir(ntsdir):
        return

    log_levels = {
        1: logging.DEBUG,
        2: logging.INFO,
        3: logging.WARN,
        4: logging.ERROR,
        5: logging.CRITICAL
    }

    level = int(level)
    loglevel = log_levels.get(level, log_levels[3])

    # if we get here, we have an existing ntsdir
    logfile = os.path.normpath(os.path.abspath(os.path.join(ntsdir, "nts.log")))

    config = {'disable_existing_loggers': False,
              'formatters': {'simple': {
                  'format': '--- %(asctime)s - %(levelname)s - %(module)s.%(funcName)s\n    %(message)s'}},
              'handlers': {
                    'file': {
                        'backupCount': 7,
                        'class': 'logging.handlers.TimedRotatingFileHandler',
                        'encoding': 'utf8',
                        'filename': logfile,
                        'formatter': 'simple',
                        'level': loglevel,
                        'when': 'midnight',
                        'interval': 1}
              },
              'loggers': {
                  'etmmv': {
                    'handlers': ['file'],
                    'level': loglevel,
                    'propagate': False}
              },
              'root': {
                  'handlers': ['file'],
                  'level': loglevel},
              'version': 1}
    logging.config.dictConfig(config)
    logger.critical("\n######## Initializing logging #########")
    if file:
        logger.critical(f'logging for file: {file}\n    logging at level: {loglevel}\n    logging to file: {logfile}')
    else:
        logger.critical(f'logging at level: {loglevel}\n    logging to file: {logfile}')

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

def mysort(items):
    return sorted(items, key=lambda item: item.name)

def myprint(tokenlines, color=None):
    # tokenlines[-1][1] = tokenlines[-1][1].rstrip()
    print_formatted_text(FormattedText(tokenlines), style=style)

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
        note.append(body)
        notes.append(note)
        note = []
        body = []
    return notes


class ListView(object):

    def __init__(self, lines=[]):
        columns, rows = shutil.get_terminal_size()
        self.rows = rows -3 # integer number of allowed display rows
        self.find = None
        self.lines = lines
        self.pages = {}
        self.page_numbers = []
        self.current_page = None
        self.set_pages(lines)


    def set_find(self, regx):
        if regx:
            self.find = re.compile(r'%s' % regx , re.IGNORECASE)
        else:
            self.find = None
        self.set_lines(self.lines)


    def set_lines(self, lines):
        """
        Format the lines according to whether or not they match the find regex
        """
        self.lines = []
        if self.find:
            for line in lines:
                if isinstance(line, (tuple, list)):
                    text = line[1].rstrip()
                else:
                    text = line.rstrip()
                if self.find.search(text):
                    line = ('class:background', f"{text} \n")
                else:
                    line = ('class:plain', f"{text} \n")
                self.lines.append(line)
        else:
            for line in lines:
                if isinstance(line, (tuple, list)):
                    text = line[1].rstrip()
                else:
                    text = line.rstrip()
                line = ('class:plain', f"{text} \n")
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
            beg_line = (page_num - 1) * (self.rows + 1)
            page_lines = self.lines[beg_line:beg_line + self.rows]
            if page_lines:
                self.pages[str(page_num)] = page_lines
            else:
                break

        self.page_numbers = [x for x in self.pages.keys()]
        self.num_pages = len(self.page_numbers)
        self.current_page = 0 # current page number = self.page_numbers[0] = 1

        # for page in self.page_numbers:
        #     print(f"page {page}")
        #     for line in self.pages[page]:
        #         print(line)


    def get_page_footer(self):
        if self.num_pages < 2:
            return [('class:plain', f"{columns*'_'}")]
        page_num = self.page_numbers[self.current_page]
        prompt = "Use the left and right cursor keys to change pages"
        return [('class:plain', f"{columns*'_'}\n"),
                ('class:plain', f"Page {page_num}/{self.num_pages}. {prompt}.")]

    def show_page(self):
        # print(f"page_numbers: {self.page_numbers}\ncurrent_page: {self.current_page}")
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

        self.setStart()
        self.setMaxLevel(None)
        self.getNodes()
        self.setMode('p')
        self.showingNodes = True
        self.tagnodes = {}

    def setMaxLevel(self, maxlevel=None):
        self.maxlevel = None if maxlevel == 0 else maxlevel


    def toggleShowNotes(self):
        self.shownotes = not self.shownotes
        # if notes are hidden, make sure nodes are not hidden
        if not self.shownotes:
            self.shownodes = True

    def toggleShowNodes(self):
        self.shownodes = not self.shownodes
        # if nodes are hidden, make sure notes are not hidden
        if not self.shownodes:
            self.shownotes = True

    def setMode(self, mode):
        if mode not in ['p', 't']:
            print(f"error: bad mode {mode}")
            return
        self.mode = 'path' if mode == 'p' else "tags"
        self.nodes = self.pathnodes if mode == 'p' else self.tagnodes

    def setStart(self, start='.'):
        self.start = start

    def getNodes(self):
        """
        Create node trees for pathnodes and tagnodes.


        """
        taghash = {}
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

        # pprint(self.notedetails)

        self.tagnodes['.'] = Node('.')
        for key, values in taghash.items():
            self.tagnodes[f".{separator}{key}"] = Node(key, self.tagnodes['.'])
            self.tagnodes[f".{separator}{key}{separator}notes"] = Node('notes',
                    self.tagnodes[f".{separator}{key}"], lines=[x for x in values])


    def showNodes(self):

        columns, rows = shutil.get_terminal_size()
        # nodes = self.pathnodes if mode == 'path' else self.tagnodes
        id = 0
        id2info = {}
        linenum = 0
        linenum2node = {}
        output_lines = []
        start = self.nodes.get(self.start, self.nodes['.'])
        for pre, fill, node in RenderTree(start, childiter=mysort, maxlevel=self.maxlevel):
            # node with lines are only used for notes
            if node.name != '.' and not hasattr(node, 'lines'):
                id += 1
            idstr = f" {id}"
            path = [x.name for x in node.path]
            pathstr = separator.join(path)
            if node.name.endswith('.txt'):
                pathstr = os.path.join(self.rootdir, pathstr[2:])
            if self.shownotes:
                notenum = 0
                if hasattr(node, 'lines') and node.lines:
                    for line in node.lines:
                        # titlestr, tagstring,  (filepath, linenum)
                        title = textwrap.shorten(line[0], width=columns-20)
                        notenum += 1
                        if self.shownodes:
                            output_lines.append(f"{fill}{title}{line[1]} {id}-{notenum}")
                        else:
                            output_lines.append(f"{title}{line[1]} {id}-{notenum}")
                        id2info[(id, notenum)] = line[2]
                else:
                    id2info[(id,)] = (pathstr, None)

                    if id > 0 and self.shownodes:
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
        """display the contens of fllepath starting with linenum"""

        columns, rows = shutil.get_terminal_size()
        output_lines = []
        with open(filepath, 'r') as fo:
            lines = fo.readlines()
        if linenum is None:
            for line in lines:
                line = line.rstrip()
                output_lines.extend(textwrap.wrap(line, width=columns-4, subsequent_indent="  ", initial_indent="  "))
        else:
            output_lines.append(lines[linenum].rstrip())
            for line in lines[linenum+1:]:
                if line.startswith('+'):
                    break
                output_lines.extend(textwrap.wrap(line, width=columns-4, subsequent_indent="  ", initial_indent="  "))

        self.notelines = output_lines


    def find(self, find):
        matching_keys = []
        output_lines = []
        self.find_lines = []
        if not find:
            return output_lines
        regex = re.compile(r'%s' % find, re.IGNORECASE)
        for key, lines in self.notedetails.items():
            match = False
            for line in lines:
                match = regex.search(line)
                if match:
                    break
            if match:
                matching_keys.append(key)
        # print(f"matching_keys: {matching_keys}")
        if matching_keys:
            columns, rows = shutil.get_terminal_size()
            for identifier, key in self.id2info.items():
                # print(f"checking identifier: {identifier}; keys: {keys}")
                if key in matching_keys:
                    lines = self.notedetails.get(key, [])
                    idstr = "-".join([str(x) for x in identifier])
                    output_lines.append(f"{lines[0]} {idstr}")
                    for line in lines[1:]:
                        output_lines.extend(textwrap.wrap(line, width=columns-4,
                            subsequent_indent="  ", initial_indent="  "))
                    output_lines.append('')
        self.findlines = output_lines

    def showID(self, idstr="0"):
        shortcuts.clear()
        self.showNodes()
        idtup = tuple([int(x) for x in idstr.split('-')])

        info = self.id2info.get(idtup, ('.', )) # (key, line) tuple or None
        # info: (key, line)
        if info[0] in self.nodes:
            # we have a starting node
            self.showingNodes = True
            self.setStart(info[0])
            self.showNodes()
            if not self.sessionMode:
                for line in self.nodelines:
                    print(line)
        elif os.path.isfile(info[0]):
            # we have a filename and linenumber
            self.showingNodes = False
            filepath, linenum = info
            self.showNotes(filepath, linenum)
            if not self.sessionMode:
                for line in self.notelines:
                    print(line)
        else:
            print(f"error: bad index {info}")
            pprint(self.nodes.keys())


def session():

    Data.sessionMode = True
    bindings = KeyBindings()
    session = PromptSession(key_bindings=bindings)
    list_view = ListView()
    list_index = 0
    help_view = ListView(helplines)
    leaf_view = ListView()
    leaf_index = 0
    find_view = ListView()
    find_index = 0
    current_view = 'list'
    logger.info("Opened session")
    # print("id2info")
    # pprint(Data.id2info)

    @Condition
    def is_showing_list():
        return current_view == 'list'
        # return Data.showingNodes

    @Condition
    def is_showing_help():
        return current_view == 'help'

    @Condition
    def is_showing_leaf():
        return current_view == 'leaf'

    @Condition
    def is_showing_find():
        return current_view == 'find'

    # @bindings.add('<', filter=is_showing_leaf)
    # def _(event):
    #     def back():
    #         list_view.show_page()
    #     run_in_terminal(back)

    # @bindings.add('>', filter=is_showing_list)
    # def _(event):
    #     def back():
    #         leaf_view.show_page()
    #     run_in_terminal(back)

    @bindings.add('right', filter=is_showing_leaf)
    def _(event):
        def down():
            leaf_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('left', filter=is_showing_leaf)
    def _(event):
        def up():
            leaf_view.scroll_up()
        run_in_terminal(up)

    @bindings.add('right', filter=is_showing_list)
    def _(event):
        def down():
            list_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('left', filter=is_showing_list)
    def _(event):
        def up():
            list_view.scroll_up()
        run_in_terminal(up)

    @bindings.add('right', filter=is_showing_help)
    def _(event):
        def down():
            help_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('left', filter=is_showing_help)
    def _(event):
        def up():
            help_view.scroll_up()
        run_in_terminal(up)

    @bindings.add('right', filter=is_showing_find)
    def _(event):
        def down():
            find_view.scroll_down()
        run_in_terminal(down)

    @bindings.add('left', filter=is_showing_find)
    def _(event):
        def up():
            find_view.scroll_up()
        run_in_terminal(up)

    # @bindings.add('<', filter=is_showing_help)
    # def _(event):
    #     def back():
    #         global current_view
    #         current_view = 'list'
    #         list_view.show_page()
    #     run_in_terminal(back)




    shortcuts.clear()
    message = [("class:prompt", 'nts session. Enter ? or h (help), q (quit) or another command at the > prompt\nand press "return"')]
    regx = ""
    myprint(message)

    run = True
    while run:
        highlight = f"/'{regx}'" if regx else ""
        hidden = "" if Data.shownotes else "notes hidden"
        conj = "; " if hidden and highlight else ""
        spc = " " if hidden or highlight else ""
        message = [("class:prompt", f"{hidden}{conj}{highlight}{spc}> ")]
        text = session.prompt(message, style=style)
        text = text.strip()

        if text == 'q':
            shortcuts.clear()
            print("bye ...")
            break

        elif text in ['?', 'h']:
            if current_view == 'list':
                current_view = 'help'
                shortcuts.clear()
                # always start help at the first page
                help_view.set_page(0)
                help_view.show_page()
            elif current_view == "help":
                current_view = 'list'
                shortcuts.clear()
                # show list at the current page
                list_view.show_page()

        elif text == 'p':
            shortcuts.clear()
            current_view = 'list'
            Data.setMode('p')
            Data.showID()
            lines = Data.nodelines if Data.showingNodes else Data.notelines
            list_view.set_pages(lines)
            list_view.show_page()

        elif text == 't':
            shortcuts.clear()
            current_view = 'list'
            Data.setMode('t')
            Data.showID()
            lines = Data.nodelines if Data.showingNodes else Data.notelines
            list_view.set_pages(lines)
            list_view.show_page()

        elif text == 's':
            if current_view == 'list':
                shortcuts.clear()
                current_view = 'leaf'
                leaf_view.show_page()
            elif current_view == 'leaf':
                shortcuts.clear()
                current_view = 'list'
                list_view.show_page()

        elif text.startswith('f'):
            current_view = 'find'
            shortcuts.clear()
            find = text[1:].strip()
            regx = find if find else None
            # pprint(Data.id2info)
            Data.find(find)
            lines = Data.findlines
            if lines:
                list_view.set_find(find)
                leaf_view.set_find(find)
                find_view.set_find(find)
            find_view.set_pages(lines)
            find_view.set_page(find_index)
            find_view.show_page()

        elif text.startswith("i"):
            shortcuts.clear()
            lineid = text[1:].strip()
            Data.showID(lineid)
            if Data.showingNodes:
                current_view = 'list'
                list_index = list_view.current_page
                lines = Data.nodelines
                list_view.set_pages(lines)
                list_view.show_page()
            else:
                current_view = 'leaf'
                leaf_index = leaf_view.current_page
                lines = Data.notelines
                leaf_view.set_pages(lines)
                leaf_view.show_page()

        elif text == 'n':
            shortcuts.clear()
            Data.toggleShowNotes()
            Data.showID()
            if Data.showingNodes:
                lines = Data.nodelines
                list_view.set_pages(lines)
                list_view.show_page()
            else:
                lines = Data.notelines
                leaf_view.set_pages(lines)
                leaf_view.show_page()

        elif text == 'N':
            shortcuts.clear()
            Data.toggleShowNodes()
            Data.showID()
            if Data.showingNodes:
                lines = Data.nodelines
                list_view.set_pages(lines)
                list_view.show_page()
            else:
                lines = Data.notelines
                leaf_view.set_pages(lines)
                leaf_view.show_page()


        elif text.startswith('/'):
            shortcuts.clear()

            arg = text[1:]
            regx = arg if arg else None
            list_view.set_find(regx)
            leaf_view.set_find(regx)
            if Data.showingNodes:
                lines = Data.nodelines
                list_view.set_pages(lines)
                list_view.set_page(list_index)
                list_view.show_page()
            else:
                lines = Data.notelines
                leaf_view.set_pages(lines)
                leaf_view.set_page(leaf_index)
                leaf_view.show_page()

        elif text:
            shortcuts.clear()
            print(f"unrecognized command: '{text}'")

        else:
            shortcuts.clear()
            list_view.show_page()



def main():

    parser = argparse.ArgumentParser(description="Note Taking Simplified")
    parser.add_argument("-s",  "--session", help="begin an interactive session",
                        action="store_true")
    parser.add_argument("-n",  "--notes", help="suppress notes",
                        action="store_true")
    parser.add_argument("-N",  "--nodes", help="suppress nodes",
                        action="store_true")
    parser.add_argument("-o", "--outline", type=str, choices=['p', 't'],
                    help="outline by path or tags", default='p')

    parser.add_argument("-i", "--id", type=str, help="show output for the node/leaf corresponding to ID", default="0")
    parser.add_argument("-f", "--find", type=str, help="show notes containing a match for FIND")
    shortcuts.clear()
    args = parser.parse_args()
    if args.notes:
        Data.toggleShowNotes()
    if args.nodes:
        Data.toggleShowNodes()
    if args.find:
        Data.find(args.find)
        for line in Data.findlines:
            print(line)

    mode = args.outline

    Data.setMode(mode)

    if args.session:
        Data.sessionMode = True
        Data.showID(args.id)
        session()
    else:
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

    Data = NodeData(rootdir)

    main()



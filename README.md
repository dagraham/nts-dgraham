<img src="https://raw.githubusercontent.com/dagraham/nts-dgraham/master/ntslogo.png" alt="nts"  width="180px" />


# Note Taking Simplified

### Overview

_nts_ is pure python and will run on any platform that supports python >= 3.7.3. It runs in a terminal window that should be configured to use a fixed width (monospaced) font. _Menlo Regular_ for OSX and _DejaVu Sans Mono_ for Linux are good choices. A width of at least 68 characters for the terminal window is recommended.

Notes are recorded in plain text files with the extension ".txt" that are located anywhere below the *nts* data directory. These note files have a simple format:

* The first line of the note file must contain a *note title line*.

* All *note title lines* must begin with a "+" in the first column followed by a space and then the title of the note.

* Tags, if given, must be comma separated and enclosed in parentheses after the note title.

* The *note body* begins on the next line and continues until another *note title line* or the end of the file is reached.

* Lines that begin with one or more white space characters and then "+" are treated as part of the *note body* and not as the beginning of a new note.

* White space in the *note body* is preserved but whitespace between notes is ignored.

* Using spaces in directory and note file names should be avoided.



Suppose, e.g., that the *nts* data directory contains a single file

    ~/nts/data/parent/child/grandchild.txt

with this content:

    ---------------- grandchild.txt begins ---------------
    + note a (red, green)
        The body of note a goes here

    + note b (blue, green)
        The body of note b here

    + note c (red, blue)
        And the body of note c here
    ---------------- grandchild.txt ends -----------------

*nts* provides two main **views** of this data.

* Path View:

        └── parent 1
            └── child 2
                └── grandchild.txt 3
                        + note a (red, green) 3-1
                        + note b (blue, green) 3-2
                        + note c (red, blue) 3-3

* Tag View:

        ├── blue 1
        │       + note b (blue, green) 1-1
        │       + note c (red, blue) 1-2
        ├── green 2
        │       + note a (red, green) 2-1
        │       + note b (blue, green) 2-2
        └── red 3
                + note a (red, green) 3-1
                + note c (red, blue) 3-2

Both views are outlines with branches that end with note title lines. In path view, the nodes along the branches correspond to directory or file names and there can be many of these in each branch. In tag view, on the other hand, the nodes correspond to tag names and there can only be one of these in each branch.

The numeric identifiers appended to the lines in both views are provided by *nts*. These are single numbers for the *nodes* in the outline branches that have children and hyphenated numbers for the *leaves*, e.g., the "3" appended to the "grandchild.txt" node in the path view and the "2-1" appended to "+ note a (red, green)" in the tag view. The first of the two numbers in the leaf identifier is the indentifier of the parent node. These identifiers are used in various ways that are explained below.


### Usage

*nts* provides two ways of interacting with the data.

* Command mode

    Commands are entered at the terminal prompt. E.g., enter

        $ nts -p

    to display the path view in the terminal window. The output can also be piped in the standard way, e.g.,

        $ nts -p | less


* Session mode

    Use the `-s` argument to begin session mode:

        $ nts -s

    This begins a session in which data is loaded into memory and remains available for subsequent interaction. In this mode, *nts* assumes command of the terminal window. Then, e.g., pressing `p` would display the path view. Session mode adds several features not available in command mode, e.g., scrolling and incremental search.

#### Command Summary

Action          | Command Mode     | Session Mode    | Notes
----------------|------------------|-----------------|------
help            |  -h              |  h              |  ~
begin session   |  -s              |  ~              |  ~
end session     |   ~              |  q              |  ~
path view       |  -p              |  p              |  ~
tags view       |  -t              |  t              |  ~
hide leaves     |  -l              |  l              |  l
hide branches   |  -b              |  b              |  b
set max levels  |  -m MAX          |  m MAX          |  m
search          |                  |  / SEARCH       |  /
find REGEX      |  -f 'REGEX'      |  f REGEX        |  f
get REGEX       |  -g 'REGEX'      |  g REGEX        |  g
join JOIN       |  -j 'JOIN'       |  j JOIN         |  j
inspect IDENT   |  -i IDENT        |  i IDENT        |  i
edit IDENT      |  -e IDENT        |  e IDENT        |  e
add to IDENT    |  -a IDENT [NAME] |  a IDENT [NAME] |  a
version check   |  -v              |  v              |  v

- l: Suppress showing leaves in the outline. In session mode this toggles the display of leaves off and on.

- b: Suppress showing branches in the outline, i.e., display only the leaves. In session mode this toggles the display of the branches off and on.

- m: Limit the diplay of nodes in the branches to the integer MAX levels. Use MAX = 0 to display all levels.

- /: Incrementally search for matches for the case-insensitive string (not regular expression) SEARCH in the current display. When the search is active, press ",," (two commas successively) to clear the search or ".." to extend the search for matches to the complete notes for the active view. This is equivalent to invoking "f" with the same SEARCH argument.

- f: Display complete notes that contain a match in the title, tags or body for the case-insensitive regular expression REGEX.

- g: Display note titles that contain a match in the nodes leading to the note for the case-insensitive regular expression REGEX.

- j: Display note titles for notes with tags satisfying JOIN. E.g. if JOIN = "red", then notes containing the tag "RED" would be displayed. If JOIN = "| red, blue" then notes with _either_ the tag "red" _or_ the tag "blue" would be displayed. Finally, if JOIN = "& red, blue", then notes with _both_ the tags "red" _and_ "blue" would be displayed. In general JOIN = [|&] comma-separated list of case-insensitive regular expressions.

- i: If IDENT is the 2-number identifier for a note, then display the contents of that note. Else if IDENT is the identifier for a ".txt" file, then display the contents of that file. Otherwise limit the display to that part of the outline which starts from the corresponding node. Use IDENT = 0 to start from the root node.

- e: If IDENT corresponds to either a note or a ".txt" file, then open that file for editing and, in the case of a note, scroll to the beginning line of the note.

- a: If IDENT corresponds to either a note or a ".txt" file, then open that file for appending a new note. Otherwise, if IDENT corresponds to a directory and NAME is provided, add a child called NAME to that node. If NAME ends with ".txt", a new note file will be created and opened for editing. Otherwise, a new subdirectory called NAME will be added to the node directory. Use "0" as the IDENT to add to the root (data) node. In command mode, "IDENT NAME" should be wrapped in quotes.

- v: Compare the installed version of nts with the latest version on GitHub (requires internet connection) and report the result.


There are no commands in _nts_ to remove either a file or a directory. Please use your favorite file manager for these risky actions and don't forget to restart _nts_ to update its display.


### Configuration

Before you start *nts* for the first time, think about where you would like to keep your personal data files and any log files that _nts_ will create. This will be your nts _home directory_. The _nts_ configuration file, "cfg.yaml" will be placed in this directory as well as the data and log files in the subdirectories _data_ and _logs_, respectively.

The default is to use the current working directory when you start _nts_ as the _home directory_ either 1) if it is empty (unused so far) or 2) if it contains  subdirectories called "data" and "logs" or 3) if it contains a file called "cfg.yaml" and a subdirectory called "logs". To use this option just change to this directory before starting _nts_.

Alternatively, if the current working directory doesn't satisfy the requirments but there is an environmental variable, `NTSHOME`, that contains the path to an existing directory, then *nts* will use this as its _home directory_. To use this option, first create the directory and then set the enivonmental variable by, e.g., appending the following to your "~/.bash_profile":

        export NTSHOME="complete path to the nts home directory"

Finally, if neither of the previous alternatives are satisfied, then *nts* will use "\~/nts" as its _home directory_, creating this directory if necessary.

The _nts_ "data" and "logs" directories will be created if necessary as well as the _nts_ configuration file, "cfg.yaml" using default settings. If "data" needs to be created, the user will additionally be offered the opportunity to populate it with illustrative data. Here are the default contents of this file:


    ##################### IMPORTANT #############################
    #
    # Changes to this file only take effect when nts is restarted.
    #
    #############################################################
    #
    ##################        EDIT      #########################
    # The following are examples using the editor vim
    # To use the native version of vim under Mac OSX, replace
    # 'vim' with '/Applications/MacVim.app/Contents/MacOS/Vim'
    # in each of the following commands. Omit the '-g' argument
    # to open vim in the same _nts_ terminal window.
    #
    # edit {filepath} at {linenum} - wait for completion
    session_edit: vim -g -f +{linenum} {filepath}
    #
    # edit {filepath} at end of file - wait for completion
    session_add: vim -g -f + {filepath}
    #
    # edit {filepath} at {linenum} - do not wait for completion
    command_edit: vim -g +{linenum} {filepath}
    #
    # edit {filepath} at end of file - do not wait for completion
    command_add: vim -g + {filepath}
    #
    ##################        STYLE        ######################
    # style hex colors for plain, prompt and highlight
    style:
        plain:        '#FFFAFA'
        prompt:       '#FFF68F'
        message:      '#90C57F'
        highlight:    'bg:#FFF68F #000000'
    #
    ##################      TAG SORT       ######################
    # for listed keys, sort by the corresponding value. E.g. In
    # tag view items with the tag "now" will be sorted as if
    # they had the tag "!". Replace the keys and values with
    # whatever you find convenient
    tag_sort:
        now:        '!'
        next:       '#'
        assigned:   '$'
        someday:    '}'
        completed:  '~'

From time to time, new versions of _nts_ may add new options to "cfg.yaml". When this happens, you might consider renaming your existing "cfg.yaml" as, say, "cfg-orig.yaml". After you update _nts_ to the new version and restart it, a new version of "cfg.yaml" will be created. You can then cut and paste between "cfg-orig.yaml" and "cfg.yaml" to incorporate your settings into the new configuration.


### Organizing with Paths and Tags

Here are a few organizational ideas that have helped me. First, a reference section for all the stuff I want to remember, but usually can't:

        └── reference
            ├── entertainment
            │   ├── books.txt
            │   ├── movies.txt
            │   └── quotations.txt
            └── programming
                ├── markdown.txt
                ├── python.txt
                └── vim.txt

then a journal section for monthly notes

        └── journal
            ├── 2021
            │   ├── 10.txt
            │   ├── 11.txt
            │   └── 12.txt
            └── 2022
                ├── 01.txt
                ├── 02.txt
                └── 03.txt

and another for my projects

        └── projects
            ├── etm
            │   ├── advocacy.txt
            │   ├── bugs.txt
            │   └── ideas.txt
            └── nts
                ├── advocacy.txt
                ├── bugs.txt
                └── ideas.txt


For tags, the _GTD_ (Getting Things Done) classifiers are useful:

now
: action required as soon as possible

next
: action needed when time permits

assigned _NAME_
: assigned to _NAME_ for action but follow up still required

someday
: review from time to time for possible action

completed
: finished and kept for reference

In the default configuration file, shown above, these tags are listed for special treatment.

        tag_sort:
            now:        '!'
            next:       '#'
            assigned:   '$'
            someday:    '}'
            completed:  '~'

This means that tag view will be sorted so that items with the tag "now" will be sorted as if the tag were "!", items with the tag "next" as if the tag were "#" and so forth. Tags not listed in _tag_sort_ are sorted using the actual tag. Since the  _dictionary order_ for common keyboard characters in python is

    '!', '#', '$', '%', '&', '(', ')', '*', '+', '-', '/',
    '1', '2', '3', ';', '<', '=', '>', '?', '@', 'A', 'B', 'C',
    '[', ']', '^', '_', 'a', 'b', 'c', '{', '}', '~'

"now" will appear first, "next" second, "assigned" third and then "someday" and "completed" last. "assigned" tags will be further sorted by the accompanying _NAME_. Tags not listed in _tag_sort_ will appear in the normal dictionary order.

To illustrate this tag sorting with the default configuration, add the file

    ~/nts/data/parent/child/tagsort.txt

to the grandchild example given above and include the following content:


    ---------------- tagsort.txt begins ---------------
    + action required as soon as possible (now)
        In tag view, items with this tag will be sorted
        first

    + action needed when time permits (next)
        In tag view, items with this tag will be sorted
        second

    + assigned to joe for action (assigned joe)
        In tag view, items with this tag will be sorted
        in a third group and, within that group, by the
        name to whom it was assigned

    + assigned to bob for action (assigned bob)
        In tag view, items with this tag will be sorted
        in a third group and, within that group, by the
        name to whom it was assigned

    + review from time to time for action (someday)
        In tag view, items with this tag will be sorted
        next to last

    + finished but kept for reference (completed)
        In tag view, items with this tag will be sorted
        last
    ---------------- tagsort.txt ends -----------------

and note the order in which tags are sorted in _Tag View_:

    ├── now 1
    │       + action required as soon as possible (now) 1-1
    ├── next 2
    │       + action needed when time permits (next) 2-1
    ├── assigned bob 3
    │       + assigned to bob for action (assigned bob) 3-1
    ├── assigned joe 4
    │       + assigned to joe for action (assigned joe) 4-1
    ├── blue 5
    │       + note b (blue, green) 5-1
    │       + note c (red, blue) 5-2
    ├── green 6
    │       + note a (red, green) 6-1
    │       + note b (blue, green) 6-2
    ├── red 7
    │       + note a (red, green) 7-1
    │       + note c (red, blue) 7-2
    ├── someday 8
    │       + review from time to time for action (someday) 8-1
    └── completed 9
            + finished but kept for reference (completed) 9-1


One of the nice things about tags is that they are so easy to change. When you've taken care of a "now" item, e.g., just change the tag to "completed".

Other ideas for tags from _GTD_ involve contexts such as _home_, _office_, _shop_, _phone_, _internet_, _driving_ and so forth.

Sorting in path view is dictionary order for sibling nodes and file order for notes. Here is path view for the expanded example:


    └── parent 1
        └── child 2
            ├── grandchild.txt 3
            │       + note a (red, green) 3-1
            │       + note b (blue, green) 3-2
            │       + note c (red, blue) 3-3
            └── tagsort.txt 4
                    + action required as soon as possible (now) 4-1
                    + action needed when time permits (next) 4-2
                    + assigned to joe for action (assigned joe) 4-3
                    + assigned to bob for action (assigned bob) 4-4
                    + review from time to time for action (someday) 4-5
                    + finished but kept for reference (completed) 4-6

Note that the siblings "grandchild.txt" and "tagsort.txt" are in dictionary order but the notes in each of these files are listed in the order in which they occur in the file.


### Installation

#### For use in a virtual environment

The steps for OS/X or linux are illustrated below. For details see [python-virtual-environments-a-primer](https://www.google.com/url?q=https%3A%2F%2Frealpython.com%2Fpython-virtual-environments-a-primer%2F&sa=D&sntz=1&usg=AFQjCNFh7QpJQ4rPCDjZ1eLrV1BRCCpSmw).

Open a terminal and begin by creating a new directory/folder for the virtual environment, say `nts-pypi`, in your home directory:

    $ mkdir ~/nts-pypi
    $ cd ~/nts-pypi

Now continue by creating the virtual environment (python >= 3.7.3 is required for nts):

    $ python3 -m venv env

After a few seconds you will have an `./env` directory. Now activate the virtual environment:

    $ source env/bin/activate

The prompt will now change to something containing `(env)` to indicate that the virtual environment is active. Updating pip is now recommended:

    (env) $ pip install -U pip

Note that this invokes `./env/bin/pip`. Once this is finished, use pip to install nts:

    (env) $ pip install -U nts-dgraham

This will install nts and all its requirements in

    ./env/lib/python3.x/sitepackages

and will also install an executable called `nts` in `./env/bin`.You can then start nts using

    (env) nts ARGS

using ARGS enumerated in the **Command Summary** section above.


#### For use system wide

If your system allows you to run `sudo` and you want general access system wide, then you could instead install nts using

    $ sudo -H python3.x -m pip install -U nts-dgraham

replacing the `3.x` with the verion of python you want to use, e.g., `3.7`. This would put nts in your path (in the bin directory for python3.7).


You can then open a terminal and start nts using

    $ nts ARGS

using ARGS enumerated in the **Command Summary** section above.

### License

Copyright (c) 2010-2022 Daniel Graham <daniel.graham@duke.edu>. All rights reserved. Further information about nts is available at [github](https://github.com/dagraham/nts-dgraham), the _nts_ discussion group at [groups.io](https://groups.io/g/nts) and, of course, from [PyPI](https://pypi.org/project/nts-dgraham/).

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but *without any warranty*; without even the implied warranty of *merchantability* or *fitness for a particular purpose*. See [GNU General Public License](http://www.gnu.org/licenses/gpl.html) for more details.



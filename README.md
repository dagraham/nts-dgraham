<img src="https://raw.githubusercontent.com/dagraham/nts-dgraham/master/ntslogo.png" alt="nts"  width="180px" />


# Note Taking Simplified

### Overview

_nts_ is pure python and runs in a terminal window on any platform that supports python >= 3.7.3. Its purpose is to facilitate both recording and retrieving information. Further information is available at [github](https://github.com/dagraham/nts-dgraham), the _nts_ discussion group at [groups.io](https://groups.io/g/nts) and [PyPI](https://pypi.org/project/nts-dgraham/).

Notes are recorded in plain text files with the extension ".txt" located anywhere below the _nts data_ directory. Note files have a simple format:

* Each note begins with a "+" in the first column followed by a space and then the title of the note.

* Tags, if given, are comma separated and enclosed in parentheses after the note title.

* The _note body_ begins on the next line and continues until another note or the end of the file is reached.

* Lines that begin with one or more white space characters and then "+" are treated as part of the _note body_ and not as the beginning of a new note.

* White space in the _note body_ is preserved but whitespace between notes is ignored.

* Hidden files, i.e. files with names beginning with a period, are ignored.

* Directory and file names should not contain spaces.

Suppose, e.g., that the _nts_ data directory contains a single file

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

*nts* provides two main views of this data.

* _Path View_:

        └── parent 1
            └── child 2
                └── grandchild.txt 3
                        + note a (red, green) 3-1
                        + note b (blue, green) 3-2
                        + note c (red, blue) 3-3

* _Tag View_:

        ├── blue 1
        │       + note b (blue, green) 1-1
        │       + note c (red, blue) 1-2
        ├── green 2
        │       + note a (red, green) 2-1
        │       + note b (blue, green) 2-2
        └── red 3
                + note a (red, green) 3-1
                + note c (red, blue) 3-2

Both views are outlines with branches that end with leaves that correspond to note title lines. In path view, the nodes along the branches correspond to directory or file names and there can be many of these in each branch. In tag view, on the other hand, the nodes correspond to tag names and there can only be one of these in each branch.

The numeric identifiers appended to the lines in both views are provided by _nts_. These are single numbers for the *nodes* in the outline branches that have children and hyphenated numbers for the *leaves*, e.g., in path view the "3" appended to the "grandchild.txt" node and the "3-1" appended to the "+ note a (red, green)" leaf. In the leaf identifier, the first of the two numbers is the indentifier of the parent node. These identifiers are the IDENT arguments in the _Command Summary_ given below.


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
end session     |   ~              |  ^q or F8       |  ~
path view       |  -p              |  p              |  ~
tags view       |  -t              |  t              |  ~
hide leaves     |  -l              |  l              |  l
hide branches   |  -b              |  b              |  b
copy view       |   ~              |  c              |  c
set max levels  |  -m MAX          |  m MAX          |  m
search          |                  |  / SEARCH       |  /
find REGEX      |  -f [!]REGEX     |  f [!]REGEX     |  f
get REGEX       |  -g REGEX        |  g REGEX        |  g
join JOIN       |  -j JOIN         |  j JOIN         |  j
inspect IDENT   |  -i IDENT        |  i IDENT        |  i
edit IDENT      |  -e IDENT        |  e IDENT        |  e
add to IDENT    |  -a IDENT [NAME] |  a IDENT [NAME] |  a
refresh         |   ~              |  r              |  r
version check   |  -v              |  v              |  v

- l: Suppress showing leaves in the outline. In session mode this toggles the display of leaves off and on.

- b: Suppress showing branches in the outline, i.e., display only the leaves. In session mode this toggles the display of the branches off and on.

- c: Copy the active view to the system clipboard.

- m: Limit the diplay of nodes in the branches to the integer MAX levels below the starting node. Use MAX = 0 to display all levels.

- /|?: Start a case-insensitive, incremental search forward (/) or backward (?) for SEARCH. When the search is active, press "n" to continue the search in the same or "N" reverse direction,  ",," (two commas successively) to clear the search or ".." to apply the search to the complete notes of the active view.

- f: Show notes in the current view whose content contains a match for the case-insensitive regex REGEX. Press ",," to clear the search highlighting.

- g: Display note titles that contain a match in the nodes leading to the note for the case-insensitive regular expression REGEX.

- j: Display note titles for notes with tags satisfying JOIN. E.g. if JOIN = "red", then notes containing the tag "RED" would be displayed. If JOIN = "| red, blue" then notes with _either_ the tag "red" _or_ the tag "blue" would be displayed. Finally, if JOIN = "& red, blue", then notes with _both_ the tags "red" _and_ "blue" would be displayed. In general JOIN = [|&] comma-separated list of case-insensitive regular expressions.

- i: If IDENT is the 2-number identifier for a note, then display the contents of that note. Else if IDENT is the identifier for a ".txt" file, then display the contents of that file. Otherwise limit the display to that part of the outline which starts from the corresponding node. Use IDENT = 0 to start from the root node.

- e: If IDENT corresponds to either a note or a ".txt" file, then open that file for editing and, in the case of a note, scroll to the beginning line of the note.

- a: If IDENT corresponds to either a note or a ".txt" file, then open that file for appending a new note. Otherwise, if IDENT corresponds to a directory and NAME is provided, add a child called NAME to that node. If NAME ends with ".txt", a new note file will be created. Otherwise, a new subdirectory called NAME will be added to the node directory. Use "0" as the IDENT to add to the root (data) node. In command mode, "IDENT NAME" should be wrapped in quotes.

- r: reload data from the files in the data directory to incorporate external changes.

- v: Compare the installed version of nts with the latest version on GitHub (requires internet connection) and report the result.

Here is a link to a series of short videos illustrating basic usage:
[![workflow](https://raw.githubusercontent.com/dagraham/nts-dgraham/master/workflow.png "nts playlist")](https://www.youtube.com/playlist?list=PLN2WQIqrwSxx5beH7Qn8RC25xdoz-wEHY)

There are no commands in _nts_ to remove either a file or a directory. Please use your favorite file manager for these risky actions and don't forget to restart _nts_ to update its display.


### Configuration

_nts_ runs in a terminal window that should be configured to use a fixed width (monospaced) font. _Menlo Regular_ for OSX and _DejaVu Sans Mono_ for Linux are good choices. A width of at least 60 characters for the terminal window is recommended.

Before you start *nts* for the first time, think about where you would like to keep your personal data files and any log files that _nts_ will create. This will be your nts _home directory_. The _nts_ configuration file, "cfg.yaml" will be placed in this directory as well as the data and log files in the subdirectories _data_ and _logs_, respectively.

The default is to use the current working directory when you start _nts_ as the _home directory_ either 1) if it is empty (unused so far) or 2) if it contains  subdirectories called "data" and "logs" or 3) if it contains a file called "cfg.yaml" and a subdirectory called "logs". To use this option just change to this directory before starting _nts_.

Alternatively, if the current working directory doesn't satisfy the requirments but there is an environmental variable, `NTSHOME`, that contains the path to an existing directory, then *nts* will use this as its _home directory_. To use this option, first create the directory and then set the enivonmental variable by, e.g., appending the following to your "~/.bash_profile":

        export NTSHOME="complete path to the nts home directory"

Finally, if neither of the previous alternatives are satisfied, then *nts* will use "\~/nts" as its _home directory_, creating this directory if necessary.

The _nts_ "data" and "logs" directories will be created if necessary as well as the _nts_ configuration file, "cfg.yaml" using default settings. If "data" needs to be created, the user will additionally be offered the opportunity to populate it with illustrative data. Here are the default contents of this file:


    # Changes to this file only take effect when nts is restarted.
    # EDIT
    # The following are examples using the editor vim. Tip: to use the
    # native version of vim under Mac OSX, replace 'vim' in each of
    # the following commands with:
    #        '/Applications/MacVim.app/Contents/MacOS/Vim'
    # session_edit: cmd to edit {filepath} at {linenum} and await completion
    session_edit: vim -g -f +{linenum} {filepath}
    # session_add: cmd to edit {filepath} at end of file and await completion
    session_add: vim -g -f + {filepath}
    # command_edit: cmd to edit {filepath} at {linenum} without waiting
    command_edit: vim -g +{linenum} {filepath}
    # command_add: cmd to edit {filepath} at end of file without waiting
    command_add: vim -g + {filepath}
    # STYLE
    # session mode hex colors
	style:
		status:             '#FFFFFF bg:#396060'
		status.key:         '#FFAA00'
		not-searching:      '#888888'
		highlighted:        '#000000 bg:#FFFF75'
		plain:              '#FAFAFA bg:#1D3030'
    # TAG SORT
    # For listed keys, sort by the corresponding value. E.g. In tag view
    # items with the tag "now" will be sorted as if they had the tag "!".
    # Replace, remove or add keys and values with whatever you like.
    tag_sort:
        now:        '!'
        next:       '#'
        assigned:   '%'
        someday:    '&'
        completed:  '}'

The default STYLE section given above is designed for a terminal with a dark background. If you prefer a light background, you might want to try these settings instead:

	style:
		status:               '#FFFFFF bg:#437070'
		status.key:           '#FFAA00'
		not-searching:        '#888888'
		highlighted:          '#1D3030 bg:#A1CAF1'
		plain:                '#000000 bg:#FFF8DC'


If you make changes to "cfg.yaml" and would like to restore the defaults just delete the relevant settings from the file and restart _nts_ - the missing settings will be restored with their default values.

From time to time, new versions of _nts_ may add new settings to "cfg.yaml". When this happens, the new settings will automatically be added to your "cfg.yaml" the next time you start _nts_.


### View Sorting

The default values for _tag_sort_ in "cfg.yaml" mean that notes will be sorted in in _tag_view_ so that items with the tag "now" will be sorted as if the tag were "!", items with the tag "next" as if the tag were "#" and so forth. Tags not listed in _tag_sort_ will sorted using the actual tag. The  _dictionary sorting order_ for common keyboard characters in python is:

`! # % & ( ) * + - / 1 2 3 ; < = > ? @ A B C [ ] ^ _ a b c { } ~`

_nts_ implicitly assigns the tag "~" to notes without tags and, because of this sorting order, untagged items are listed last in _Tags View_.


To illustrate this tag sorting with the default configuration, suppose the file

    ~/nts/data/tagsort.txt

is added to the grandchild example given above with the following content:


    ---------------- tagsort.txt begins ---------------
    + action required as soon as possible (now)
        In tag view, items with this tag will be sorted
        first

    + action needed when time permits (next)
        In tag view, items with this tag will be sorted
        after 'now' items

    + assigned for action (assigned joe)
        In tag view, items with this tag will be sorted
        in a third group and, within that group, by the
        name to whom it was assigned

    + assigned for action (assigned bob)
        In tag view, items with this tag will be sorted
        in a third group and, within that group, by the
        name to whom it was assigned

    + review from time to time for action (someday)
        In tag view, items with this tag will be sorted
        after all tagged items other than 'completed'

    + finished but kept for reference (completed)
        In tag view, items with this tag will be sorted
        after all tagged items

    + a note with no tags
        In tag view, such items will be sorted last under
        the implicit tag '~'
    ---------------- tagsort.txt ends -----------------

With this addition, _Path View_ appears as:

    ├── parent 1
    │   └── child 2
    │       └── grandchild.txt 3
    │               + note a (red, green) 3-1
    │               + note b (blue, green) 3-2
    │               + note c (red, blue) 3-3
    └── tagsort.txt 4
            + action required as soon as possible (now) 4-1
            + action needed when time permits (next) 4-2
            + assigned for action (assigned joe) 4-3
            + assigned for action (assigned bob) 4-4
            + review from time to time for action (someday) 4-5
            + finished but kept for reference (completed) 4-6
            + a note with no tags 4-7


Sorting in this view is dictionary order for sibling nodes but notes are listed in the order in which they occur in the file. E.g., the siblings "parent" and "tagsort.txt" are in dictionary order but the notes in each file are listed in the order in which they occur in the file.


_Tags View_ reflects the _tag_sort_ setting in "cfg.yaml" with _now_, _next_,  _assigned_ and _someday_ first in that order, then _blue_, _green_ and _red_ in the middle in dictionary order and finally _completed_ and _~_ last:


	├── now 1
	│       + action required as soon as possible (now) 1-1
	├── next 2
	│       + action needed when time permits (next) 2-1
	├── assigned bob 3
	│       + assigned for action (assigned bob) 3-1
	├── assigned joe 4
	│       + assigned for action (assigned joe) 4-1
	├── someday 5
	│       + review from time to time for action (someday) 5-1
	├── blue 6
	│       + note b (blue, green) 6-1
	│       + note c (red, blue) 6-2
	├── green 7
	│       + note a (red, green) 7-1
	│       + note b (blue, green) 7-2
	├── red 8
	│       + note a (red, green) 8-1
	│       + note c (red, blue) 8-2
	├── completed 9
	│       + finished but kept for reference (completed) 9-1
	└── ~ 10
			+ a note with no tags 10-1

  Note also that within the _assigned_ tags, the sorting is in dictionary order with _assigned bob_ followed by _assigned joe_ even though _assigned joe_ occured before _assigned bob_ in the file.


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

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version. See [GNU General Public License](http://www.gnu.org/licenses/gpl.html) for more details. This program is distributed in the hope that it will be useful, but *without any warranty*; without even the implied warranty of *merchantability* or *fitness for a particular purpose*.


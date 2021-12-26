<figure>
	<img src="https://raw.githubusercontent.com/dagraham/nts-dgraham/master/ntslogo.png" alt="nts"  width="180px" />
</figure>


# Note Taking Simplified

### Overview

*nts* is pure python and will run on any platform that supports python >= 3.7.3.

Notes are recorded in plain text files with the extension ".txt" that are located anywhere below the *nts* data directory. These note files have a simple format:

* The first line of the note file must contain a *note title line*.

* All *note title lines* must begin with a "+" in the first column followed by a space and then the title of the note.

* Tags, if given, must be comma separated and enclosed in parentheses after the note title.

* The *note body* begins on the next line and continues until another *note title line* or the end of the file is reached.

* Lines that begin with one or more white space characters and then "+" are treated as part of the *note body* and not as the beginning of a new note.

* White space in the *note body* is preserved but whitespace between notes is ignored.



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

		$ nts.py -o p

	to display the path view in the terminal window. The output can also be piped in the standard way, e.g.,

		$ ntp.py -o p | less


* Session mode

    Use the `-s` argument to begin session mode:

		$ nts.py -s

	This begins a session in which data is loaded into memory and remains available for subsequent interaction. In this mode, *nts* assumes command of the terminal window and provides its own `>` command prompt. Then, e.g., entering `p` at the prompt

		> p

	would display the path view. Session mode adds several features not available in command mode. E.g., when there are more lines to display than will fit in the terminal window, the lines are divided into pages with up and down cursor keys used to change pages.

#### Command Summary

Action          | Command Mode | Session Mode | Notes
---|---|---|---
help            |  -h      |  h or ?    |   1
begin session   |  -s      |  ~         |   ~
end session     |    ~     |  q         |   ~
path view       |  -o p    |  p         |   ~
tags view       |  -o t    |  t         |   ~
hide notes      | -n       | n          |   2
hide nodes      | -N       | N          |   3
set max levels  | -m MAX   | m MAX      |   4
highlight REGEX |          |  / REGEX   |   5
find REGEX      | -f REGEX | f REGEX    |   6
inspect IDENT   | -i IDENT | i IDENT    |   7
switch displays |    ~     | s          |   8
edit IDENT      | -e IDENT | e IDENT    |   9
add to IDENT    | -a IDENT | a IDENT    |  10

1. In session mode, this is a toggle that switches the display back and forth between the active and the help displays.
1. Suppress showing notes in the outline. In session mode this toggles the display of notes off and on.
1. Suppress showing nodes in the outline, i.e., display only the notes. In session mode this toggles the display of the nodes off and on.
1. Limit the diplay of nodes in the outline to the integer MAX levels. Use MAX = 0 to display all levels.
1. Highlight displayed lines that contain a match for the case-insensitive regular expression REGEX. Enter an empty REGEX to clear highlighting.
1. Display complete notes that contain a match in the title, tags or body for the case-insensitive regular expression REGEX.
1. If IDENT is the 2-number identifier for a note, then display the contents of that note. Else if IDENT is the identifier for a ".txt" file, then display the contents of that file. Otherwise limit the display to that part of the outline which starts from the corresponding node.
1. In session mode, switch back and forth between the most recent path or tag display and the most recent display of a file or note.
1. If IDENT corresponds to either a note or a ".txt" file, then open that file for editing and, in the case of a note, scroll to the beginning line of the note.
1. If IDENT corresponds to either a note or a ".txt" file, then open that file for appending a new note. Otherwise, if IDENT corresponds to a directory, then prompt for the name of a child to add to that node. If the name entered ends with ".txt", a new note file will be created and opened for editing. Otherwise, a new subdirectory will be added to the node directory using the name provided. Use "0" as the IDENT to add to the root (data) node.


### Configuration

In the current, preliminary version of *nts* there are no user configurable options. *nts* will use "\~/nts" as its home directory and will store its data files in and below "\~/nts/data".

### License

Copyright (c) 2010-2022 Daniel Graham <daniel.graham@duke.edu>. All rights reserved. Further information about nts is available at [github](https://github.com/dagraham/nts-dgraham) and in the nts discussion group at [groups.io](https://groups.io/g/nts).

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but *without any warranty*; without even the implied warranty of *merchantability* or *fitness for a particular purpose*. See [GNU General Public License](http://www.gnu.org/licenses/gpl.html) for more details.



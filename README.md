<img src="https://raw.githubusercontent.com/dagraham/nts-dgraham/master/ntslogo.png" alt="nts"  width="180px" />


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

		$ nts -v p

	to display the path view in the terminal window. The output can also be piped in the standard way, e.g.,

		$ nts -v p | less


* Session mode

    Use the `-s` argument to begin session mode:

		$ nts -s

	This begins a session in which data is loaded into memory and remains available for subsequent interaction. In this mode, *nts* assumes command of the terminal window and provides its own `>` command prompt. Then, e.g., entering `p` at the prompt

		> p

	would display the path view. Session mode adds several features not available in command mode. E.g., when there are more lines to display than will fit in the terminal window, the lines are divided into pages with up and down cursor keys used to change pages.

#### Command Summary

Action          | Command Mode | Session Mode | Notes
----------------|--------------|--------------|------
help            |  -h		   |  h or ?      |   1
begin session   |  -s		   |  ~			  |   ~
end session     |    ~		   |  q			  |   ~
path view       |  -v p		   |  p			  |   ~
tags view       |  -v t		   |  t			  |   ~
hide notes      | -n		   | n			  |   2
hide nodes      | -N		   | N			  |   3
set max levels  | -m MAX	   | m MAX		  |   4
highlight REGEX |			   |  / REGEX	  |   5
find REGEX      | -f REGEX	   | f REGEX	  |   6
inspect IDENT   | -i IDENT	   | i IDENT	  |   7
switch displays |    ~		   | s			  |   8
edit IDENT      | -e IDENT	   | e IDENT	  |   9
add to IDENT    | -a IDENT	   | a IDENT	  |  10

1. In session mode, this is a toggle that switches the display back and forth between the active and the help displays.
2. Suppress showing notes in the outline. In session mode this toggles the display of notes off and on.
3. Suppress showing nodes in the outline, i.e., display only the notes. In session mode this toggles the display of the nodes off and on.
4. Limit the diplay of nodes in the outline to the integer MAX levels. Use MAX = 0 to display all levels.
5. Highlight displayed lines that contain a match for the case-insensitive regular expression REGEX. Enter an empty REGEX to clear highlighting.
6. Display complete notes that contain a match in the title, tags or body for the case-insensitive regular expression REGEX.
7. If IDENT is the 2-number identifier for a note, then display the contents of that note. Else if IDENT is the identifier for a ".txt" file, then display the contents of that file. Otherwise limit the display to that part of the outline which starts from the corresponding node.
8. In session mode, switch back and forth between the most recent path or tag display and the most recent display of a file or note.
9. If IDENT corresponds to either a note or a ".txt" file, then open that file for editing and, in the case of a note, scroll to the beginning line of the note.
10. If IDENT corresponds to either a note or a ".txt" file, then open that file for appending a new note. Otherwise, if IDENT corresponds to a directory, then prompt for the name of a child to add to that node. If the name entered ends with ".txt", a new note file will be created and opened for editing. Otherwise, a new subdirectory will be added to the node directory using the name provided. Use "0" as the IDENT to add to the root (data) node.


### Configuration

Before you start *nts* for the first time, think about where you would like to keep your personal data files and any log files that _nts_ will create. This will be your nts *home* directory. The _nts_ configuration file, "cfg.yaml" will be placed in this directory as well as the data and log files in the subdirectories "data" and "logs", respectively.

1. The default is to use whatever directory you're in when you start _nts_ as the  home directory either 1) if it is empty (unused so far) or 2) if it contains  subdirectories called "data" and "logs" (not empty and already in use for _nts_). To use this option just change to this directory before starting _nts_.

2. Alternatively, if the current working directory doesn't satisfy the requirments but there is an environmental variable, `NTSHOME`, that contains the path to an existing directory, then *nts* will use this as its home directory. To use this option, first create the directory and then set the enivonmental variable by, e.g., appending the following to your "~/.bash_profile":

		export NTSHOME="complete path to the nts home directory"

3. Finally, if neither of the previous alternatives are satisfied, then *nts* will use "\~/nts" as its home directory, creating this directory if necessary.

    The _nts_ "data" and "logs" directories will be created if necessary. If "data" needs to be created, the user will additionally be offered the opportunity to populate it with the data for the grandchild.txt example discussed above.

4. The _nts_ configuration file, `cfg.yaml` will also be created in this home directory. The default settings are for the editor _vim_.  If you prefer using another editor, you will need to edit this file and make the necessary changes. Here are the default contents of this file:

        ################# IMPORTANT #########################
        #
        # Changes only take effect when nts is restarted.
        #
        #####################################################
        #
        # edit {filepath} at {linenum} - wait for completion
        session_edit: gvim -f +{linenum} {filepath}
        #
        # edit {filepath} at end of file - wait for completion
        session_add: gvim -f + {filepath}
        #
        # edit {filepath} at {linenum} - no wait for completion
        command_edit: gvim +{linenum} {filepath}
        #
        # edit {filepath} at end of file - no wait for completion
        command_add: gvim  + {filepath}

    The first command, e.g.,  is for editing in session mode and invokes gvim with the '-f' switch. This switch blocks _nts_ until gvim is closed and, when this happens, _nts_ will reload the data files to reflect any changes. The '+{linenum}' and '{filepath}' arguments will be replaced by _nts_ before the command is executed by the relevant line number and filepath.


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



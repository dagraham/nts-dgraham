<img src="https://raw.githubusercontent.com/dagraham/nts-dgraham/master/ntslogo.png" alt="nts" title="note taking simplified" width="200px" />

This is the etm user manual. Further information about etm is available at [github](https://github.com/dagraham/nts-dgraham) and in the nts discussion group at [groups.io](https://groups.io/g/nts).


Features
----------

* Pure python with plain text note files. Both the GUI and command line versions run on any platform that supports python.

* Quickly enter notes using a simple, intuitive format:

        ------------------- begin note file ---------------------
        + note title (optional comma-separated list of tags)
        note body on one or more lines

        + another note title (possibly with tags)
        and its body

        ...
        --------------------- end note file ---------------------

* View items sorted by file path or tag.

* Limit the display to items whose path, tags and/or text match regular expression search strings.

* Start typing in the left-hand tree panel of the gui to expose and jump to
  matching notes.

* Edit notes internally or externally with your favorite editor.

* Display selected items as HTML with an option to print.

* Use standard markdown or restructured text markup in note bodies.

* Export selected items in md (markdown) or rst (restructured text) format.

* Full support for unicode.

* Optional base 64 encoding for selected note files.

Configuration
-----------------

If the current working directory when you start nts has a file named 'rc' in
it, then that file will be used as the nts configuration file even if it is
empty. Otherwise, '~/.nts/rc' will be used and, if necessary, created. Missing
settings will be added with default values.

This configuration file is self-documented and can be freely edited. If you make changes you don't like you can simply erase the offending part, or even the entire file, and it will be recreated with defaults the next time you run either *n.py* or *n.pyw*.

Note file format
------------------

Notes files by default have either the extension '.txt' (plain text) or the
extension '.enc' (base 64 encoded) and are located in or below 'ntsdata'. The
data directory 'ntsdata' and the file extensions 'ntstxt' for plain text and
'ntsenc' for base 64 encrypted are set in your rc file. Note that the base 64
encoding is intended to provide only VERY LIGHT WEIGHT protection.

Both the plain text and encoded file types support unicode characters with
normal, readable display both in the GUI and in command line output.

Each notes file can contain one or more notes using the following format
for each::

    + note title (optional tags)
    one or more lines containing
       the body of the note

    with all white space preserved.

The first line of the note file must contain a note title. In this and other
note titles, the '+' must be in the first column. If given, tags must be comma
separated and enclosed in parentheses. The note body begins with the next line
and continues until another note title or the end of the file is reached.
(Lines that begin with one or more white space characters and then '+' are
treated as part of the note body and not as a new note title.) White space in
the note body is preserved but whitespace between notes is ignored.

Note file hierarchy
--------------------

The directory structure in your ntsdata directory provides the hierarchy for
your notes. E.g., suppose you have the notes file::

        ~/.nts/data/parent/child/grandchild.txt

with the following content::

    ----------- begin grandchild.txt ----------------------
    + note a (tag 1, tag 2)
    the body of my first note

    + note b (tag 2, tag 3)
    the body of my second note
    ----------- end grandchild.txt ------------------------

Then when outlining by **path** you would see::

    parent
        child
            grandchild
                note a
                note b

and when outlining by **tag** you would see::

    tag 1
        note a
    tag 2
        note a
        note b
    tag 3
        note b

Multiple note collections
---------------------------

You can have as many rc files as you like, each with its own ntsdata
directory, and thus as many separate notes hierarchies as you like.

Suppose, for example, I have a directory '~/Documents/Research' with
subdirectories corresponding to my research projects. I can place an empty rc
file in this directory, say by changing to this directory in a terminal and
then running 'touch rc'. When I next run 'n.py' from the same directory, nts
will fill the empty rc file with defaults and with this directory as the value
of ntsdata. If I already have files with the extension '.txt' in or below this
directory, I could change the 'ntstxt' entry to, say, '.nts', to avoid
conflicts. Now I can put notes files anywhere I like within this directory and
its sub-directories. To make life even more convenient I could create a shell
script::

        --------------begin research.sh-----------------------
        #!/bin/sh
        cd ~/Documents/Research
        n.pyw &
        -------------- end research.sh -----------------------

and then use the command 'research.sh' to start an instance of the nts gui
with the notes from the Research directory.

Since pressing F5 within nts with a directory selected opens that directory
with the system default application, usually your file manager, nts gives you
immediate access to other, related files within the directory hierarchy.

Markup
-------

Either 'markdown' or 'restructured text' markup can be used in the body of
notes. Moreover, by setting either

    markup = "md"

or

    markup = "rst"

in your nts rc file, nts will provide consistent markup when exporting
selected notes. Further, if markdown (or docutils for restructured text) is
installed on your system, you will be able to display selected notes as html
with an option to print.

There are many similarities between the two types of markup, e.g., under
either you would use ``*emphasis*`` for *emphasis* and ``**bold faced**`` for
**bold faced**. More generally, markdown is somewhat simpler to use but also
somewhat less powerful. See markdown_ and quickref_ for details.

.. _markdown: http://daringfireball.net/projects/markdown/syntax

.. _quickref: http://docutils.sourceforge.net/docs/user/rst/quickref.html

Using the standard tools that come with python's docutils module, rst output
can be easily converted to a number of formats including HTML, Latex and
OpenOffice ODF. Similarly, md output can be converted to other formats using
pandoc_.

.. _pandoc: http://johnmacfarlane.net/pandoc/


Rotating backup files
----------------------

A backup is made of any file before nts makes any changes to it. For example,
before saving a change to the base 64 encoded file, 'mynotes.enc', the exising
file would first be copied to '.mynotes.bk1'. If '.mynotes.bk1' already exists
and it is more than one day old, it would first be moved to '.mynotes.bk2'.
Similarly, if '.mynotes.bk2' already exists, then it would be first be moved
to '.mynotes.bk3' and so forth. In this way, up to 'numbaks' (3 by default)
rotating backups of are kept with '.bk1' the most recent.

The process is similar for plain text files but the copy is encoded before
saving.  Thus all backups are base 64 encoded.


Installation/Updating
----------------------

nts can be installed in the normal python way: download, unpack the nts source in a temporary directory, open a terminal ('Command Prompt' in Windows), cd to that directory and then run::

    sudo python setup.py install

Windows users can omit the 'sudo'. The temporary directory can then be removed. This will download and install any necessary supporting modules, install the nts package in the 'site-packages' subdirectory of your python distribution and install the executables *n.py*  and *n.pyw* in the 'bin' subdirectory of your python distribution.

If you have setuptools installed, you can skip downloading and use::

    sudo easy_install -U nts

either to install nts or to update to the latest version.

Setuptools can also be used to install docutils::

    sudo easy_install -U docutils

and markdown::

    sudo easy_install -U markdown

Easy_install is part of the python package setuptools_. To install it, download the appropriate egg file for your platform, e.g.,
::

    setuptools-0.6c11-py2.6.egg.sh

.. _setuptools: http://pypi.python.org/pypi/setuptools

Then cd to the directory containing the egg file and, if necessary, rename it to remove the '.sh' extension::

    mv setuptools-0.6c11-py2.6.egg.sh setuptools-0.6c11-py2.6.egg

The last step is to run the (renamed) egg file as if it were a shell script::

    sudo sh setuptools-0.6c11-py2.6.egg

Setuptools will install itself using the matching version of python (e.g. 'python2.6'), and will place the 'easy_install' executable in the default location for python scripts.

OS X users
~~~~~~~~~~~~

A standalone version, nts.app, is provided for Mac OS X users as a standard dmg file. Download this file, click on it and then drag nts.app to your Applications folder. Note that this application provides the gui version of nts but not the command line version.

Local / temporary installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you would like to try *nts* out without installing the system files or if you don't have root privileges but would like to install nts for your own use, the process is simple. Unpack the nts source in a convenient directory, cd to that directory and then run
::

  ./n.py [options]

This does not require root privileges and will not install any system files but will create the user specific configuration, data and alert files mentioned below in your home directory. You could, of course, use aliases or symbolic links to these files and avoid even having to change to this directory, e.g., if these files are located in NTSDIR, then you could add these lines to your ~/.bash_profile::

    alias n.py='NTSDIR/n.py'

replacing NTSDIR, of course, with the actual path. This alias would then function in the way described under *usage* below.


Usage
-------------------

For command line usage, running
::

    n.py -h

gives::

    Usage: n.py [options] [args]

    Manage notes using simple text files. (C) 2010-2011 Daniel A Graham.

    Options:
    --version     show program's version number and exit
    -h, --help    show this help message and exit
    -o OUTLINEBY  An element from [p, t] where:
                    p: outline by path
                    t: outline by tag
                    Default: p.
    -p PATH       Regular expression. Include items with paths matching PATH
                    (ignoring case). Prepend an exclamation mark, i.e., use !PATH
                    rather than PATH, to include items which do NOT have paths
                    matching PATH.
    -t TAG        Regular expression. Include items with tags matching TAG
                    (ignoring case). Prepend an exclamation mark, i.e., use !TAG
                    rather than TAG, to include items which do NOT have tags
                    matching TAG.
    -f FIND       Regular expression. Include items containing FIND (ignoring
                    case) in the note text. Prepend an exclamation mark, i.e., use
                    !FIND rather than FIND, to include notes which do NOT have
                    note texts matching FIND.
    -d DISPLAY    An integer from [1, ..., 7] which is the sum of one or
                    more of the following:
                    1: note title
                    2: note body
                    4: note id and tags
                    Default: 1.
    -l LINES      If LINES is 0 or if the note body contains no more than LINES
                    + 1 lines, show the entire body of the note. Else show the
                    first LINES lines and append a line showing the number of
                    omitted lines. Default: 0.
    -n NUMBER     0: hide item numbers; 1: Show item numbers.
                    Default: 1.
    -e EDIT       If there is a note numbered EDIT among those which satisfy the
                    current filters, then open that note for editing using EDITOR.
    -E EDITFILE   If there is a note numbered EDITFILE among those which satisfy
                    the current filters, then open the file containing that note
                    at the beginning line of the note for editing using EDITOR.
    -r REMOVE     If there is a note numbered REMOVE among those which satisfy
                    the current filters, then remove that note after prompting for
                    confirmation.
    --tag_usage   Print a report showing the number of uses for each tag and
                    exit.
    -a            Add a new note.
    -q            Add a quick note.
    -N            Check for a newer version of nts and exit.

    Args:
        numbers and ranges of note numbers to display, e.g., '10 14:16' would
        limit the display to notes numbered 10, 14, 15 and 16.


Alternatively, for the gui usage, run::

    n.pyw

to open the wx(python) GUI interface and then press *F1* for usage information.

License
-------

Copyright (c) 2010 Daniel Graham <daniel.graham@duke.edu>. All rights
reserved.

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.

    http://www.gnu.org/licenses/gpl.html

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.


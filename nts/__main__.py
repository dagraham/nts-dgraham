#tp!/usr/bin/env python3
import sys
import os
import logging
import logging.config
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger()
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.styles.named_colors import NAMED_COLORS
from copy import deepcopy

import ruamel.yaml
yaml = ruamel.yaml.YAML()

# for nts.yaml

dark = """\
light_background: false
style:
    status:             '#FFFFFF bg:#396060'
    status.key:         '#FFAA00'
    not-searching:      '#888888'
    highlighted:        '#000000 bg:#FFFF75'
    plain:              '#FAFAFA bg:#1D3030'
"""

light = """\
light_background: true
style:
    status:               '#FFFFFF bg:#437070'
    status.key:           '#FFAA00'
    not-searching:        '#888888'
    highlighted:          '#1D3030 bg:#A1CAF1'
    plain:                '#000000 bg:#FFF8DC'
"""

default_template= """\
# Changes to this file only take effect when nts is restarted.
# EDIT
# The following are examples using the editor vim. Tip: to use the
# native version of vim under Mac OSX, replace 'vim' in edit_command
# with:
#        /Applications/MacVim.app/Contents/MacOS/Vim
edit_command: vim
# session_edit_args: arguments to edit {filepath} at {linenum} in
# session mode and await completion
session_edit_args: -g -f +{linenum} {filepath}
# session_add: arguments to edit {filepath} at end of file in session
# mode and await completion
session_add_args: -g -f + {filepath}
# command_edit_args: arguments to edit {filepath} at {linenum} in
# command mode without waiting
command_edit_args:  +{linenum} {filepath}
# command_add_args: arguments to edit {filepath} at end of file
# in command mode without waiting
command_add_args: + {filepath}
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
# STYLE
# color settings for session mode
"""



def make_grandchild(rootdir):
    grandchild = """\
+ note a (red, green)
    The body of note a goes here

+ note b (blue, green)
    The body of note b goes here

+ note c (red, blue)
    And the body of note c goes here
"""
    tagsort = """\
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
"""
    full_path = rootdir
    for path in ['parent', 'child']:
        full_path = os.path.join(full_path, path)
        if not os.path.isdir(full_path):
            os.mkdir(full_path)
    grandchild_path = os.path.join(full_path, 'grandchild.txt')
    with open(grandchild_path, 'w') as fo:
        fo.write(grandchild)
    print(f"created '{full_path}'")

    tagsort_path = os.path.join(rootdir, 'tagsort.txt')
    with open(tagsort_path, 'w') as fo:
        fo.write(tagsort)
    print(f"created '{full_path}'")

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


def main():
    import nts
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logger = logging.getLogger()
    MIN_PYTHON = (3, 7, 3)
    if sys.version_info < MIN_PYTHON:
        mv = ".".join([str(x) for x in MIN_PYTHON])
        sys.exit(f"Python {mv} or later is required.\n")
    import os
    IS_VENV = os.getenv('VIRTUAL_ENV') is not None
    import nts.__version__ as version

    cwd = os.getcwd()
    dlst = [x for x in os.listdir(cwd) if not x.startswith('.')]
    NTSHOME = os.environ.get("NTSHOME")
    if len(dlst) == 0 or ('data' in dlst and 'logs' in dlst) or ('cfg.yaml' in dlst and 'logs' in dlst):
        # use cwd if it is empty or contains both data and logs
        ntshome = cwd
    elif NTSHOME and os.path.isdir(NTSHOME):
        # else use NTSHOME if it is set and specifies a directory
        ntshome = NTSHOME
    else:
        # use the default ~/nts
        ntshome = os.path.join(os.path.expanduser('~'), 'nts')
    if not os.path.isdir(ntshome):
        text = prompt(f"'{ntshome}' does not exist. Create it [yN] > ")
        if text.lower().strip() == 'y':
            os.mkdir(ntsdir)
        else:
            print("cancelled")
            return

    cfg_path = os.path.join(ntshome, 'cfg.yaml')
    if os.path.isfile(cfg_path):
        has_cfg = True
        with open(cfg_path, 'r') as fn:
            try:
                user = yaml.load(fn)
            except Exception as e:
                error = f"This exception was raised when loading settings:\n---\n{e}---\nPlease correct the error in {cfg_path} or remove it and restart nts.\n"
                logger.critical(error)
                sys.exit()
        if 'light_background' not in user:
            text = prompt(f"""\
d)ark or l)ight terminal background? [Dl] > """)
            if text.lower() == 'l':
                default_cfg = default_template + light
            else:
                default_cfg = default_template + dark
        elif user['light_background']:
            default_cfg = default_template + light
        else:
            default_cfg = default_template + dark
    else:
        has_cfg = False
        text = prompt(f"""\
Use color settings for a d)ark or l)ight terminal background? [Dl] > """)
        if text.lower() == 'l':
            default_cfg = default_template + light
        else:
            default_cfg = default_template + dark


    defaults = ruamel.yaml.load(default_cfg, ruamel.yaml.RoundTripLoader)
    # ruamel.yaml.dump(defaults, sys.stdout, Dumper=ruamel.yaml.RoundTripDumper)
    merged = deepcopy(defaults)

    logdir = os.path.normpath(os.path.join(ntshome, 'logs'))
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    loglevel = 2 # info
    log_levels = [str(x) for x in range(1, 6)]
    if len(sys.argv) > 1 and sys.argv[1] in log_levels:
        loglevel = int(sys.argv.pop(1))

    setup_logging(loglevel, logdir)
    logger.debug(f"nts home directory: '{ntshome}'")
    if has_cfg:
        changes = []
        for key, value in defaults.items():
            # if there is a user setting, use it - else use the default
            if key in user:
                if key == 'style':
                    for k, v in defaults['style'].items():
                        if user['style'] is not None and k in user['style']:
                            merged['style'][k] = user['style'][k]
                        else:
                            # a missing user setting component - use the default and update the file
                            changes.append(f"replaced missing setting for style[{k}] with {v}")

                    if user['style'] is not None:
                        for k, v in user['style'].items():
                            if k not in merged['style']:
                                changes.append(f'removed invalid "{k}" setting for style')
                else:
                    merged[key] = user[key]
            else:
                # a missing user setting - use the default and update the file
                changes.append(f"replaced missing setting for {key} with {value}")

        for key, value in user.items():
            if key not in merged:
                changes.append(f'removed invalid "{key}" setting')
        if changes:
            with open(cfg_path, 'w', encoding='utf-8') as fn:
                yaml.dump(merged, fn)
            logger.info(f"updated {cfg_path}: {', '.join(changes)}")

    else:
        with open(cfg_path, 'w', encoding='utf-8') as fn:
            yaml.dump(merged, fn)



    rootdir = os.path.join(ntshome, 'data')
    if not os.path.isdir(rootdir):
        os.makedirs(rootdir)
        logger.info(f"Created '{rootdir}'")
        text = prompt(f"populate {rootdir} with example data? [yN] > ")
        if text.lower().strip() == 'y':
            make_grandchild(rootdir)
            logger.info("added example data")
    import nts.nts as nts
    nts.logger = logger
    Data = nts.NodeData(rootdir)
    nts.Data = Data
    if os.path.isfile(cfg_path):
        with open(cfg_path, 'r') as fo:
            yaml_data = yaml.load(fo)
        session_edit = f"{yaml_data['edit_command']} {yaml_data['session_edit_args']}"
        nts.session_edit = session_edit
        session_add = f"{yaml_data['edit_command']} {yaml_data['session_add_args']}"
        nts.session_add = session_add
        command_edit = f"{yaml_data['edit_command']} {yaml_data['command_edit_args']}"
        nts.command_edit = command_edit
        command_add = f"{yaml_data['edit_command']} {yaml_data['command_add_args']}"
        nts.command_add = command_add
        user_style = yaml_data['style']
        style_obj = Style.from_dict(user_style)
        nts.style_obj = style_obj
        tag_sort = yaml_data.get('tag_sort', {})
        nts.tag_sort = tag_sort

    nts.main()
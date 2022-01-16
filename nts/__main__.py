#tp!/usr/bin/env python3
import sys
import os
import logging
import logging.config
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger()
from prompt_toolkit import prompt
import ruamel.yaml

# from ruamel.yaml import YAML
yaml = ruamel.yaml.YAML()
from prompt_toolkit.styles import Style
from prompt_toolkit.styles.named_colors import NAMED_COLORS
from copy import deepcopy

# for nts.yaml
default_cfg = """\
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
    status:             '#FFFFFF bg:#696969'
    status.key:         '#FFAA00'
    message:            '#FFF86F'
    not-searching:      '#888888'
# TAG SORT
# For listed keys, sort by the corresponding value. E.g. In tag view
# items with the tag "now" will be sorted as if they had the tag "!".
# Replace the keys and values with whatever you find convenient
tag_sort:
    now:        '!'
    next:       '#'
    assigned:   '%'
    someday:    '{'
    completed:  '}'
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

    tagsort_path = os.path.join(full_path, 'tagsort.txt')
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
    if os.path.isfile(cfg_path):
        with open(cfg_path, 'r') as fn:
            try:
                user = yaml.load(fn)
            except Exception as e:
                error = f"This exception was raised when loading settings:\n---\n{e}---\nPlease correct the error in {cfg_path} or remove it and restart nts.\n"
                logger.critical(error)
                sys.exit()
        changes = []
        for key, value in defaults.items():
            # if there is a user setting, use it - else use the default
            if key in user:
                if key == 'style':
                    for k, v in defaults['style'].items():
                        if k in user['style']:
                            merged['style'][k] = user['style'][k]
                        else:
                            # a missing user setting component - use the default and update the file
                            changes.append(f"replaced missing setting for style[{k}] with {v}")

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
        nts.session_edit= yaml_data['session_edit']
        nts.session_add= yaml_data['session_add']
        nts.command_edit= yaml_data['command_edit']
        nts.command_add= yaml_data['command_add']
        user_style = yaml_data['style']
        style_obj = Style.from_dict(user_style)
        nts.style_obj = style_obj
        tag_sort = yaml_data.get('tag_sort', {})
        nts.tag_sort = tag_sort

    nts.main()
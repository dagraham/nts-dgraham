#tp!/usr/bin/env python3
import sys
import os
import logging
import logging.config
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger()
from prompt_toolkit import prompt
from ruamel.yaml import YAML
yaml = YAML(typ='safe', pure=True)
from prompt_toolkit.styles import Style

# for nts.yaml
default_cfg = """\
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
    delegated:  '$'
    someday:    '}'
    completed:  '~'
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
    second

+ assigned to joe for action (delegated joe)
    In tag view, items with this tag will be sorted
    in a third group and, within that group, by the
    name to whom it was delegated

+ assigned to bob for action (delegated bob)
    In tag view, items with this tag will be sorted
    in a third group and, within that group, by the
    name to whom it was delegated

+ review from time to time for action (someday)
    In tag view, items with this tag will be sorted
    next to last

+ finished but kept for reference (completed)
    In tag view, items with this tag will be sorted
    last
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
    if not os.path.isfile(cfg_path):
        with open(cfg_path, 'w') as fo:
            fo.write(default_cfg)


    logdir = os.path.normpath(os.path.join(ntshome, 'logs'))
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    loglevel = 2 # info
    log_levels = [str(x) for x in range(1, 6)]
    if len(sys.argv) > 1 and sys.argv[1] in log_levels:
        loglevel = int(sys.argv.pop(1))

    setup_logging(loglevel, logdir)
    logger.debug(f"nts home directory: '{ntshome}'")

    rootdir = os.path.join(ntshome, 'data')
    if not os.path.isdir(rootdir):
        os.makedirs(rootdir)
        logger.info(f"Created '{rootdir}'")
        text = prompt(f"populate {rootdir} with example data? [yN] > ")
        if text.lower().strip() == 'y':
            make_grandchild(rootdir)
            logger.info("added example data")
    import nts.nts as nts
    Data = nts.NodeData(rootdir)
    nts.logger = logger
    nts.Data = Data
    if os.path.isfile(cfg_path):
        with open(cfg_path, 'r') as fo:
            yaml_data = yaml.load(fo)
        logger.debug(f"yaml_data: {yaml_data}")

        nts.session_edit= yaml_data['session_edit']
        nts.session_add= yaml_data['session_add']
        nts.command_edit= yaml_data['command_edit']
        nts.command_add= yaml_data['command_add']

        default_style = {
                'plain':        '#FFFAFA',
                'prompt':       '#FFF68F',
                'message':      '#90C57F',
                'highlight':    'bg:#FFF68F #000000',
                }

        user_style = yaml_data['style']
        style_dict = {}
        for key, value in default_style.items():
            style_dict[key] = user_style.get(key, value)
            if key not in user_style:
                logger.info(f"using default color '{value}' for class: '{key}'")
        style_obj = Style.from_dict(style_dict)
        nts.style_obj = style_obj

        tag_sort = yaml_data.get('tag_sort', {})
        nts.tag_sort = tag_sort

    nts.main()
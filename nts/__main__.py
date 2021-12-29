#!/usr/bin/env python3
import sys
import os
import logging
import logging.config
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger()
from prompt_toolkit import prompt
from ruamel.yaml import YAML
yaml = YAML(typ='safe', pure=True)

# for nts.yaml
default_cfg = """\
###################### IMPORTANT ####################################
#
# Changes to this file only take effect when nts is next # restarted.
#
#####################################################################
#
# The following are examples using the editor gvim
# edit {filepath} starting at {linenum} and wait for completion
session_edit: gvim -f +{linenum} {filepath}
#
# edit {filepath} starting at end of file without waiting for completion
command_add: gvim + {filepath}
#
# edit {filepath} starting at {linenum} without waiting for completion
command_edit: gvim +{linenum} {filepath}
#
# edit {filepath} starting at end of file and wait for completion
session_add: gvim -f + {filepath}
"""

def make_grandchild(rootdir):
    grandchild = """\
+ note a (red, green)
    The body of note a goes here

+ note b (blue, green)
    The body of note b here

+ note c (red, blue)
    And the body of note c here
"""
    full_path = rootdir
    for path in ['parent', 'child']:
        full_path = os.path.join(full_path, path)
        if not os.path.isdir(full_path):
            os.mkdir(full_path)
    full_path = os.path.join(full_path, 'grandchild.txt')
    with open(full_path, 'w') as fo:
        fo.write(grandchild)

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
    dlst = os.listdir(cwd)
    NTSHOME = os.environ.get("NTSHOME")
    if len(dlst) == 0 or ('data' in dlst and 'logs' in dlst):
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
        text = prompt(f"populate {rootdir} with grandchild example data? [yN] > ")
        if text.lower().strip() == 'y':
            make_grandchild(rootdir)
            logger.info("added grandchild example")
    import nts.nts as nts
    Data = nts.NodeData(rootdir)
    nts.logger = logger
    nts.Data = Data
    if os.path.isfile(cfg_path):
        fo = open(cfg_path, 'r')
        yaml_data = yaml.load(fo)
        fo.close()

        nts.session_edit= yaml_data['session_edit']
        nts.session_add= yaml_data['session_add']
        nts.command_edit= yaml_data['command_edit']
        nts.command_add= yaml_data['command_add']

    nts.main()
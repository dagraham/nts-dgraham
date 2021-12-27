#!/usr/bin/env python3
import sys
import os
import logging
import logging.config
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger()

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
    ntshome = os.environ.get("NTSHOME")
    print(f"NTSHOME: {ntshome}")
    ntsdir = ntshome if ntshome else os.path.join(os.path.expanduser('~'), 'nts')
    if not os.path.isdir(ntsdir):
        from prompt_toolkit import prompt
        text = prompt(f"'{ntsdir}' does not exist. Create it [yN] > ")
        if text.lower().strip() == 'y':
            os.mkdir(ntsdir)
            print(f"Created '{ntsdir}'")
        else:
            print("cancelled")
            return
    rootdir = os.path.join(ntsdir, 'data')
    if not os.path.isdir(rootdir):
        os.makedirs(rootdir)
        print(f"Created '{rootdir}'")
        text = prompt(f"populate {rootdir} with grandchild example data? [yN] > ")
        if text.lower().strip() == 'y':
            make_grandchild(rootdir)
    logdir = os.path.normpath(os.path.join(ntsdir, 'logs'))
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
        print(f"Created '{logdir}'")
    loglevel = 2 # info
    setup_logging(loglevel, logdir)
    import nts.nts as nts
    Data = nts.NodeData(rootdir)
    nts.logger = logger
    nts.Data = Data
    nts.main()
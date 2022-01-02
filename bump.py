#!/usr/bin/env python3

import pendulum
import sys, os
import logging
import logging.config
import subprocess # for check_output

logger = logging.getLogger()

from nts.__version__ import version


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

def check_output(cmd):
    if not cmd:
        return
    res = ""
    try:
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True, encoding='UTF-8')
        return True, res
    except subprocess.CalledProcessError as e:
        logger.warning(f"Error running {cmd}\n'{e.output}'")
        lines = e.output.strip().split('\n')
        msg = lines[-1]
        return False, msg


setup_logging(1, '~/nts-dgraham')

# check_output = view.check_output
ok, gb = check_output("git branch")
print('branch:')
print(gb)
ok, gs = check_output("git status -s")
if gs:
    print('status:')
    print(gs)
    print("There are uncommitted changes.")
    ans = input("Continue anyway? [yN] ")
    if not (ans and ans.lower() == "y"):
        sys.exit()

# PEP 440 extensions
# possible_extensions = ['a', 'b', 'rc', '.post', '.dev']
# For nts only the following will be used
possible_extensions = ['a', 'b', 'rc']

pre = post = version
ext = 'a'
ext_num = 1
for poss in possible_extensions:
    if poss in version:
        ext = poss
        pre, post = version.split(ext)
        print(f"pre: {pre}; post: {post}; ext: {ext}")
        if post:
            ext_num = int(post) + 1
        break

extension_options = {
        'a': {'a': f'a{ext_num}', 'b': 'b0', 'r': 'rc0'},
        'b': {'b': f'b{ext_num}', 'r': 'rc0'},
        'rc': {'r': f'rc{ext_num}'},
        }


# print(version, pre, post, ext)

new_ext = f"{pre}{ext}{ext_num}"
# print(pre)
major, minor, patch = pre.split('.')
# print(major, minor, patch)
b_patch = ".".join([major, minor, str(int(patch)+1)])
b_minor = ".".join([major, str(int(minor)+1), '0'])
b_major = ".".join([str(int(major)+1), '0', '0'])
# print(b_patch, b_minor, b_major)
# parts = pre.split('.')
# parts[-1] = str(int(parts[-1]) + 1)
# new_patch = ".".join(parts)

opts = [f'The current version is {version}']
if ext and ext in extension_options:
    i = 0
    for k, v in extension_options[ext].items():
        opts.append(f"  {k}: {pre}{v}")
    opts.append(f"  p: {b_patch}")
    opts.append(f"  n: {b_minor}")
    opts.append(f"  j: {b_major}")

import os
version_file = os.path.join(os.getcwd(), 'nts', '__version__.py')

print("\n".join(opts))
res = input(f"Which new version? ")

new_version = ''
res = res.lower()
if not res:
    print('cancelled')
    sys.exit()
bmsg = ""
if res in extension_options[ext]:
    new_version = f"{pre}{extension_options[ext][res]}"
    bmsg = "release candidate version update"
elif res == 'p':
    new_version = b_patch
    bmsg = "patch version update"
elif res == 'n':
    new_version = b_minor
    bmsg = "minor version update"
elif res == 'j':
    new_version = b_major
    bmsg = "major version update"

tplus = ""
if bmsg:
    tplus = input(f"Optional {bmsg} message:\n")

tmsg = f"Tagged version {new_version}. {tplus}"

print(f"\nThe tag message for the new version will be:\n{tmsg}\n")

ans = input(f"Commit and tag new version: {new_version}? [yN] ")
if ans.lower() != 'y':
    print('cancelled')
    sys.exit()

if new_version:
    with open(version_file, 'w') as fo:
        fo.write(f"version = '{new_version}'")
    print(f"new version: {new_version}")
    tmsg = f"Tagged version {new_version}. {tplus}"
    check_output(f"git commit -a -m '{tmsg}'")
    ok, version_info = check_output("git log --pretty=format:'%ai' -n 1")
    check_output(f"git tag -a -f '{new_version}' -m '{version_info}'")

    count = 20
    # check_output(f"echo 'Recent tagged changes as of {pendulum.now()}:' > CHANGES.txt")
    check_output(f"echo 'Recent changes as of {pendulum.now()}:' > CHANGES.txt")
    # check_output(f"git log --pretty=format:'- %ar%d %an%n    %h %ai%n%w(70,4,4)%B' --max-count={count} --no-walk --tags >> CHANGES.txt")
    check_output(f"git log --pretty=format:'- %ar%d %an%n    %h %ai%n%w(70,4,4)%B' --max-count={count} --no-walk  >> CHANGES.txt")
    check_output(f"git commit -a --amend -m '{tmsg}'")

else:
    print(f"retained version: {version}")


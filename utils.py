import os
import re
import random
import string
import shutil


class ConsoleColors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def colored_print(s, type_=None):
    s = str(s)
    if hasattr(ConsoleColors, type_):
        s = '%s%s%s' % (getattr(ConsoleColors, type_), s, ConsoleColors.ENDC)
    print(s)


def purge(dir_, pattern):
    for f in os.listdir(dir_):
        if re.search(pattern, f):
            os.remove(os.path.join(dir_, f))


def rand_string(n):
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(n)
    )


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

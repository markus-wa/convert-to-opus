import sys
import difflib
import os

from_dir = sys.argv[1]
to_dir = sys.argv[2]


def structure(directory):
    s = []
    for parent, dirs, files in sorted(os.walk(directory)):
        for file in sorted(files):
            file_base, src_ext = os.path.splitext(file)
            s += [os.path.relpath(parent + os.sep + file_base, directory) + '\n']
    return s


diff = difflib.unified_diff(structure(from_dir), structure(to_dir), fromfile=from_dir, tofile=to_dir, n=0)
sys.stdout.writelines(diff)

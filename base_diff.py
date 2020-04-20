import itertools
import sys

import configargparse
import difflib
import os
from typing import List, Set


def structure(directory: str, ignored_files: Set) -> List[str]:
    s = []
    for parent, dirs, files in sorted(os.walk(directory)):
        for file in sorted(files):
            file_base, src_ext = os.path.splitext(file)

            if os.path.basename(file) not in ignored_files:
                s.append(os.path.relpath(parent + os.sep + file_base, directory))
    return s


def parse_args():
    p = configargparse.ArgParser()
    p.add_argument('-s', '--from-dir', required=True, help='source dir')
    p.add_argument('-t', '--to-dir', required=True, help='target dir')
    p.add_argument('-i', '--ignore', action='append', default=[], help='files to exclude in the comparison (REGEXP)')
    return p.parse_args()


def diff_dirs(from_dir: str, to_dir: str, ignored_files: Set):
    diff = difflib.unified_diff(structure(from_dir, ignored_files), structure(to_dir, ignored_files), from_dir, to_dir, n=0, lineterm='')

    peek = next(diff, None)
    if peek is not None:
        for line in itertools.chain([peek], diff):
            print(line)
        return 1
    return 0


def main(cfg) -> int:
    if cfg.ignore is not None:
        ignored_files = set(cfg.ignore)
    else:
        ignored_files = None

    return diff_dirs(cfg.from_dir, cfg.to_dir, ignored_files)


if __name__ == '__main__':
    sys.exit(main(parse_args()))

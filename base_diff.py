import itertools
import sys

import difflib
import os
from typing import List


def structure(directory: str) -> List[str]:
    s = []
    for parent, dirs, files in sorted(os.walk(directory)):
        for file in sorted(files):
            file_base, src_ext = os.path.splitext(file)
            # TODO: make configurable
            if src_ext not in ['.driveupload', '.drivedownload']:
                s.append(os.path.relpath(parent + os.sep + file_base, directory))
    return s


def main(from_dir: str, to_dir: str) -> int:
    diff = difflib.unified_diff(structure(from_dir), structure(to_dir), from_dir, to_dir, n=0, lineterm='')

    peek = next(diff, None)
    if peek is not None:
        for line in itertools.chain([peek], diff):
            print(line)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(from_dir=sys.argv[1], to_dir=sys.argv[2]))

import sys
from multiprocessing import Pool

import configargparse
import json
import logging
import os
import re
from pathlib import Path
from shutil import copyfile, which
from subprocess import Popen
from typing import Callable, Dict, List, Set

SOURCE_EXTENSIONS = ['.wav', '.flac', '.ogg', '.aif']

if which('opusenc') is None:
    print("ERROR: opusenc not found in PATH - please make sure it's installed", file=sys.stderr)
    exit(1)


def opusenc(src: str, dest: str) -> None:
    if Popen(['opusenc', src, dest] + opusenc_args).wait() is 0:
        logging.info('converted "%s" -> "%s"', src, dest)
    else:
        # Fallback to copy
        # Can happen if a .ogg file is encoded as Vorbis, not FLAC
        logging.warning('Falling back to copy for %s', src)
        _, src_ext = os.path.splitext(src)
        target_base, _ = os.path.splitext(dest)
        copyfile(src, target_base + src_ext)


class Migrator(object):
    def __init__(self,
                 src_dir: str,
                 dest_dir: str,
                 threads: int = 8,
                 del_removed: bool = False,
                 opus_args: List[str] = None,
                 db: Dict[str, Dict] = None,
                 exclude_regexes: Set = None):
        if opus_args is None:
            opus_args = []
        if exclude_regexes is None:
            exclude_regexes = {}

        self.logger = logging.getLogger('migrator')

        self.source_dir = src_dir
        self.target_dir = dest_dir
        self.opusenc_args = opus_args
        self.db = db
        self.exclude_regexes = [re.compile(expr) for expr in exclude_regexes]

        if del_removed:
            self.delete_removed()

        self.extensions_to_action = {
            # Convert files with these extensions to .opus
            **{ext: self.to_opus for ext in SOURCE_EXTENSIONS},

            # Ignore files with these extensions
            # My source folder is synced with google drive and I don't want to copy google drive metadata
            # TODO: make configurable
            **{ext: lambda *args: None for ext in ['.driveupload', '.drivedownload']}
        }

        self.pool = Pool(processes=threads, initializer=init_worker, initargs=[opus_args, self.logger.level])

    def to_opus(self, src_base: str, src_ext: str) -> None:
        self.base_action(src_base, src_ext, '.opus', opusenc)

    def copy(self, src_base: str, src_ext: str) -> None:
        self.base_action(src_base, src_ext, src_ext, copyfile)

    def base_action(self, src_base: str, src_ext: str, dest_ext: str, migrate: Callable[[str, str], None]):
        dest_base = self.target_dir + os.sep + os.path.relpath(src_base, self.source_dir)
        dest_path = dest_base + dest_ext
        Path(dest_base).parent.mkdir(parents=True, exist_ok=True)
        src_path = src_base + src_ext
        if self.needs_migration(src_path, dest_path):
            self.logger.info('migrating: "%s" -> "%s"', src_path, dest_path)
            self.pool.apply_async(migrate, (src_path, dest_path,), error_callback=logging.error)

    def needs_migration(self, src_file: str, dest_file: str) -> bool:
        base_name = os.path.basename(dest_file)
        if any(p.match(base_name) for p in self.exclude_regexes):
            return False

        needs_migration = not os.path.isfile(dest_file)

        if self.db is not None:
            size = os.path.getsize(src_file)
            mod_time = os.path.getmtime(src_file)

            if src_file in self.db:
                needs_migration |= self.db[src_file]['size'] != size
                needs_migration |= self.db[src_file]['last_modified'] != mod_time
            else:
                needs_migration = True

            self.db[src_file] = {
                'size': size,
                'last_modified': mod_time,
            }

        return needs_migration

    def migrate(self):
        self.logger.info('checking for unconverted files')
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                file_base, src_ext = os.path.splitext(file)
                src_base = root + os.sep + file_base
                self.extensions_to_action.get(src_ext, self.copy)(src_base, src_ext)

        self.logger.info('finishing conversions')
        self.pool.close()
        self.pool.join()

    def delete_removed(self):
        self.logger.info('checking source files that do not exist anymore')
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                file_base, dest_ext = os.path.splitext(file)
                dest_base = root + os.sep + file_base
                dest_path = dest_base + dest_ext
                src_base = self.source_dir + os.sep + os.path.relpath(dest_base, self.target_dir)

                needs_deletion = True
                if dest_ext == ".opus":  # check for unconverted origin file
                    for ext in SOURCE_EXTENSIONS:
                        if os.path.isfile(src_base + ext):
                            needs_deletion = False
                            break
                elif os.path.isfile(src_base + dest_ext):  # check any other file types (images, etc.)
                    needs_deletion = False

                if needs_deletion:
                    self.logger.info("deleting " + dest_path + " (source file doesn't exist anymore)")
                    os.remove(dest_path)
                    if self.db is not None:
                        if dest_ext == ".opus":
                            for ext in SOURCE_EXTENSIONS:  # this (fishing for dict key) could be better
                                if self.db.get(src_base + ext) is not None:
                                    del self.db[src_base + ext]
                        elif self.db.get(file) is not None:
                            del self.db[file]
                    continue

        for root, dirs, _ in os.walk(self.target_dir):  # check for empty dirs AFTER it deleted all possible files
            for directory in dirs:
                dir_path = root + os.sep + directory
                if not os.listdir(dir_path):
                    self.logger.info("deleting " + dir_path + " (empty directory)")
                    os.rmdir(dir_path)


def parse_args():
    p = configargparse.ArgParser()
    p.add_argument('-c', '--config', is_config_file=True, help='config file path')
    p.add_argument('-s', '--source', required=True, help='path to source directory')
    p.add_argument('-t', '--target', required=True, help='path to target directory')
    p.add_argument('-thr', '--threads', metavar="COUNT", help='thread count for parallel processing')
    p.add_argument('-del', '--del-removed', action='store_true',
                   help='delete converted opus files, for which source files do not exist anymore')
    p.add_argument('-a', '--opusenc-args', action='append', default=[],
                   help='arguments to pass to opusenc. '
                        '(see https://mf4.xiph.org/jenkins/view/opus/job/opus-tools/ws/man/opusenc.html)')
    p.add_argument('-db', '--database', help='path to the database file')
    p.add_argument('-v', '--verbose', action='store_true', help='print debug information')
    p.add_argument('-x', '--exclude', action='append', default=[],
                   help='files (Python REGEX) to exclude in the migration. '
                   'see https://docs.python.org/3/howto/regex.html')

    options = p.parse_args()

    # to avoid configargparse misinterpreting the opusenc-args values we need to use single quotes around them
    options.opusenc_args = list(map(lambda arg: arg.replace("'", ''), options.opusenc_args))

    return options


def init_worker(opus_args: List[str], log_level: int):
    global opusenc_args
    opusenc_args = opus_args
    configure_logging(log_level)


def configure_logging(log_level: int):
    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=log_level,
        datefmt='%Y-%m-%d %H:%M:%S')


def main(cfg):
    log_level = {
        True: logging.DEBUG,
        False: logging.INFO,
    }[cfg.verbose]
    configure_logging(log_level)

    logging.debug('config: %s', cfg)

    if cfg.threads is not None:
        cfg.threads = int(cfg.threads)

    if cfg.database is not None:
        if os.path.exists(cfg.database):
            with open(cfg.database, 'r') as f:
                db: Dict[str, Dict] = json.load(f)
        else:
            db = {}
    else:
        db = None

    if cfg.exclude is not None:
        exclude = set(cfg.exclude)
    else:
        exclude = None

    Migrator(cfg.source, cfg.target, cfg.threads, cfg.del_removed, cfg.opusenc_args, db, exclude).migrate()

    if db is not None:
        logging.info('updating db file')
        with open(cfg.database, 'w') as f:
            f.write(json.dumps(db))


if __name__ == '__main__':
    main(parse_args())

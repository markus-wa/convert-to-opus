import sys
from multiprocessing import Pool

import configargparse
import json
import logging
import os
from pathlib import Path
from shutil import copyfile, which
from subprocess import Popen
from typing import Callable, Dict, List

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
                 opus_args: List[str] = None,
                 db: Dict[str, Dict] = None):
        if opus_args is None:
            opus_args = []

        self.logger = logging.getLogger('migrator')

        self.source_dir = src_dir
        self.target_dir = dest_dir
        self.opusenc_args = opus_args
        self.db = db

        self.extensions_to_action = {
            # Convert files with these extensions to .opus
            **{ext: self.to_opus for ext in ['.wav', '.flac', '.ogg', '.aif']},

            # Ignore files with these extensions
            # My source folder is synced with google drive and I don't want to copy google drive metadata
            # TODO: make configurable
            **{ext: lambda *args: None for ext in ['.driveupload', '.drivedownload']}
        }

        self.pool = Pool(processes=8, initializer=init_worker, initargs=[opus_args, self.logger.level])

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


def parse_args():
    p = configargparse.ArgParser()
    p.add_argument('-c', '--config', is_config_file=True, help='config file path')
    p.add_argument('-s', '--source', required=True, help='path to source directory')
    p.add_argument('-t', '--target', required=True, help='path to target directory')
    p.add_argument('--opusenc-args', action='append', default=[],
                   help='arguments to pass to opusenc (see '
                        'https://mf4.xiph.org/jenkins/view/opus/job/opus-tools/ws/man/opusenc.html)')
    p.add_argument('-db', '--database', help='path to the database file')
    p.add_argument('-v', '--verbose', action='store_true', help='print debug information')

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

    if cfg.database is not None:
        if os.path.exists(cfg.database):
            with open(cfg.database, 'r') as f:
                db: Dict[str, Dict] = json.load(f)
        else:
            db = {}
    else:
        db = None

    Migrator(cfg.source, cfg.target, cfg.opusenc_args, db).migrate()

    if db is not None:
        logging.info('updating db file')
        with open(cfg.database, 'w') as f:
            f.write(json.dumps(db))


if __name__ == '__main__':
    main(parse_args())

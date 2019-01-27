import sys
import unittest

import os
import shutil

import base_diff
import to_opus

test_dir = os.path.dirname(os.path.realpath(__file__))
source_dir = test_dir + os.sep + 'source'
target_dir = test_dir + os.sep + 'target'
golden_dir = test_dir + os.sep + 'golden'

db_empty = test_dir + os.sep + 'db_empty.json'
db_empty_tmp = db_empty + '.tmp'
db_full = test_dir + os.sep + 'db_full.json'
db_full_tmp = db_full + '.tmp'
db_nonexistent = test_dir + os.sep + 'db_nonexistent.json'


class MicroMock(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def clean_up():
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    if os.path.exists(db_empty_tmp):
        os.remove(db_empty_tmp)
    if os.path.exists(db_full_tmp):
        os.remove(db_full_tmp)
    if os.path.exists(db_nonexistent):
        os.remove(db_nonexistent)


class TestToOpus(unittest.TestCase):

    def setUp(self):
        clean_up()
        shutil.copyfile(db_empty, db_empty_tmp)
        shutil.copyfile(db_full, db_full_tmp)

    def tearDown(self):
        clean_up()

    def test_main(self):
        to_opus.main(MicroMock(
            source=source_dir,
            target=target_dir,
            verbose=True,
            opusenc_args=[],
            database=None
        ))

        self.assertEqual(0, base_diff.main(source_dir, target_dir))

    def test_main_db_empty(self):
        to_opus.main(MicroMock(
            source=source_dir,
            target=target_dir,
            verbose=True,
            opusenc_args=[],
            database=db_empty_tmp
        ))

        self.assertEqual(0, base_diff.main(source_dir, target_dir))

    def test_main_db_full(self):
        to_opus.main(MicroMock(
            source=source_dir,
            target=target_dir,
            verbose=True,
            opusenc_args=[],
            database=db_full_tmp
        ))

        self.assertEqual(0, base_diff.main(source_dir, target_dir))

    def test_main_db_nonexistent(self):
        to_opus.main(MicroMock(
            source=source_dir,
            target=target_dir,
            verbose=True,
            opusenc_args=[],
            database=db_nonexistent
        ))

        self.assertEqual(0, base_diff.main(source_dir, target_dir))

    def test_parse_args_min(self):
        sys.argv = [
            'cmd',
            '-s', '/path/to/src',
            '-t', '/path/to/out',
        ]

        cfg = to_opus.parse_args()

        self.assertEqual('/path/to/src', cfg.source)
        self.assertEqual('/path/to/out', cfg.target)
        self.assertEqual(False, cfg.verbose)
        self.assertEqual([], cfg.opusenc_args)

    def test_parse_args_full(self):
        sys.argv = [
            'cmd',
            '-s', '/path/to/src',
            '-t', '/path/to/out',
            '-v',
            '--opusenc-args', "'--cvbr'",
            '--opusenc-args', "'--quiet'",
        ]

        cfg = to_opus.parse_args()

        self.assertEqual('/path/to/src', cfg.source)
        self.assertEqual('/path/to/out', cfg.target)
        self.assertEqual(True, cfg.verbose)
        self.assertEqual(['--cvbr', '--quiet'], cfg.opusenc_args)

    def test_parse_cfg_min(self):
        sys.argv = [
            'cmd',
            '-c', test_dir + '/cfg_min.txt',
        ]

        cfg = to_opus.parse_args()

        self.assertEqual('/path/to/src', cfg.source)
        self.assertEqual('/path/to/out', cfg.target)
        self.assertEqual(False, cfg.verbose)
        self.assertEqual([], cfg.opusenc_args)

    def test_parse_cfg_full(self):
        sys.argv = [
            'cmd',
            '-c', test_dir + '/cfg_full.txt',
        ]

        cfg = to_opus.parse_args()

        self.assertEqual('/path/to/src', cfg.source)
        self.assertEqual('/path/to/out', cfg.target)
        self.assertEqual(True, cfg.verbose)
        self.assertEqual(['--cvbr', '--quiet'], cfg.opusenc_args)

    def test_needs_migration_unmigrated(self):
        mig = to_opus.Migrator(source_dir, target_dir)

        self.assertEqual(True,
                         mig.needs_migration(source_dir + os.sep + 'wave.wav', target_dir + os.sep + 'wave.opus'))

    def test_needs_migration_no_db_migrated(self):
        mig = to_opus.Migrator(source_dir, target_dir)

        self.assertEqual(False,
                         mig.needs_migration(source_dir + os.sep + 'wave.wav', golden_dir + os.sep + 'wave.opus'))

    def test_needs_migration_db_no_entry(self):
        mig = to_opus.Migrator(source_dir, target_dir, db={})

        self.assertEqual(True, mig.needs_migration(source_dir + os.sep + 'wave.wav', golden_dir + os.sep + 'wave.opus'))

    def test_needs_migration_db_wrongsize(self):
        src_file = source_dir + os.sep + 'wave.wav'
        db = {src_file: {'size': 1, 'last_modified': os.path.getmtime(src_file)}}

        mig = to_opus.Migrator(source_dir, target_dir, db=db)

        self.assertEqual(True, mig.needs_migration(src_file, golden_dir + os.sep + 'wave.opus'))

    def test_needs_migration_db_old_modification_date(self):
        src_file = source_dir + os.sep + 'wave.wav'
        db = {src_file: {'size': 94182, 'last_modified': 123}}

        mig = to_opus.Migrator(source_dir, target_dir, db=db)

        self.assertEqual(True, mig.needs_migration(src_file, golden_dir + os.sep + 'wave.opus'))

    def test_needs_migration_db_migrated(self):
        src_file = source_dir + os.sep + 'wave.wav'
        db = {src_file: {'size': 94182, 'last_modified': os.path.getmtime(src_file)}}

        mig = to_opus.Migrator(source_dir, target_dir, db=db)

        self.assertEqual(False, mig.needs_migration(src_file, golden_dir + os.sep + 'wave.opus'))


if __name__ == '__main__':
    unittest.main()

import unittest

import os

import base_diff

tests_dir = os.path.dirname(os.path.realpath(__file__))
source_dir = tests_dir + '/source'
golden_dir = tests_dir + '/golden'


class TestBaseDiff(unittest.TestCase):

    def test_structure(self):
        actual = base_diff.structure(source_dir)

        expected = [
            'aifc',
            'aiff',
            'flac-ogg',
            'flac',
            'opus',
            'vorbis',
            'wave',
            'nested' + os.sep + 'text',
            'nested' + os.sep + 'deep' + os.sep + 'aifc',
            'nested' + os.sep + 'deep' + os.sep + 'aiff',
            'nested' + os.sep + 'deep' + os.sep + 'flac-ogg',
            'nested' + os.sep + 'deep' + os.sep + 'flac',
            'nested' + os.sep + 'deep' + os.sep + 'opus',
            'nested' + os.sep + 'deep' + os.sep + 'vorbis',
            'nested' + os.sep + 'deep' + os.sep + 'wave',
        ]
        self.assertEqual(expected, actual)

    def test_main_same(self):
        exit_code = base_diff.main(source_dir, golden_dir)

        self.assertEqual(0, exit_code)

    def test_main_diff(self):
        exit_code = base_diff.main(source_dir, source_dir + '/nested')

        self.assertEqual(1, exit_code)


if __name__ == '__main__':
    unittest.main()

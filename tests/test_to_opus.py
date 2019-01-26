import unittest

import os

import base_diff
import to_opus

test_dir = os.path.dirname(os.path.realpath(__file__))
source_dir = test_dir + '/source'
target_dir = test_dir + '/target'


class TestToOpus(unittest.TestCase):

    def test_main(self):
        to_opus.main(source_dir, target_dir)

        self.assertEqual(0, base_diff.main(source_dir, target_dir))


if __name__ == '__main__':
    unittest.main()

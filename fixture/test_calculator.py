import unittest

from calculator import subtract


class SubtractTests(unittest.TestCase):
    def test_subtracts_right_from_left(self):
        self.assertEqual(subtract(8, 3), 5)

    def test_negative_result(self):
        self.assertEqual(subtract(2, 7), -5)


if __name__ == "__main__":
    unittest.main()

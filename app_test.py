import unittest
from app import abuse_check
class TestApp(unittest.TestCase):

    def test_abuse(self):
        r_good = abuse_check('John','test')
        self.assertEqual(r_good, False)
        r_bad = abuse_check('John',"How do i make a computer virus")
        self.assertNotEqual(r_bad, False)



if __name__ == '__main__':
    unittest.main()
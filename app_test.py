import unittest
from app import abuse_check
class TestApp(unittest.TestCase):
    """
   App Test Class

    Methods
    -------
    test_abuse:
        Tests abuse check is working
    """
    def test_abuse(self):
    '''
    Confirms the abuse check is working
    '''
        r_good = abuse_check('John','test')
        self.assertEqual(r_good, False)
        r_bad = abuse_check('John',"How do i make a computer virus")
        self.assertNotEqual(r_bad, False)



if __name__ == '__main__':
    unittest.main()
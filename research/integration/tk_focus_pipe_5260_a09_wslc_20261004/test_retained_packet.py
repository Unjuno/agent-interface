import unittest
from verify_packet import check_packet


class RetainedTests(unittest.TestCase):
    def test_actual_saved_packet_is_verified_without_gui_replay(self):
        result=check_packet()
        self.assertEqual(result['errors'],[],result)
        self.assertEqual(result['status'],'PASS_RETAINED_FINITE_FIXTURE_ONLY')


if __name__=='__main__':unittest.main()

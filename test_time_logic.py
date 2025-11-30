import unittest
from datetime import datetime, timedelta
from main import parse_relative_time, is_within_time_window, TIME_WINDOW_MINUTES

class TestTimeLogic(unittest.TestCase):
    def test_parse_relative_time(self):
        now = datetime.now()
        
        # Test seconds
        t = parse_relative_time("30s")
        dt = datetime.fromisoformat(t)
        diff = now - dt
        self.assertTrue(timedelta(seconds=29) <= diff <= timedelta(seconds=31))
        
        # Test minutes
        t = parse_relative_time("45m")
        dt = datetime.fromisoformat(t)
        diff = now - dt
        self.assertTrue(timedelta(minutes=44) <= diff <= timedelta(minutes=46))
        
        # Test hours
        t = parse_relative_time("2h")
        dt = datetime.fromisoformat(t)
        diff = now - dt
        self.assertTrue(timedelta(hours=1, minutes=59) <= diff <= timedelta(hours=2, minutes=1))

    def test_is_within_time_window(self):
        now = datetime.now()
        
        # Recent time (30 mins ago)
        recent = (now - timedelta(minutes=30)).isoformat()
        self.assertTrue(is_within_time_window(recent, 60))
        
        # Borderline time (59 mins ago)
        borderline = (now - timedelta(minutes=59)).isoformat()
        self.assertTrue(is_within_time_window(borderline, 60))
        
        # Old time (61 mins ago)
        old = (now - timedelta(minutes=61)).isoformat()
        self.assertFalse(is_within_time_window(old, 60))
        
        # Very old time (24 hours ago)
        very_old = (now - timedelta(hours=24)).isoformat()
        self.assertFalse(is_within_time_window(very_old, 60))

if __name__ == '__main__':
    print(f"Testing with TIME_WINDOW_MINUTES = {TIME_WINDOW_MINUTES}")
    unittest.main()

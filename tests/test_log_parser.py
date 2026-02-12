import unittest
from src.services.log_parser import LogParser

class TestLogParser(unittest.TestCase):

    def setUp(self):
        self.log_parser = LogParser()

    def test_parse_log_line(self):
        log_line = '2023-10-01T12:00:00Z GET /api/v4/projects 200 1234 "Mozilla/5.0"'
        expected_output = {
            'access_time': '2023-10-01T12:00:00Z',
            'http_method': 'GET',
            'api_path': '/api/v4/projects',
            'http_status': 200,
            'response_size': 1234,
            'user_agent': 'Mozilla/5.0'
        }
        result = self.log_parser.parse_log_line(log_line)
        self.assertEqual(result, expected_output)

    def test_parse_log_file(self):
        log_file_path = 'path/to/gitlab_access.log'  # Update with the actual path for testing
        parsed_data = self.log_parser.parse_log_file(log_file_path)
        self.assertIsInstance(parsed_data, list)
        self.assertGreater(len(parsed_data), 0)

if __name__ == '__main__':
    unittest.main()
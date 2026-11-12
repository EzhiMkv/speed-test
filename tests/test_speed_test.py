import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speed_test import error_reason, format_bytes, format_seconds, parse_args


class FormatBytesTests(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(format_bytes(950), "950 Б")

    def test_kilobytes(self):
        self.assertEqual(format_bytes(1000), "1.00 КБ")

    def test_megabytes(self):
        self.assertEqual(format_bytes(1_048_576), "1.05 МБ")

    def test_gigabytes(self):
        self.assertEqual(format_bytes(1_500_000_000), "1.50 ГБ")


class FormatSecondsTests(unittest.TestCase):
    def test_milliseconds(self):
        self.assertEqual(format_seconds(0.02), "20 мс")

    def test_seconds(self):
        self.assertEqual(format_seconds(2.5), "2.50 с")


class ErrorReasonTests(unittest.TestCase):
    def test_http_error(self):
        exc = urllib.error.HTTPError("http://example.com", 404, "Not Found", None, None)
        self.assertEqual(error_reason(exc), "HTTP 404")

    def test_url_error_with_reason(self):
        exc = urllib.error.URLError(OSError("Connection refused"))
        self.assertEqual(error_reason(exc), "Connection refused")


class ParseArgsTests(unittest.TestCase):
    def test_defaults(self):
        args = parse_args(["https://example.com/file"])
        self.assertEqual(args.count, 10)
        self.assertEqual(args.timeout, 30)

    def test_explicit_options(self):
        args = parse_args(["-n", "3", "--timeout", "5", "http://example.com/f"])
        self.assertEqual(args.count, 3)
        self.assertEqual(args.timeout, 5)

    def test_rejects_bad_count(self):
        with self.assertRaises(SystemExit):
            parse_args(["-n", "0", "https://example.com/f"])

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(SystemExit):
            parse_args(["ftp://example.com/f"])

    def test_rejects_missing_scheme(self):
        with self.assertRaises(SystemExit):
            parse_args(["example.com/f"])


if __name__ == "__main__":
    unittest.main()

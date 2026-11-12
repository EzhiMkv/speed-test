import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speed_test import (
    error_reason,
    format_bytes,
    format_seconds,
    parse_args,
    percentile,
    request_row,
)


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


class PercentileTests(unittest.TestCase):
    def test_median_odd(self):
        self.assertEqual(percentile([5, 1, 3], 50), 3)

    def test_median_even_interpolates(self):
        self.assertEqual(percentile([1, 2, 3, 4], 50), 2.5)

    def test_p95_interpolates(self):
        self.assertEqual(percentile([float(i) for i in range(1, 11)], 95), 9.55)

    def test_single_value(self):
        self.assertEqual(percentile([7], 50), 7)


class RequestRowTests(unittest.TestCase):
    def test_row_fields(self):
        row = request_row("прогрев:", 1.0, 1_000_000)
        self.assertTrue(row.startswith("  прогрев:"))
        self.assertIn("1.00 с", row)
        self.assertIn("1.00 МБ", row)
        self.assertIn("8.00 Мбит/с", row)


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

    def test_no_warmup_flag(self):
        self.assertFalse(parse_args(["https://example.com/f"]).no_warmup)
        self.assertTrue(parse_args(["--no-warmup", "https://example.com/f"]).no_warmup)


if __name__ == "__main__":
    unittest.main()

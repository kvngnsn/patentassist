"""Offline tests for scripts/normalize_number.py."""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

from normalize_number import fetch_candidates, kindless, normalize, run  # noqa: E402

# input -> (canonical, doc_type, display, ambiguous)
TABLE = [
    ("US 9,457,709 B2", "US9457709B2", "patent", "US 9,457,709 B2", False),
    ("9457709", "US9457709", "patent", "US 9,457,709", True),
    ("US20160144773A1", "US20160144773A1", "application_pub", "US 2016/0144773 A1", False),
    ("US 2016/0144773 A1", "US20160144773A1", "application_pub", "US 2016/0144773 A1", False),
    ("16/123,456", "US16/123,456", "application_no", "16/123,456", False),
    ("EP1234567B1", "EP1234567B1", "patent", "EP 1 234 567 B1", False),
    ("EP1234567A1", "EP1234567A1", "application_pub", "EP 1 234 567 A1", False),
    ("WO2019/123456", "WO2019123456", "application_pub", "WO 2019/123456", False),
    ("WO2019123456A1", "WO2019123456A1", "application_pub", "WO 2019/123456 A1", False),
    ("CN109123456A", "CN109123456A", "application_pub", "CN 109123456 A", False),
    ("JP2019123456A", "JP2019123456A", "application_pub", "JP 2019-123456 A", False),
    ("KR1020190012345A", "KR1020190012345A", "application_pub", "KR 10-2019-0012345 A", False),
    ("RE45,123", "USRE45123", "reissue", "US RE45,123", False),
    ("D876,543", "USD876543", "design", "US D876,543", False),
    ("PP12,345", "USPP12345", "plant", "US PP12,345", False),
    ("USRE45123E1", "USRE45123E1", "reissue", "US RE45,123 E1", False),
    ("USD876543S1", "USD876543S1", "design", "US D876,543 S1", False),
    ("USPP12345P2", "USPP12345P2", "plant", "US PP12,345 P2", False),
    ("U.S. Pat. No. 9,457,709", "US9457709", "patent", "US 9,457,709", True),
    ("US-9457709-B2", "US9457709B2", "patent", "US 9,457,709 B2", False),
    ("us9457709b2", "US9457709B2", "patent", "US 9,457,709 B2", False),
    ("US 11,234,567 B2", "US11234567B2", "patent", "US 11,234,567 B2", False),
    ("5093563", "US5093563A", "patent", "US 5,093,563 A", False),
    ("WO 99/12345", "WO1999012345", "application_pub", "WO 1999/012345", False),
    ("PCT/US2019/012345", "PCT/US2019/012345", "application_no", "PCT/US2019/012345", False),
    ("63/123,456", "US63/123,456", "application_no", "63/123,456", False),
    ("EP19123456.7", "EP19123456.7", "application_no", "EP 19123456.7", False),
    ("JP2019-123456", "JP2019-123456", "application_no", "JP 2019-123456", False),
    ("KR10-2019-0012345", "KR10-2019-0012345", "application_no", "KR 10-2019-0012345", False),
    ("CN201910123456.7", "CN201910123456.7", "application_no", "CN 201910123456.7", False),
    ("EP 3 456 789 B1", "EP3456789B1", "patent", "EP 3 456 789 B1", False),
    ("2016/144773", "US20160144773", "application_pub", "US 2016/0144773", False),
    ("U.S. Patent Application Publication No. 2016/0144773", "US20160144773", "application_pub",
     "US 2016/0144773", False),
    ("Application Ser. No. 16/123,456", "US16/123,456", "application_no", "16/123,456", False),
    ("JP6789012B2", "JP6789012B2", "patent", "JP 6789012 B2", False),
    ("KR102123456B1", "KR102123456B1", "patent", "KR 102123456 B1", False),
    ("16123456", "US16/123,456", "application_no", "16/123,456", False),
]


class TestNormalizeTable(unittest.TestCase):
    def test_table(self):
        self.assertGreaterEqual(len(TABLE), 25)
        for raw, canon, doc, disp, amb in TABLE:
            with self.subTest(raw=raw):
                r = normalize(raw)
                self.assertTrue(r["ok"], r)
                self.assertEqual(r["canonical"], canon)
                self.assertEqual(r["doc_type"], doc)
                self.assertEqual(r["display"], disp)
                self.assertEqual(r["ambiguous"], amb)

    def test_bare_us_candidates_b2_then_b1(self):
        r = normalize("9457709")
        self.assertTrue(r["ambiguous"])
        self.assertEqual([c["canonical"] for c in r["candidates"]][:2], ["US9457709B2", "US9457709B1"])
        self.assertEqual(r["google_patents_url"], "https://patents.google.com/patent/US9457709/en")

    def test_eight_digit_in_patent_range_lists_application_reading(self):
        r = normalize("11234567")
        self.assertTrue(r["ambiguous"])
        kinds = [c["doc_type"] for c in r["candidates"]]
        self.assertIn("patent", kinds)
        self.assertIn("application_no", kinds)

    def test_kindless_ep_is_ambiguous_between_pub_and_grant(self):
        r = normalize("EP1000000")
        self.assertTrue(r["ambiguous"])
        self.assertEqual({c["doc_type"] for c in r["candidates"]}, {"patent", "application_pub"})

    def test_urls(self):
        self.assertEqual(normalize("US 9,457,709 B2")["google_patents_url"],
                         "https://patents.google.com/patent/US9457709B2/en")
        self.assertIsNone(normalize("16/123,456")["google_patents_url"])

    def test_garbage(self):
        self.assertFalse(normalize("hello")["ok"])
        self.assertFalse(normalize("")["ok"])

    def test_fetch_candidates_and_kindless(self):
        self.assertEqual(fetch_candidates(normalize("US9457709B2")), ["US9457709B2"])
        c = fetch_candidates(normalize("9457709"))
        self.assertEqual(c[0], "US9457709")
        self.assertIn("US9457709B1", c)
        self.assertEqual(fetch_candidates(normalize("16/123,456")), [])
        self.assertEqual(kindless("US20160144773A1"), "US20160144773")
        self.assertEqual(kindless("USRE45123E1"), "USRE45123")

    def test_batch_stdin(self):
        res = run({"numbers": [], "stdin_text": "US9457709B2\n# comment\n\nWO2019/123456\nnot a number\n"})
        self.assertEqual(len(res["results"]), 3)
        self.assertEqual(res["summary"]["unparsed"], 1)
        self.assertEqual(res["exit_code"], 2)


if __name__ == "__main__":
    unittest.main()


class TestJapaneseEraNumbers(unittest.TestCase):
    """Google Patents prints pre-2000 JP numbers with an era letter (found dogfooding: both were
    rejected, one with the wrong message 'prefix H is only used for US documents')."""

    def test_showa_and_heisei(self):
        r = normalize("JPS62195890A")
        self.assertTrue(r["ok"])
        self.assertEqual((r["country"], r["canonical"], r["doc_type"]), ("JP", "JPS62195890A", "application_pub"))
        r = normalize("JPH0570913B2")
        self.assertTrue(r["ok"])
        self.assertEqual((r["canonical"], r["doc_type"]), ("JPH0570913B2", "patent"))
        self.assertIn("JPH0570913B2", r["google_patents_url"])

    def test_us_h_prefix_still_us(self):
        r = normalize("H1234")
        self.assertEqual(r["country"], "US")

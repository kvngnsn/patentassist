"""Offline tests for the Google Patents parser in scripts/patent_fetch.py (real saved pages)."""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

from patent_fetch import deps_from_text, fetch_one, find_cached, parse_google_html  # noqa: E402
from state import write_json  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "search")


def load(name):
    with open(os.path.join(FIX, name + ".html"), encoding="utf-8") as fh:
        return parse_google_html(fh.read(), requested=name)


class TestGrantParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = load("US9457709B2")

    def test_identity(self):
        r = self.r
        self.assertEqual(r["schema"], "patentassist/patent@1")
        self.assertEqual(r["number"], "US9457709B2")
        self.assertEqual((r["country"], r["kind"], r["doc_type"]), ("US", "B2", "patent"))
        self.assertEqual(r["title"], "Bicycle helmet with an adaptive light notification system that varies brightness")
        self.assertTrue(r["abstract"].startswith("An adaptive light notification system"))

    def test_dates(self):
        r = self.r
        self.assertEqual(r["priority_date"], "2014-11-26")
        self.assertEqual(r["filing_date"], "2014-11-26")
        self.assertEqual(r["publication_date"], "2016-10-04")
        self.assertEqual(r["grant_date"], "2016-10-04")
        self.assertEqual(r["expiration"], "2035-03-20")
        self.assertEqual(r["legal_status"], "Expired - Fee Related")

    def test_parties_and_numbers(self):
        r = self.r
        self.assertEqual(r["inventors"], ["Reem Jafar ALATAAS"])
        self.assertEqual(r["assignees"], ["Individual"])
        self.assertEqual(r["application_number"], "US14/554,357")
        self.assertEqual(r["family"], ["US20160144773A1"])
        self.assertEqual(r["cpc"][0], "B60Q1/2676")
        self.assertIn("A42B3/0453", r["cpc"])

    def test_claims(self):
        c = self.r["claims"]
        self.assertEqual(len(c), 20)
        self.assertEqual(self.r["claim_count"], 20)
        self.assertTrue(c[0]["independent"])
        self.assertTrue(c[0]["text"].startswith("1. An adaptive light notification system, comprising:"))
        self.assertIn("a head protection enclosure that ensures protection of a head;", c[0]["text"])
        self.assertEqual(c[1]["depends_on"], [1])
        self.assertEqual(c[2]["depends_on"], [2])
        self.assertEqual(c[3]["depends_on"], [2])
        indep = [x["num"] for x in c if x["independent"]]
        self.assertIn(1, indep)
        self.assertGreaterEqual(len(indep), 2)

    def test_description_labels_synthesized_for_grant(self):
        d = self.r["description"]
        self.assertEqual(len(d), 58)
        self.assertEqual(self.r["paragraph_labels"], "synthesized")
        self.assertEqual(d[0]["label"], "p1")
        self.assertEqual(d[0]["heading"], "GRANT OF NON-EXCLUSIVE RIGHT")
        self.assertTrue(any("column:line" in n for n in self.r["notes"]))

    def test_citations(self):
        cit = self.r["citations"]
        back = [x["number"] for x in cit["backward"]]
        self.assertEqual(len(back), 5)
        self.assertIn("EP0185922A2", back)
        self.assertIn("US7264368B2", back)
        ep = [x for x in cit["backward"] if x["number"] == "EP0185922A2"][0]
        self.assertEqual(ep["date"], "1986-07-02")
        self.assertEqual(ep["assignee"], "Michael Slarve")
        self.assertGreaterEqual(len(cit["forward"]), 10)
        self.assertTrue(any(x["examiner"] for x in cit["forward"]))
        self.assertFalse(all(x["examiner"] for x in cit["forward"]))
        self.assertEqual(len(cit["npl"]), 6)


class TestPublicationParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = load("US20160144773A1")

    def test_identity_and_dates(self):
        r = self.r
        self.assertEqual((r["number"], r["kind"], r["doc_type"]), ("US20160144773A1", "A1", "application_pub"))
        self.assertEqual(r["publication_date"], "2016-05-26")
        self.assertIsNone(r["grant_date"])
        self.assertEqual(r["family"], ["US9457709B2"])

    def test_printed_paragraph_labels(self):
        d = self.r["description"]
        self.assertEqual(self.r["paragraph_labels"], "printed")
        self.assertEqual(d[0]["label"], "[0001]")
        self.assertEqual(d[0]["pid"], "p0001")
        self.assertEqual(d[-1]["label"], "[0058]")
        labels = [x["label"] for x in d]
        self.assertEqual(len(labels), len(set(labels)))

    def test_claims_with_bold_numbers(self):
        c = self.r["claims"]
        self.assertEqual(len(c), 20)
        self.assertTrue(c[0]["text"].startswith("1. An adaptive"))
        self.assertEqual(c[4]["depends_on"], [1])

    def test_examiner_marker_on_forward(self):
        fw = self.r["citations"]["forward"]
        kol = [x for x in fw if x["number"] == "US20160113345A1"]
        self.assertTrue(kol and kol[0]["examiner"])


class TestEPParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = load("EP1000000B1")

    def test_basic(self):
        r = self.r
        self.assertEqual((r["number"], r["country"], r["kind"], r["doc_type"]), ("EP1000000B1", "EP", "B1", "patent"))
        self.assertEqual(r["title"], "Apparatus for manufacturing green bricks for the brick manufacturing industry")
        self.assertEqual(r["priority_date"], "1998-11-12")
        self.assertEqual(r["filing_date"], "1999-11-08")
        self.assertEqual(r["grant_date"], "2003-02-12")
        self.assertEqual(r["assignees"], ["Beheermaatschappij De Boer Nijmegen BV"])
        self.assertIn("EP1000000A1", r["family"])
        self.assertIn("US6093011A", r["family"])

    def test_claims_dependencies_from_text(self):
        c = self.r["claims"]
        self.assertEqual(len(c), 11)
        self.assertTrue(c[0]["text"].startswith("1. Apparatus for manufacturing green bricks"))
        self.assertEqual(c[1]["depends_on"], [1])
        self.assertEqual(c[2]["depends_on"], [1, 2])          # "claim 1 or 2"
        self.assertEqual(c[3]["depends_on"], [1, 2, 3])       # "any of the foregoing claims"

    def test_paragraph_labels_from_ids(self):
        d = self.r["description"]
        self.assertEqual(self.r["paragraph_labels"], "printed")
        self.assertEqual(d[0]["label"], "[0001]")
        self.assertIn("green bricks", d[0]["text"])


class TestDepsFromText(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(deps_from_text("The method of claim 3, wherein", 4), [3])
        self.assertEqual(deps_from_text("Apparatus according to claims 1 to 3, wherein", 5), [1, 2, 3])
        self.assertEqual(deps_from_text("Device as in any one of claims 2-4 or 6", 7), [2, 3, 4, 6])
        self.assertEqual(deps_from_text("A system comprising a widget", 1), [])
        self.assertEqual(deps_from_text("Use as claimed in any of the preceding claims", 3), [1, 2])


class TestCacheLookupOffline(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "cache"))
        write_json(os.path.join(self.d, "cache", "US9457709B2.json"), load("US9457709B2"))

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_kindless_hits_cache(self):
        p, rec = find_cached(self.d, "9457709")
        self.assertTrue(p.endswith("US9457709B2.json"))
        r = fetch_one("US 9,457,709", self.d, offline=True, no_audit=True)
        self.assertEqual(r["status"], "cached")
        self.assertEqual(r["canonical"], "US9457709B2")

    def test_offline_miss(self):
        r = fetch_one("US20160144773A1", self.d, offline=True, no_audit=True)
        self.assertEqual(r["status"], "not_cached")

    def test_application_number_rejected(self):
        r = fetch_one("16/123,456", self.d, offline=True, no_audit=True)
        self.assertEqual(r["status"], "bad_input")


if __name__ == "__main__":
    unittest.main()


class TestTranslatedClaims(unittest.TestCase):
    """Google's translated pages mark claims as a bare <claim num=..> element with the source text
    in a google-src-text span (found dogfooding EP0944293A1: 8 claims listed, 0 parsed)."""

    HTML = (
        '<html><head><title>EP0944293A1 - Verfahren - Google Patents</title></head><body>'
        '<span itemprop="publicationNumber">EP0944293A1</span>'
        '<section itemprop="claims" itemscope><h2>Claims (<span itemprop="count">2</span>)</h2>'
        '<aside>Translated from <span itemprop="translatedLanguage">German</span></aside>'
        '<div itemprop="content" html><claims lang="EN" load-source="google">'
        '<claim num="1"><claim-text><span class="notranslate"> <span class="google-src-text">'
        'Verfahren zur Ermittlung</span>Method for determining the boiling point.</span></claim-text></claim>'
        '<claim num="2"><claim-text><span class="notranslate"> <span class="google-src-text">'
        'Verfahren nach Anspruch 1</span>Method according to claim 1, wherein a microphone is used.</span>'
        '</claim-text></claim></claims></div></section></body></html>')

    def test_bare_claim_elements_parsed_without_source_text(self):
        r = parse_google_html(self.HTML, requested="EP0944293A1")
        self.assertEqual(len(r["claims"]), 2)
        self.assertNotIn("Verfahren", r["claims"][0]["text"])
        self.assertTrue(r["claims"][0]["text"].startswith("1. Method for determining"))
        self.assertEqual(r["claims"][1]["depends_on"], [1])

    def test_translation_noted_for_ep(self):
        r = parse_google_html(self.HTML, requested="EP0944293A1")
        self.assertTrue(any("machine translation from German" in n for n in r["notes"]))


class TestCanceledClaims(unittest.TestCase):
    """F27: KR101390397B1's claims 1-2 read only "delete" and parsed as independent claims."""

    HTML = (
        '<html><head><title>KR101390397B1 - Safety device - Google Patents</title></head><body>'
        '<span itemprop="publicationNumber">KR101390397B1</span>'
        '<section itemprop="claims" itemscope><h2>Claims (<span itemprop="count">4</span>)</h2>'
        '<aside>Translated from <span itemprop="translatedLanguage">Korean</span></aside>'
        '<div itemprop="content" html><claims lang="EN" load-source="google">'
        '<claim num="1"><claim-text><span class="notranslate"><span class="google-src-text">삭제</span>'
        'delete</span></claim-text></claim>'
        '<claim num="2"><claim-text><span class="notranslate"><span class="google-src-text">삭제</span>'
        '(Deleted)</span></claim-text></claim>'
        '<claim num="3"><claim-text>A cooking appliance comprising a load cell.</claim-text></claim>'
        '<claim num="4"><claim-text>The appliance of claim 3, wherein the load cell is deleted from the plate.'
        '</claim-text></claim></claims></div></section></body></html>')

    def test_deleted_claims_marked_canceled_not_independent(self):
        r = parse_google_html(self.HTML, requested="KR101390397B1")
        c = {x["num"]: x for x in r["claims"]}
        self.assertTrue(c[1]["canceled"] and c[2]["canceled"])
        self.assertFalse(c[1]["independent"] or c[2]["independent"])
        self.assertEqual([x["num"] for x in r["claims"] if x["independent"]], [3])
        self.assertNotIn("canceled", c[4])
        self.assertEqual(c[4]["depends_on"], [3])
        self.assertTrue(any("Claims 1, 2 are deleted/canceled" in n for n in r["notes"]))

    def test_language_variants(self):
        from patent_fetch import is_canceled_text
        for t in ("1. delete", "2. Deleted.", "3. (Canceled)", "4. Cancelled", "5. [삭제]", "6. 削除",
                  "7. Claim 7 is deleted.", "8. (gestrichen)"):
            self.assertTrue(is_canceled_text(t), t)
        for t in ("9. A method of deleting a file.", "10. Canceled-order handling system comprising a queue."):
            self.assertFalse(is_canceled_text(t), t)


class TestSimilarDocuments(unittest.TestCase):
    """F02: cache Google's Similar Documents list and print it with `similar NUMBER`."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "cache"))

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_parsed_into_record(self):
        sim = load("US9457709B2")["similar"]
        self.assertGreater(len(sim), 5)
        self.assertEqual(sim[0], {"number": "US20160144773A1",
                                  "title": "Bicycle helmet with an adaptive light notification system",
                                  "date": "2016-05-26"})
        self.assertTrue(all(s["number"] and s["number"] != "US9457709B2" for s in sim))

    def test_similar_command_from_cache_marks_known(self):
        import patent_fetch
        from state import empty_prior_art
        write_json(os.path.join(self.d, "cache", "US9457709B2.json"), load("US9457709B2"))
        pa = empty_prior_art()
        pa["references"] = [{"id": "R1", "type": "application", "number": "US20160144773A1"}]
        write_json(os.path.join(self.d, "prior-art.json"), pa)
        res = patent_fetch.run({"command": "similar", "number": "9457709", "dir": self.d, "offline": True,
                                "no_audit": True})
        self.assertEqual(res["exit_code"], 0, res)
        self.assertEqual(res["similar"][0]["known_as"], "R1")
        self.assertTrue(any("patent_fetch.py fetch" in t for t in res["text"]))
        self.assertEqual(res["summary"]["new"], len(res["similar"]) - 1)

    def test_old_record_reparsed_from_raw_page(self):
        import gzip
        import patent_fetch
        rec = load("US9457709B2")
        rec.pop("similar")
        write_json(os.path.join(self.d, "cache", "US9457709B2.json"), rec)
        raw = patent_fetch.raw_html_path(self.d, "US9457709B2")
        os.makedirs(os.path.dirname(raw))
        with open(os.path.join(FIX, "US9457709B2.html"), "rb") as src, gzip.open(raw, "wb") as dst:
            dst.write(src.read())
        res = patent_fetch.run({"command": "similar", "number": "US9457709B2", "dir": self.d, "offline": True,
                                "no_audit": True})
        self.assertIn("similar (re-parsed saved page)", res["checks_run"])
        self.assertIn("similar", patent_fetch.read_json(os.path.join(self.d, "cache", "US9457709B2.json")))

    def test_offline_miss(self):
        import patent_fetch
        res = patent_fetch.run({"command": "similar", "number": "US9457709B2", "dir": self.d, "offline": True,
                                "no_audit": True})
        self.assertEqual(res["exit_code"], 3)

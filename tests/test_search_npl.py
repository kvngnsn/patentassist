"""Offline tests for scripts/npl_fetch.py (F09): abstracts are cached so NPL quotes can be checked,
search ranks by OpenAlex relevance and prints the abstract's first sentence. The HTTP layer
(npl_fetch._get_json) is replaced with canned Crossref / OpenAlex responses."""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import npl_fetch  # noqa: E402
import quote_check  # noqa: E402
from state import empty_prior_art, read_json, write_json  # noqa: E402

DOI = "10.1121/1.1566333"
CROSSREF_ITEM = {
    "DOI": DOI, "title": ["Acoustic detection of boiling in cookware"], "type": "journal-article",
    "author": [{"given": "Ada", "family": "Lovelace"}, {"given": "Ben", "family": "Franklin"}],
    "container-title": ["J. Acoust. Soc. Am."], "issued": {"date-parts": [[2003, 4, 1]]},
    "URL": "https://doi.org/" + DOI, "score": 41.5,
}
JATS = ("<jats:title>Abstract</jats:title><jats:p>Sound from a heated pot changes as water nears boiling. "
        "The <jats:italic>dominant</jats:italic> band shifts &amp; the level rises.</jats:p>")


def inverted(text):
    inv = {}
    for i, w in enumerate(text.split()):
        inv.setdefault(w, []).append(i)
    return inv


OA_ABSTRACT = "Bubble collapse noise peaks before boiling. A microphone near the pot hears it."
OA_WORK = {"id": "https://openalex.org/W1", "doi": "https://doi.org/" + DOI,
           "title": "Acoustic detection of boiling in cookware", "publication_date": "2003-04-01",
           "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
           "primary_location": {"source": {"display_name": "J. Acoust. Soc. Am."}},
           "abstract_inverted_index": inverted(OA_ABSTRACT), "relevance_score": 812.3, "type": "article"}
OA_OTHER = {"id": "https://openalex.org/W2", "doi": "https://doi.org/10.1000/xyz",
            "title": "Accelerometer calibration for appliances", "publication_date": "2019-01-01",
            "authorships": [], "primary_location": {}, "relevance_score": 300.0,
            "abstract_inverted_index": inverted("Calibration of accelerometers is described. More text.")}


class FakeHttp(object):
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        for prefix, payload in self.routes:
            if url.startswith(prefix):
                return (200, payload) if payload is not None else (404, None)
        return 404, None


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._orig = npl_fetch._get_json

    def tearDown(self):
        npl_fetch._get_json = self._orig
        shutil.rmtree(self.d)

    def http(self, routes):
        npl_fetch._get_json = FakeHttp(routes)
        return npl_fetch._get_json


class TestAbstracts(Base):
    def test_rebuild_and_strip(self):
        self.assertEqual(npl_fetch._openalex_abstract(inverted("a b a c")), "a b a c")
        self.assertIsNone(npl_fetch._openalex_abstract({}))
        self.assertEqual(npl_fetch.strip_jats(JATS), "Sound from a heated pot changes as water nears boiling. "
                                                      "The dominant band shifts & the level rises.")
        self.assertEqual(npl_fetch.first_sentence(OA_ABSTRACT), "Bubble collapse noise peaks before boiling.")

    def test_doi_crossref_abstract_cached_and_quotable(self):
        item = dict(CROSSREF_ITEM, abstract=JATS)
        self.http([(npl_fetch.CROSSREF + "/", {"message": item})])
        res = npl_fetch.run({"command": "doi", "target": DOI, "dir": self.d, "no_audit": True})
        rec = res["record"]
        self.assertEqual(rec["abstract_source"], "crossref")
        self.assertIn("dominant band shifts & the level rises", rec["abstract"])
        # quote_check can now confirm a quote from the abstract
        pa = empty_prior_art()
        pa["references"] = [{"id": "R1", "type": "npl", "doi": DOI, "element_map": {
            "E1": {"state": "explicit", "quote": "The dominant band shifts & the level rises", "pinpoint": None}}}]
        write_json(os.path.join(self.d, "prior-art.json"), pa)
        qc = quote_check.run({"dir": self.d, "no_audit": True})
        self.assertEqual(qc["exit_code"], 0, qc["findings"])
        self.assertEqual(read_json(os.path.join(self.d, "prior-art.json"))["references"][0]["element_map"]["E1"]
                         ["pinpoint"], "abstract")

    def test_doi_falls_back_to_openalex_for_abstract(self):
        fake = self.http([(npl_fetch.CROSSREF + "/", {"message": CROSSREF_ITEM}),
                          (npl_fetch.OPENALEX + "/doi:", OA_WORK)])
        rec = npl_fetch.run({"command": "doi", "target": DOI, "dir": self.d, "no_audit": True})["record"]
        self.assertEqual(rec["source"], "crossref")
        self.assertEqual((rec["abstract"], rec["abstract_source"]), (OA_ABSTRACT, "openalex"))
        self.assertEqual(len(fake.calls), 2)
        self.assertFalse(any("No abstract" in n for n in rec["notes"]))

    def test_doi_without_any_abstract_says_so(self):
        self.http([(npl_fetch.CROSSREF + "/", {"message": CROSSREF_ITEM}),
                   (npl_fetch.OPENALEX + "/doi:", dict(OA_WORK, abstract_inverted_index=None))])
        rec = npl_fetch.run({"command": "doi", "target": DOI, "dir": self.d, "no_audit": True})["record"]
        self.assertIsNone(rec["abstract"])
        self.assertTrue(any("No abstract or text" in n for n in rec["notes"]))


class TestSearch(Base):
    def test_ranked_by_openalex_relevance_nothing_cached(self):
        self.http([(npl_fetch.OPENALEX + "?", {"results": [OA_OTHER, OA_WORK]}),
                   (npl_fetch.CROSSREF + "?", {"message": {"items": [
                       CROSSREF_ITEM, {"DOI": "10.2000/only-crossref", "title": ["Pot lid sensor"], "score": 9.0}]}})])
        res = npl_fetch.run({"command": "search", "target": "boil over sound sensing", "dir": self.d,
                             "no_audit": True})
        titles = [c["title"] for c in res["candidates"]]
        # OpenAlex order kept (its relevance), Crossref duplicate merged, Crossref-only result last
        self.assertEqual(titles, ["Accelerometer calibration for appliances", "Acoustic detection of boiling in "
                                  "cookware", "Pot lid sensor"])
        self.assertEqual(res["candidates"][1]["abstract_first_sentence"], "Bubble collapse noise peaks before boiling.")
        self.assertEqual(res["status"], "candidates_only")
        self.assertTrue(any(t.startswith("Search results (nothing cached); fetch one with") for t in res["text"]))
        self.assertFalse(any("No match" in t for t in res["text"]))
        self.assertTrue(any("Bubble collapse noise peaks" in t for t in res["text"]))
        self.assertEqual([f for f in os.listdir(os.path.join(self.d, "cache"))], [])

    def test_title_lookup_caches_with_abstract(self):
        self.http([(npl_fetch.OPENALEX + "?", {"results": [OA_WORK]}),
                   (npl_fetch.CROSSREF + "?", {"message": {"items": []}})])
        res = npl_fetch.run({"command": "search", "target": "Acoustic detection of boiling in cookware",
                             "dir": self.d, "no_audit": True})
        self.assertEqual(res["status"], "fetched")
        rec = read_json(res["path"])
        self.assertEqual(rec["abstract"], OA_ABSTRACT)
        self.assertNotIn("title_score", rec)
        self.assertNotIn("relevance", rec)


if __name__ == "__main__":
    unittest.main()

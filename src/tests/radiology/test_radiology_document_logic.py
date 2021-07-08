import pytest

from src.util import build_nlp

nlp = build_nlp("radiology")

class TestRadiologyLogic:
    def test_pos_doc(self):
        text = "Impression: There is infiltrate."
        doc = nlp(text)
        assert doc._.document_classification == "POS"

    def test_indication_doc(self):
        text = "Indication: pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0]._.section_category == "indication"
        assert doc.ents[0]._.is_ignored is True
        assert doc._.document_classification == "NEG"

    def test_suspect_pneumonia(self):
        text = "Suspect pneumonia in the right lung."
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0]._.is_uncertain is True
        assert doc._.document_classification == "POS"

    def test_indication_and_positive(self):
        text = "Indication: Pneumonia. Impression: Infiltrate"
        doc = nlp(text)
        assert len(doc.ents) == 2
        assert doc.ents[0]._.is_ignored is True
        assert doc._.document_classification == "POS"
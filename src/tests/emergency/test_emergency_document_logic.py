import pytest

from src.util import build_nlp

nlp = build_nlp("emergency")

class TestDischargeLogic:
    def test_pos_doc(self):
        text = "Chief complaint: Pneumonia."
        doc = nlp(text)
        assert doc._.document_classification == "POS"

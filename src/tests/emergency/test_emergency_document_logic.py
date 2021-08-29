import pytest

from src.util import build_nlp

nlp = build_nlp("emergency")

class TestDischargeLogic:
    def test_pos_docs(self):
        texts = [
            "ASSESSMENT/Plan: Pneumonia",
            "Diagnosis: Pneumonia",
            "Diagnoses: Pneumonia",
            "Final Diagnoses: Pneumonia",
        ]
        failed = [] # [(doc, expected, actual)]
        for text in texts:
            doc = nlp(text)
            if doc._.document_classification != "POS":
                failed.append((doc, "POS", doc._.document_classification))
        assert failed == []

    def test_possible_docs(self):
        texts = [
            "ASSESSMENT/Plan: Possible Pneumonia",
            "ASSESSMENT/Plan: Ddx includes pneumonia",
            "Medical Decision Making: Pneumonia",
            "Final Diagnoses: rule out Pneumonia",
        ]
        failed = []
        for text in texts:
            doc = nlp(text)
            if doc._.document_classification != "POSSIBLE":
                failed.append((doc, "POSSIBLE", doc._.document_classification))
        assert failed == []
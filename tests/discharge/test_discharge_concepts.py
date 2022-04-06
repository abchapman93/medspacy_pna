import pytest

from medspacy_pna.util import build_nlp

nlp = build_nlp("discharge")
print(nlp)
class TestDischargeConcepts:

    def test_templates(self):
        texts = ["The patient has COPD or had Pneumonia during this admission."]
        for text in texts:
            doc = nlp(text)
            assert len(doc.ents) == 1
            assert doc.ents[0].label_ == "TEMPLATE"

    def test_initially_treated(self):
        text = "He was initially treated for pneumonia."
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0].label_ == "PNEUMONIA"
        assert doc.ents[0]._.is_historical is True

    def test_rule_out(self):

        texts = ["rule out pneumonia", "r/o pneumonia", "ro pneumonia"]
        failed = []
        for text in texts:
            doc = nlp(text)
            try:
                assert len(doc.ents) == 1
                ent = doc.ents[0]
                assert ent.label_ == "PNEUMONIA"
                assert ent._.is_ignored is True
            except AssertionError:
                failed.append(text)
        assert failed == []

    def test_ruled_out(self):
        texts = ["pneumonia: ruled out", "pneumonia -ruled out"]
        failed = []
        for text in texts:
            doc = nlp(text)
            try:
                assert len(doc.ents) == 1
                ent = doc.ents[0]
                assert ent.label_ == "PNEUMONIA"
                assert ent._.is_negated is True
            except AssertionError:
                failed.append(text)
        assert failed == []

    def test_hospital_acquired_pneumonia(self):
        texts = ["HAP", "hospital-acquired pneumonia", "hospital acquired pneumonia", "healthcare-associated pneumonia", "healthcare associated pna"]
        failed = []
        for text in texts:
            doc = nlp(text)
            try:
                assert len(doc.ents) == 1
                assert doc.ents[0].label_ == "HOSPITAL_ACQUIRED_PNEUMONIA"
            except AssertionError:
                failed.append(text)
        assert failed == []



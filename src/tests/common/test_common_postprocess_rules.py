from src.util import build_nlp

nlp = build_nlp("discharge")

class TestDCommonPostprocessRules:
    def test_cap_medications(self):
        doc = nlp("Medications: cap")
        assert doc._.section_categories[0] == "medications"
        assert len(doc.ents) == 0

    def test_cap_not_medications(self):
        doc = nlp("cap")
        assert len(doc.ents) == 1
        assert doc.ents[0].label_ == "PNEUMONIA"

    def test_pneumonia_medications(self):
        doc = nlp("Medications: pneumonia")
        assert doc._.section_categories[0] == "medications"
        assert len(doc.ents) == 0

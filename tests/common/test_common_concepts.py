from medspacy_pna.util import build_nlp
import pytest

nlp = build_nlp("discharge")

class TestCommonConcepts:
    def test_pneumonia(self):
        texts = ["pneumonia", "pna",
                 # "cap",
                 "community-acquired pneumonia"]
        docs = list(nlp.pipe(texts))
        for doc in docs:
            assert len(doc.ents) == 1
            assert doc.ents[0].label_ == "PNEUMONIA"

    def test_hap(self):
        texts = ["hospital-acquired pneumonia", "hospital acquired pna", "hap"]
        docs = list(nlp.pipe(texts))
        for doc in docs:
            assert len(doc.ents) == 1
            assert doc.ents[0].label_ == "HOSPITAL_ACQUIRED_PNEUMONIA"

    @pytest.mark.skip("Filtered out category")
    def test_tx_for_pneumonia(self):
        texts = ["empiric treatment for pneumonia", "abx for pna"]
        docs = list(nlp.pipe(texts))
        for doc in docs:
            assert len(doc.ents) == 1
            assert doc.ents[0].label_ == "PNEUMONIA"
            assert len(doc.ents[0]) == len(doc)

    def test_template(self):
        texts = ["[] Pneumonia", "() Pneumonia", "[ ] Pneumonia", "( ) Pneumonia"]
        for text in texts:
            doc = nlp(text)
            assert len(doc.ents) == 1
            assert doc.ents[0].label_ == "TEMPLATE"
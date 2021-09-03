from src.util import build_nlp

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

    def test_tx_for_pneumonia(self):
        texts = ["empiric treatment for pneumonia", "abx for pna"]
        docs = list(nlp.pipe(texts))
        for doc in docs:
            assert len(doc.ents) == 1
            assert doc.ents[0].label_ == "PNEUMONIA"
            assert len(doc.ents[0]) == len(doc)
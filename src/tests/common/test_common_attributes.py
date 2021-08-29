from src.util import build_nlp

nlp = build_nlp("discharge")

class TestCommonAttributes:
    def test_recent_pneumonia_historical(self):
        text = "recent pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0].label_ == "PNEUMONIA"
        assert doc.ents[0]._.is_historical is True

    def test_ro_pneumonia(self):
        text = "objective r/o pneumonia"
        doc = nlp(text)
        # doc[0].is_sent_start = True
        # for token in doc[1:]: # sentence splitting issues
        #     token.is_sent_start = False
        assert len(doc.ents) == 1
        assert doc.ents[0].label_ == "PNEUMONIA"
        assert doc.ents[0]._.is_hypothetical is True
from medspacy_pna.util import build_nlp

nlp = build_nlp("emergency")

class TestCommonAttributes:
    def test_recent_pneumonia_historical(self):
        text = "recent pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0].label_ == "PNEUMONIA"
        assert doc.ents[0]._.is_historical is True


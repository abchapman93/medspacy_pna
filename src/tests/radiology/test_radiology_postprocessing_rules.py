import pytest

from src.util import build_nlp

nlp = build_nlp("radiology")

class TestRadiologyLogic:

    def test_indication_ent(self):
        text = "Indication: pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0]._.section_category == "indication"
        assert doc.ents[0]._.is_uncertain is True

import pytest

from src.util import build_nlp

nlp = build_nlp("radiology")

DISABLE = [
    "postprocessor",
    "document_classifier",
]

class TestRadiologyLogic:

    def test_indication_ent(self):
        text = "Indication: pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0]._.section_category == "indication"
        assert doc.ents[0]._.is_ignored is True

    @pytest.mark.skip("Disabling for now")
    def test_first_line_report_text(self):
        text = "REPORT_TEXT: pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0]._.section_category == "report_text"
        assert doc.ents[0]._.is_ignored is True

    def test_pulmonary_artery(self):
        text = "There is adequate opacification of the pulmonary arteries."
        doc = nlp(text, disable=DISABLE)
        assert len(doc.ents)
        ent = doc.ents[0]
        assert ent.label_ == "OPACITY"
        assert ent._.anatomy.text == "pulmonary arteries"
        assert ent._.is_ignored is False
        nlp.get_pipe("postprocessor")(doc)
        assert ent._.is_ignored is True

    def test_no_acute_chest_findings(self):
        for phrase in ["disease", "process", "findings"]:
            text = f"No acute chest {phrase}."
            doc = nlp(text, disable=DISABLE)
            assert len(doc.ents)
            ent = doc.ents[0]
            assert ent.label_ == "PNEUMONIA"
            assert ent._.is_ignored is True
            assert ent._.is_negated is True
            nlp.get_pipe("postprocessor")(doc)
            assert ent._.is_ignored is False

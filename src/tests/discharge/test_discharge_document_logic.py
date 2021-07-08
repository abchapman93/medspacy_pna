import pytest

from src.util import build_nlp
from src.constants import FINDINGS_CONCEPTS

nlp = build_nlp("discharge")

class TestDischargeLogic:
    def test_pos_doc(self):
        text = "The patient developed pneumonia."
        doc = nlp(text)
        assert doc._.document_classification == "POS"

    def test_hpi_doc(self):
        """We may not want evidence from the HPI for discharge summaries since that reflects initial dx."""
        text = "History of Present Illness: The patient arrived yesterday. The patient developed pneumonia."
        doc = nlp(text)
        assert doc._.section_categories[0] == "history_of_present_illness"
        assert doc._.document_classification == "NEG"

    def test_admitting_diagnosis_doc(self):
        """We may not want evidence from the admitting diagnosis for discharge summaries since that reflects initial dx."""
        text = "Admitting diagnosis: pneumonia."
        doc = nlp(text)
        assert doc._.section_categories[0] == "admission_diagnoses"
        assert doc._.document_classification == "NEG"

    @pytest.mark.skip(reason="Need to solidify logic")
    def test_finding_doc(self):
        text = "Chest x-ray showed consolidation."
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0].label_ in FINDINGS_CONCEPTS
        assert doc._.document_classification == "NEG"

    @pytest.mark.skip(reason="Need to solidify logic")
    def test_finding_ap_doc(self):
        text = "Assessment/Plan: patient has consolidation."
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0].label_ in FINDINGS_CONCEPTS
        assert doc._.section_categories[0] == "observation_and_plan"
        assert doc._.document_classification == "POS"
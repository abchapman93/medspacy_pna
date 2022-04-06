import pytest

from medspacy_pna.util import build_nlp
from medspacy_pna.util import get_document_classifier_pipe_name
from medspacy_pna.constants import FINDINGS_CONCEPTS

nlp = build_nlp("discharge")
assert nlp.get_pipe(get_document_classifier_pipe_name(nlp)).classification_schema == "full"

class TestDischargeLogic:
    def test_pos_doc(self):
        texts = [
            "Hospital course: The patient developed pneumonia.",
            "Diagnoses: HAP",
            "Final Dx: Pneumonia",
            "Hospital course: Pneumonia"
        ]
        failed = []
        for text in texts:
            doc = nlp(text)
            try: assert doc._.document_classification == "POS"
            except AssertionError: failed.append(text)
        assert failed == []

    def test_neg_doc(self):
        texts = [
            "Discharge Dx: No pneumonia. Hospital course: possible pneumonia",
            "MDM: Pneumonia",
            "ED course: Pneumonia",
            "Discharge Dx: airspace disease",
            "Discharge Dx: Rule out pneumonia"

        ]
        failed = []
        for text in texts:
            doc = nlp(text)
            try: assert doc._.document_classification == "NEG"
            except AssertionError: failed.append(text)
        assert failed == []

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
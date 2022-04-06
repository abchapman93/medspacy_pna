import pytest

from medspacy_pna.util import build_nlp
from medspacy_pna.util import get_document_classifier_pipe_name
from medspacy_pna.document_classification.emergency_document_classifier import EmergencyDocumentClassifier

nlp = build_nlp("emergency")

class TestDischargeLogic:

    def test_clf_cls(self):
        assert isinstance(nlp.get_pipe(get_document_classifier_pipe_name(nlp)), EmergencyDocumentClassifier)

    def test_pos_docs(self):
        texts = [
            "ASSESSMENT/Plan: Pneumonia",
            "Diagnosis: Pneumonia",
            "Diagnoses: Pneumonia",
            "Final Diagnoses: Pneumonia",
        ]
        failed = [] # [(doc, expected, actual)]
        for text in texts:
            doc = nlp(text)
            if doc._.document_classification != "POS":
                failed.append((doc, "POS", doc._.document_classification))
        assert failed == []

    def test_possible_docs(self):
        texts = [
            "ASSESSMENT/Plan: Possible Pneumonia",
            "ASSESSMENT/Plan: Ddx includes pneumonia",
            "Medical Decision Making: Pneumonia",
            "Final Diagnoses: rule out Pneumonia",
            "ED course: Pneumonia",
            "Hospital course: Pneumonia",
        ]
        failed = []
        for text in texts:
            doc = nlp(text)
            if doc._.document_classification != "POSSIBLE":
                failed.append((doc, "POSSIBLE", doc._.document_classification))
        assert failed == []

    def test_neg_docs(self):
        texts = [

            "Assessment/Plan: Airspace disease"
        ]
        failed = []
        for text in texts:
            doc = nlp(text)
            if doc._.document_classification != "NEG":
                failed.append((doc, "NEG", doc._.document_classification))
        assert failed == []

    def test_ro_pneumonia(self): # TODO: Move this somewhere else
        text = "objective r/o pneumonia"
        doc = nlp(text)
        # doc[0].is_sent_start = True
        # for token in doc[1:]: # sentence splitting issues
        #     token.is_sent_start = False
        assert len(doc.ents) == 1
        assert doc.ents[0].label_ == "PNEUMONIA"
        assert doc.ents[0]._.is_uncertain is True

    def test_imaging_terms(self):
        texts = [
            ("A/P: consolidation", "NEG"),
            ("Medical Decision Making: possible pneumonia. A/P: No consolidation.", "NEG"),
            ("Medical Decision Making: possible pneumonia. A/P: No airspace disease.", "NEG"),
            ("A/P: There is pneumonia. No consolidation.", "POS"),
        ]
        failed = []
        for (text, expected) in texts:
            doc = nlp(text)
            pred = doc._.document_classification
            if pred != expected:
                failed.append((text, expected, pred))
        assert failed == []

    def test_uncertain_followed_by_negated_rad(self):
        """Test that a document which contains an uncertain Tier 1 term but has a negated term later in the document should be 'NEG'"""
        text = """
        Medical Decision Making: Possible pneumonia.
        
        Impression: Chest x-ray showed no infiltrate.
        """
        doc = nlp(text)
        assert doc._.document_classification == "NEG"

    def test_positive_followed_by_uncertain(self):
        text = """
        Assessment/Plan: pneumonia.
        Medical Decision Making: Possible pneumonia.
        """
        doc = nlp(text)
        assert doc._.document_classification == "POS"

    def test_positive_followed_by_negated(self):
        text = """
        Assessment/Plan: pneumonia. No pneumonia.
        """
        doc = nlp(text)
        assert doc._.document_classification == "POS"

    # def test_disambiguate_impression
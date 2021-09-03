import pytest

from src.util import build_nlp
from src.document_classification.radiology_document_classifier import RadiologyDocumentClassifier


nlp = build_nlp("radiology")

class TestRadiologyLogic:
    def test_clf_class(self):
        assert isinstance(nlp.get_pipe("document_classifier"), RadiologyDocumentClassifier)

    def test_pos_doc(self):
        text = "Impression: There is infiltrate."
        doc = nlp(text)
        assert doc._.document_classification == "POS"

    def test_indication_doc(self):
        text = "Indication: pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0]._.section_category == "indication"
        assert doc.ents[0]._.is_ignored is True
        assert doc._.document_classification == "NEG"

    def test_suspect_pneumonia(self):
        text = "Suspect pneumonia in the right lung."
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0]._.is_uncertain is True
        assert doc._.document_classification == "POSSIBLE"

    def test_indication_and_positive(self):
        text = "Indication: Pneumonia. Impression: Infiltrate"
        doc = nlp(text)
        assert len(doc.ents) == 2
        assert doc.ents[0]._.is_ignored is True
        assert doc._.document_classification == "POS"

    def test_tier_2_excluding_diagnosis(self):
        """Test that a 'Tier 2' evidence will be overruled by an excluding diagnosis such as atelectasis."""
        text = "Found an infiltrate which is likely atelectasis."
        doc = nlp(text)
        assert len(doc.ents) == 2
        assert doc.ents[1].label_ == "ATELECTASIS"
        assert doc.ents[0].label_ == "INFILTRATE"
        assert doc._.document_classification == "NEG"

    def test_tier_1_excluding_diagnosis(self):
        """Test that a 'Tier 1' evidence will overrule an excluding diagnosis such as atelectasis."""
        text = "Found an infiltrate which is likely atelectasis or possibly pneumonia."
        doc = nlp(text)
        assert len(doc.ents) == 3
        assert doc.ents[2].label_ == "PNEUMONIA"
        assert doc.ents[1].label_ == "ATELECTASIS"
        assert doc.ents[0].label_ == "INFILTRATE"
        assert doc._.normalized_document_classification == "POS"

    def test_negated_keyword_only(self):
        text = "No evidence of pneumonia."
        doc = nlp(text, disable=["document_classifier"])
        clf = nlp.get_pipe("document_classifier")
        assert clf.classify_document(doc, schema="keywords") == "POS"
        assert clf.classify_document(doc, schema="full") == "NEG"

    def test_attribute_classification(self):
        texts = [
            ("There is no evidence of pneumonia", "NEG"),
            ("There is possible infiltrate", "POSSIBLE"),
            ("There is pneumonia", "POS"),
            ("There is possible infiltrate. There is atelectasis.", "POSSIBLE"),
        ]
        clf = nlp.get_pipe("document_classifier")
        for text, expected_cls in texts:
            doc = nlp(text)
            assert clf.classify_document(doc, schema="attributes") == expected_cls

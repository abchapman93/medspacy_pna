from src.document_classification.radiology_document_classifier import RadiologyDocumentClassifier
from spacy import blank
from spacy.tokens import Doc

nlp = blank("en")

class TestRadiologyDocumentClassifier:

    def test_init(self):
        clf = RadiologyDocumentClassifier()
        assert clf.domain == "radiology"
        assert clf.name == "document_classifier"

    def test_call(self):
        clf = RadiologyDocumentClassifier()
        doc = nlp("This is my text.")
        doc = clf(doc)
        assert isinstance(doc, Doc)

    def test_domain_classes(self):
        clf = RadiologyDocumentClassifier()
        assert clf.target_classes == {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"}
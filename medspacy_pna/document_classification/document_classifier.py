from abc import ABC, abstractmethod

class BaseDocumentClassifier(ABC):
    """Abstract base class for pneumonia document classifiers.
    Classes inheriting from this will implement domain-specific logic for classifying documents.
    Each inheriting class should have a method _classify_document(doc, **kwargs) which returns a string.
    """
    name = "document_classifier"
    domain = None

    _TARGET_CLASSES = set()

    def __init__(self, classification_schema=None, debug=False):
        self.classification_schema = classification_schema
        self.debug = debug
        pass

    def __call__(self, doc, normalized=False, classification_schema=None, **kwargs):
        doc._.document_classification = self.classify_document(doc, normalized=normalized, classification_schema=classification_schema, **kwargs)
        return doc

    def classify_document(self, doc, normalized=False, classification_schema=None, **kwargs):
        classification = self._classify_document(doc, classification_schema=classification_schema, **kwargs)
        if normalized:
            classification = self.normalize_document_classification(classification)
        return classification

    @abstractmethod
    def _classify_document(self, doc, classification_schema=None, **kwargs):
        pass

    def normalize_document_classification(self, classification):
        if classification == "POSSIBLE":
            return "POS"
        return classification

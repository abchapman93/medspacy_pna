from abc import ABC, abstractmethod

class BaseDocumentClassifier(ABC):
    """Abstract base class for pneumonia document classifiers.
    Classes inheriting from this will implement domain-specific logic for classifying documents.
    Each inheriting class should have a method _classify_document(doc, **kwargs) which returns a string.
    """
    name = "document_classifier"
    domain = None

    _TARGET_CLASSES = set()

    def __init__(self):
        pass


    def __call__(self, doc, normalized=False, **kwargs):
        doc._.document_classification = self.classify_document(doc, normalized=normalized, **kwargs)
        return doc

    def classify_document(self, doc, normalized=False, **kwargs):
        classification = self._classify_document(doc, **kwargs)
        if normalized:
            classification = self.normalize_document_classification(classification)
        return classification

    @abstractmethod
    def _classify_document(self, doc, **kwargs):
        pass

    def normalize_document_classification(self, classification):
        if classification == "POSSIBLE":
            return "POS"
        return classification

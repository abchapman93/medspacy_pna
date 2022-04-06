from medspacy_pna.document_classification.radiology_document_classifier import RadiologyDocumentClassifier
from spacy import blank
from spacy.tokens import Doc

from ..util.testutils import testutils
from medspacy_pna.util import build_nlp
from medspacy_pna.util import get_document_classifier_pipe_name
from medspacy_pna._extensions import set_extensions

set_extensions()

nlp = blank("en")

class TestRadiologyDocumentClassifier:

    def test_init(self):
        clf = RadiologyDocumentClassifier(nlp)
        assert clf.domain == "radiology"

    def test_call(self):
        clf = RadiologyDocumentClassifier(nlp, classification_schema="attributes")
        doc = nlp("This is my text.")
        doc = clf(doc)
        assert isinstance(doc, Doc)

    def test_domain_classes(self):
        clf = RadiologyDocumentClassifier(nlp)
        assert clf.target_classes == {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"}

    def test_schemas(self):
        schemas = ["keywords", "attributes", "full", "linked"]
        for schema in schemas:
            nlp = build_nlp("radiology", doc_cls_schema=schema)
            assert nlp.get_pipe(get_document_classifier_pipe_name(nlp)).classification_schema == schema
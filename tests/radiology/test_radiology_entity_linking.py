from medspacy_pna.util import build_nlp
from medspacy_pna.util import get_document_classifier_pipe_name
# from medspacy_pna.document_classification.radiology_document_classifier import link_evidence


nlp = build_nlp("radiology")
clf = nlp.get_pipe(get_document_classifier_pipe_name(nlp))

class TestRadiologyLogic:
    def test_link_evidence(self):
        text = "Opacity most likely due to atelectasis."
        doc = nlp(text, disable=[get_document_classifier_pipe_name(nlp)])
        clf.link_evidence(doc)
        assert len(doc.ents) == 2
        for ent in doc.ents:
            assert len(ent._.linked_ents)

    def test_link_evidence_dx(self):
        from medspacy_pna.document_classification.radiology_document_classifier import ALTERNATE_DIAGNOSES
        for dx in ALTERNATE_DIAGNOSES:
            text = f"Opacity most likely due to {' '.join(dx.split('_'))}."
            doc = nlp(text, disable=[get_document_classifier_pipe_name(nlp)])
            clf.link_evidence(doc)
            assert len(doc.ents) == 2
            for ent in doc.ents:
                assert len(ent._.linked_ents)


    def test_link_evidence_clf(self):
        text = "Opacity most likely due to atelectasis."
        doc = nlp(text, disable=[get_document_classifier_pipe_name(nlp)])
        cls1 = clf.classify_document(doc, schema="linked")
        assert cls1 == "NEG"

    def test_link_evidence_pos_clf(self):
        text = "Opacity most likely due to atelectasis. There is infiltrate."

        doc = nlp(text, disable=[get_document_classifier_pipe_name(nlp)])
        doc.ents[0]._.is_uncertain = False
        doc.ents[-1]._.is_uncertain = False
        cls1 = clf.classify_document(doc, classification_schema="linked")
        assert cls1 == "POS"

    def test_not_link_evidence_clf(self):
        text = "Opacity most likely due to atelectasis. There is infiltrate."
        doc = nlp(text, disable=[get_document_classifier_pipe_name(nlp)])
        cls1 = clf.classify_document(doc, classification_schema="full")
        assert cls1 == "NEG"



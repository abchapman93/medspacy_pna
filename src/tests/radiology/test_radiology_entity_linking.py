import pytest

from src.util import build_nlp
from src.document_classifier import link_evidence


nlp = build_nlp("radiology")
clf = nlp.get_pipe("document_classifier")

class TestRadiologyLogic:
    def test_link_evidence(self):
        text = "Opacity most likely due to atelectasis."
        doc = nlp(text, disable=["document_classifier"])
        link_evidence(doc)
        assert len(doc.ents) == 2
        for ent in doc.ents:
            assert len(ent._.linked_ents)

    def test_link_evidence_clf(self):
        text = "Opacity most likely due to atelectasis."
        doc = nlp(text, disable=["document_classifier"])
        cls1 = clf.classify_document(doc, schema="linked")
        assert cls1 == "NEG"

    def test_link_evidence_pos_clf(self):
        text = "Opacity most likely due to atelectasis. There is infiltrate."
        doc = nlp(text, disable=["document_classifier"])
        cls1 = clf.classify_document(doc, schema="linked")
        assert cls1 == "POS"

    def test_not_link_evidence_clf(self):
        text = "Opacity most likely due to atelectasis. There is infiltrate."
        doc = nlp(text, disable=["document_classifier"])
        cls1 = clf.classify_document(doc, schema="full", link_ents=False)
        assert cls1 == "NEG"



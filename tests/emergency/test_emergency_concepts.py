import pytest

from medspacy_pna.util import build_nlp

nlp = build_nlp("emergency")

class TestEmergencyConcepts:

    def test_rad_pna(self):
        """Test that the phrase 'acute disease' is disambiguated.
        """
        pos_texts = ["acute disease in the chest", "Imaging: no acute disease", "airspace disease"]
        failed = []
        for text in pos_texts:
            doc = nlp(text)
            ents = [ent for ent in doc.ents if ent.label_ == "RAD_PNEUMONIA"]
            try:
                assert ents
                ent = ents[0]
                # assert ent.text.lower() == "acute disease"
                assert ent._.is_ignored is False
            except:
                failed.append(text)
        assert failed == []

        ignored_texts = ["acute disease", "A/P: acute disease"]
        failed = []
        for text in ignored_texts:
            doc = nlp(text)
            ents = [ent for ent in doc.ents if ent.label_ == "RAD_PNEUMONIA"]
            try:
                assert ents
                ent = ents[0]
                assert ent.text.lower() == "acute disease"
                assert ent._.is_ignored is True
            except:
                failed.append(text)
        assert failed == []

    def test_annotation_guide_pneumonia_clinical_terms(self):
        """Test that the terms marked in the annotation guide all match entities."""
        terms = [
            "Pneumonia",
            "HCAP",
            "PNA",
            "bronchopneumonia",
            # "cap",
            "legionellosis",
            "parapneumonia effusion",
            "empyema",
            "pneumonia protocial"
        ]
        failed = []
        for term in terms:
            doc = nlp(term)
            try:
                assert len(doc.ents)
                ent = doc.ents[0]
                assert len(ent) == len(doc)
                assert ent.label_ == "PNEUMONIA"
            except AssertionError:
                failed.append(term)
        assert failed == []

    def test_annotation_guide_pneumonia_rad_terms(self):
        """Test that the terms marked in the annotation guide all match entities."""
        from medspacy_pna.document_classification.emergency_document_classifier import RADIOGRAPHIC_CLASSES
        terms = [
            "opacity",
            "infiltrate",
            "consolidation",
            "pneumonitis"
        ]
        failed = []
        for term in terms:
            doc = nlp(term)
            try:
                assert len(doc.ents)
                ent = doc.ents[0]
                assert len(ent) == len(doc)
                assert ent.label_ in RADIOGRAPHIC_CLASSES
            except AssertionError:
                failed.append(term)
        assert failed == []

    def test_disambiguate_cap(self):
        positive = ["Assessment/Plan: CAP", "Diagnoses: CAP", "CAP"]
        failed = []
        for text in positive:
            doc = nlp(text)
            try:
                ent = doc.ents[-1]
            except IndexError as e:
                failed.append(text)
                continue
            try:
                assert ent.label_ == "PNEUMONIA"
                assert ent._.is_ignored is False
            except Exception as e:
                failed.append(text)


        ignored = ["Medications: cap", "mg cap", "100 cap", "capsule cap", "cap by mouth"]
        assert failed == []

        failed = []
        for text in ignored:
            doc = nlp(text)
            try:
                ent = doc.ents[-1]
                assert ent.label_ == "PNEUMONIA"
                assert ent._.is_ignored is True
            except Exception as e:
                failed.append(text)
        assert failed == []

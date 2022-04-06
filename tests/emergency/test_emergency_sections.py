import pytest

from medspacy_pna.util import build_nlp

from medspacy_pna.resources.clinical.clinical_postprocess_rules import RAD_TERMS

nlp = build_nlp("emergency")

class TestEmergencySections:
    def test_ap(self):
        titles = ["A/P:", "Assessment/Plan:", "\nA:\n", "\nAssessment & Plan\n", "\nAssessment and Plan\n", "\nAssessment\n"]
        template = "{} Pneumonia"
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == "observation_and_plan"
        # Now check ones that shouldn't match
        titles = ["a:", "\na:", "a:\n", "\nAssessment & Plan", "Assessment and Plan\n", "Assessment pneumonia"]
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == None

    def test_mdm(self):
        titles = ["MDM:", "Medical Decision Making:",]
        template = "{} Pneumonia"
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == "medical_decision_making"
        # Now check ones that shouldn't match
        titles = []
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == None

    def test_disambiguate_impression(self):
        """Test that the section category 'Impression' is correctly disambiguated between Imaging and A/P.
        This disambiguation is only performed when there is an entity in that section due to it being performed
        in the postprocessing component.
        """

        template = "Impression: {} Pneumonia"
        for term in RAD_TERMS:
            text = template.format(term)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == "imaging"

        failed = []
        ap_texts = ["Diagnostic Impressions: Pneumonia", "Impression: Pneumonia", "<<ADDENDUM>>: Pneumoia"]
        for text in ap_texts:
            doc = nlp(text)
            section = doc._.sections[-1]
            try:
                assert section.category != "imaging"
            except AssertionError:
                failed.append((text, section.category))
        assert failed == []

        failed = []
        imaging_texts = ["Labs and Studies: XYZ. Impression: Pneumonia", "Procedures: XYZ Impression: Pneumonia", "Imaging: XYZ Impression: Pneumonia",
                         "Imaging: XYZ Addendum: Pneumonia", "Imaging: XYZ Impression: XYZ Addendum: Pneumonia",
                         "Chest Xray - Impression: Pneumonia"
                         ]
        for text in imaging_texts:
            doc = nlp(text)
            section = doc._.sections[-1]
            try:
                assert section.category == "imaging"
            except AssertionError:
                failed.append((text, section.category))
        assert failed == []

    def test_hospital_course(self):
        titles = ["Hospital Course: "]
        template = "{} Pneumonia"
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == "hospital_course"

    def test_ed_course(self):
        titles = ["ED Course: "]
        template = "{} Pneumonia"
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == "ed_course"

    def test_appended_addendum(self):
        text = "<<ADDENDUM>>:\n\n"
        doc = nlp(text)
        assert doc._.section_categories[0] == "addendum"

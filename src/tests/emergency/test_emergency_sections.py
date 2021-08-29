import pytest

from src.util import build_nlp

nlp = build_nlp("emergency")

class TestEmergencySections:
    def test_ap(self):
        titles = ["A/P:", "Assessment/Plan:", "\nA:\n", "\nAssessment & Plan\n", "\nAssessment and Plan\n"]
        template = "{} Pneumonia"
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == "observation_and_plan"
        # Now check ones that shouldn't match
        titles = ["a:", "\na:", "a:\n", "\nAssessment & Plan", "Assessment and Plan\n"]
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
        rad_terms = {
            "cxr", "imaging", "image", "contrast", "ct",
            "technique", "procedure"
        }
        template = "Impression: {} Pneumonia"
        for term in rad_terms:
            text = template.format(term)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == "imaging"

        for text in ["Diagnostic Impressions: Pneumonia", "Impression: Pneumonia"]:
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category != "imaging"

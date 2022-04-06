import pytest

from medspacy_pna.util import build_nlp

from medspacy_pna.resources.clinical.clinical_postprocess_rules import RAD_TERMS

nlp = build_nlp("discharge")

class TestDischargeSections:
    def test_summary(self):
        titles = ["\nSummary:\n", "\rSummary:\r"]
        template = "{} Pneumonia"
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category == "hospital_course"
        # Now check ones that shouldn't match
        titles = ["Summary:", "\nSummary\n", "\nSummary:", "Summary:\n"]
        for title in titles:
            text = template.format(title)
            doc = nlp(text)
            section = doc._.sections[0]
            assert section.category is None

    def test_sections(self):
        texts = [
            ("DIAGNOSIS AT THE TIME OF DEATH", "discharge_diagnoses"),
            ("Discharge Diagnosis:", "discharge_diagnoses"),
            ("Discharge Diagnoses:", "discharge_diagnoses"),
            ("Discharge Diagnoses\n", "discharge_diagnoses"),
            ("Discharge Diagnosis\n", "discharge_diagnoses"),
            ("Discharge Diagnosis(es):", "discharge_diagnoses"),
            ("Discharge Dx:", "discharge_diagnoses"),
            ("Admission Diagnosis:", "admission_diagnoses"),
            ("Admission Diagnoses:", "admission_diagnoses"),
            ("Admission Diagnoses\n", "admission_diagnoses"),
            ("Admission Diagnosis\n", "admission_diagnoses"),
            ("Admitting Diagnosis:", "admission_diagnoses"),
            ("Admission Diagnosis(es):", "admission_diagnoses"),
            ("Admission Dx:", "admission_diagnoses"),
            ("Reason for Admission:", "admission_diagnoses"),


            # ("\\nBrief Hospital Course by problem, including pertinent physical/lab/radiology findings (as identified as present on admission or not present on admission):", "hospital_course"),

        ]
        failed = []
        for text, expected in texts:
            doc = nlp(text)
            actual = doc._.sections[0].category
            try:
                assert actual == expected
            except AssertionError:
                failed.append((text, expected, actual))
        assert failed == []

    def test_admit_diagnoses(self):
        # "admi(t|ssion|tting|tted) (diagnosis|diagnoses|dx)[\\s]*(:|[\\n\\r])"
        tokens = [
            ("admit", "admission", "admitting", "admitted"),
            ("diagnoses", "dx", "diagnosis",),
            (":", "\n", "\r")
        ]
        failed = []
        for token1 in tokens[0]:
            for token2 in tokens[1]:
                for token3 in tokens[2]:
                    text = " ".join((token1, token2, token3))
                    doc = nlp(text)
                    try:
                        assert doc._.section_categories[0] == "admission_diagnoses"
                    except AssertionError:
                        failed.append((text, doc._.section_categories[0]))
        assert failed == []
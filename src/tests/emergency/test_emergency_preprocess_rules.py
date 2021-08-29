import pytest

from src.util import build_nlp

nlp = build_nlp("emergency")

class TestEmergencySections:
    def test_section_formatting(self):
        texts = ["Diagnoses----\n", "Diagnoses* * * * * \n"]
        for text in texts:
            doc = nlp.tokenizer(text)
            assert doc.text == "Diagnoses:\n"
        texts = ["Diagnoses----", "Diagnoses* * * * * ", "Diagnoses"]
        for text in texts:
            doc = nlp.tokenizer(text)
            assert doc.text == text


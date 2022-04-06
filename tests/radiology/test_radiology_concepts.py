import pytest
from ..util.testutils import testutils
from medspacy_pna.util import build_nlp


class TestRadiologyConcepts:
    @pytest.mark.skip("Filtered out category")
    def test_right_sided_anatomy(self, testutils):
        nlp = build_nlp("radiology")
        text = "right-sided thingy found"
        doc = nlp(text)

        msg = testutils.test_token_concept_tag_exists(doc, "right", "LOCATION")

        assert (msg == '')

    @pytest.mark.skip("Filtered out category")
    def test_non_pneumonia_anatomy(self, testutils):
        nlp = build_nlp("radiology")
        text = "bony structures observed"
        doc = nlp(text)

        msg = testutils.test_token_concept_tag_exists(doc, "bony", "ANATOMY")

        assert (msg == '')

    @pytest.mark.skip("Filtered out category")
    def test_illdefined(self, testutils):
        nlp = build_nlp("radiology")
        text = "hazy observation"
        doc = nlp(text)

        msg = testutils.test_token_concept_tag_exists(doc, "hazy", "ILLDEFINED")

        assert (msg == '')

    def test_opacities(self, testutils):
        nlp = build_nlp("radiology")
        text = "several opacities observed"
        doc = nlp(text)

        msg = testutils.test_token_concept_tag_exists(doc, "opacities", "OPACITY")

        assert (msg == '')

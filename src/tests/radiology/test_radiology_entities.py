import pytest

import medspacy
from medspacy.postprocess import postprocessing_functions
import spacy

from src.util import build_nlp
from src.tests.util.testutils import testutils

nlp = build_nlp("radiology")

class TestRadiologyEntities:
    def test_infiltrates(self, testutils):
        text = "Infiltrate found on lower right lobe"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'infiltrate')

        assert(msg == '')

    def test_infiltrative_density(self, testutils):
        text = "infiltrative density found on lower right lobe"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'infiltrative density')

        assert(msg == '')

    def test_patchy_consolidation(self, testutils):
        text = "patchy consolidation found on lower right lobe"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'patchy consolidation')

        assert(msg == '')

    def test_focal_consolidation(self, testutils):
        text = "focal consolidation found on lower right lobe"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'focal consolidation')

        assert(msg == '')

    def test_focal_pneumonia(self, testutils):
        text = "focal pneumonia observed"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'focal pneumonia')

        assert(msg == '')

    def test_infiltrative_pneumonia(self, testutils):
        text = "infiltrative pneumonia observed"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'infiltrative pneumonia')

        assert(msg == '')

    def test_linear_opacity(self, testutils):
        text = "linear opacity observed"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'linear opacity')

        assert(msg == '')

    def test_opacification(self, testutils):
        text = "opacification observed"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'opacification')

        assert(msg == '')

    def test_infectious_process(self, testutils):
        texts = ["infectious process", "inflammatory process", "infectious/inflammatory process"]
        for text in texts:
            doc = nlp(text)

            msg = testutils.test_entity_exists(doc, text)

            assert(msg == '')

    def test_patchy_density(self, testutils):
        text = "patchy density observed"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'patchy density')

        assert(msg == '')

    def test_airspace_disease(self, testutils):
        text = "airspace disease"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'airspace disease')

        assert(msg == '')

    def test_pneumonitis(self, testutils):
        text = "pneumonitis"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, "pneumonitis")

        assert(msg == '')

    def test_interstitial_lung_markings(self, testutils):
        text = "interstitial lung markings"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, text)

        assert (msg == '')

    def test_focal_density(self, testutils):
        text = "focal density observed"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'focal density')

        assert(msg == '')

    def test_localized_anatomy_modifier(self, testutils):
        # This multi-word example does not work yet
        text = "infiltrate in the right upper lobe"

        doc = nlp(text)

        expected_anatomy_text = 'right upper lobe'

        assert (len(doc.ents) > 0)
        ent = doc.ents[0]
        anatomy = ent._.anatomy
        assert anatomy == expected_anatomy_text

    def test_atelectasis_or_pneumonia(self, testutils):
        texts = ["pneumonia and/or atelectasis", "atelectasis and/or pneumonia", "atelectasis or pneumonia",]
        for text in texts:
            doc = nlp(text)
            msg = testutils.test_entity_exists(doc, text)

            assert (msg == '')
            ent = doc.ents[0]
            assert ent._.is_uncertain is True

    def test_atelectasis(self, testutils):
        text = "atelectasis"
        doc = nlp(text)

        msg = testutils.test_entity_exists(doc, 'atelectasis')

        assert(msg == '')

    def test_history_section(self, testutils):
        text = "History: pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0].lower_ == "pneumonia"
        assert doc.ents[0]._.section_category == "indication"
        assert doc.ents[0]._.is_ignored is True

    def test_indication_section(self, testutils):
        text = "Indication: pneumonia"
        doc = nlp(text)
        assert len(doc.ents) == 1
        assert doc.ents[0].lower_ == "pneumonia"
        assert doc.ents[0]._.section_category == "indication"
        assert doc.ents[0]._.is_ignored is True

    def test_covid_pneumonia(self, testutils):
        texts = ["covid pneumonia", "covid-19 pneumonia", "covid19 pneumonia", ]
        for text in texts:
            doc = nlp(text)
            msg = testutils.test_entity_exists(doc, text)

            assert (msg == '')
            ent = doc.ents[0]




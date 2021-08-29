import pytest

import medspacy
import spacy

from src.util import build_nlp
from src.tests.util.testutils import testutils

# NOTE: POSSIBLE_EXISTENCE and others tested here are  not in the Underscore by default, but for this pipeline
# we augment this in _extensions.py

nlp = build_nlp("radiology")

class TestRadiologyContextModifiers:
    def test_consolidation_negated(self, testutils):
        
        text = "no evidence of consolidation"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_negated')

        assert(msg == '')

    def test_consolidation_or_infiltrate_negated(self, testutils):
        
        text = "no evidence of consolidation or infiltrate"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_negated')
        assert (msg == '')

        msg = testutils.test_entity_modifier_extension_true(doc, 'infiltrate', 'is_negated')
        assert (msg == '')

    def test_free_of_consolidation(self, testutils):
        
        text = "free of consolidation"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_negated')
        assert (msg == '')

    def test_possible_pneumonia(self, testutils):
        
        text = "INTERPRETATION: possible pneumonia"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'pneumonia', 'is_possible_existence')
        assert (msg == '')

    def test_probable_pneumonia(self, testutils):
        
        text = "INTERPRETATION: probable pneumonia"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'pneumonia', 'is_possible_existence')
        assert (msg == '')

    def test_consolidation_present(self, testutils):
        
        text = "INTERPRETATION: consolidation is present"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_positive_existence')
        assert (msg == '')

    def test_consolidation_decreased(self, testutils):
        
        text = "consolidation decreased from previous imaging"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_decreased')
        assert (msg == '')

    def test_consolidation_increased(self, testutils):
        
        text = "consolidation increased from previous imaging"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_increased')
        assert (msg == '')

    def test_consolidation_unchanged(self, testutils):
        
        text = "consolidation unchanged from previous imaging"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_unchanged')
        assert (msg == '')

    def test_consolidation_improved(self, testutils):
        
        text = "consolidation improved from previous imaging"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_improved')
        assert (msg == '')

    def test_consolidation_less_prominent(self, testutils):
        
        text = "consolidation less prominent with respect to previous imaging"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_improved')
        assert (msg == '')

    def test_consolidation_worsening(self, testutils):
        
        text = "consolidation worsened from previous imaging"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_worsened')
        assert (msg == '')

    def test_consolidation_no_interval_changed(self, testutils):
        
        text = "no interval changed of consolidation"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_unchanged')
        assert (msg == '')

    def test_consolidation_not_changed(self, testutils):
        
        text = "consolidation has not changed since last imaging"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_unchanged')
        assert (msg == '')

    def test_consolidation_not_significantly_changed(self, testutils):
        text = "consolidation not significantly changed since last imaging"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_unchanged')
        assert (msg == '')

    def test_poorly_defined_infiltrate(self, testutils):
        texts = ["poorly defined infiltrate", "ill-defined infiltrate", "poorly defined infiltrate"]
        for text in texts:
            doc = nlp(text)
            msg = testutils.test_entity_modifier_extension_true(doc, 'infiltrate', 'is_uncertain')
            assert (msg == '')

    def test_hazy_consolidation(self, testutils):
        text = "hazy consolidation"
        doc = nlp(text)
        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_uncertain')
        assert (msg == '')

    def test_no_significant_consolidation_negated(self, testutils):
        text = "no significant consolidation"
        doc = nlp(text)

        msg = testutils.test_entity_modifier_extension_true(doc, 'consolidation', 'is_negated')

        assert (msg == '')

    def test_no_significant_change_consolidation(self, testutils):
        text = "no significant change in consolidation"
        doc = nlp(text)
        assert len(doc.ents)
        ent = doc.ents[0]
        assert ent._.is_negated is False
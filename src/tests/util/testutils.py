import pytest


class TestUtils:
    @staticmethod
    def test_token_concept_tag_exists(doc, expected_token_text, expected_token_concept_tag):
        tokens = [x.text for x in doc]

        found = False

        for token in doc:
            token_text = token.text.lower()
            token_concept_tag = token._.concept_tag
            if token_text == expected_token_text and token_concept_tag == expected_token_concept_tag:
                found = True

        msg = ''
        if not found:
            msg = 'Expected token text : [{0}] with concept_tag [{1}] was not extracted'.format(expected_token_text,
                                                                                           expected_token_concept_tag)
        return msg

    @staticmethod
    def test_entity_exists(doc, expected_entity_text):
        if len(doc.ents) == 0:
            msg = "Expected at least one entity but found 0"
            return msg

        found = False
        for ent in doc.ents:
            if ent.text.lower() == expected_entity_text:
                found = True

        msg = ''
        if not found:
            msg = 'Expected entity text : {} was not extracted'.format(expected_entity_text)

        return msg

    @staticmethod
    def test_entity_modifier_extension_true(doc, expected_entity_text, modifier_extension):

        if len(doc.ents) == 0:
            return 'Expected at least 1 entity to check modifier extension (i.e. negated, or other modifier) but 0 present'

        found = False
        for ent in doc.ents:
            entity_text = ent.text.lower()

            modifier_true = False
            # This allows for any Underscore extension, not just "is_negated"
            if hasattr(ent._, modifier_extension):
                modifier_true = getattr(ent._, modifier_extension)

            if entity_text == expected_entity_text and modifier_true:
                found = True

        msg = ''
        if not found:
            msg = 'Expected entity text : {0} with "ent._.{1}" was not extracted'.format(expected_entity_text,
                                                                                         modifier_extension)

        return msg

@pytest.fixture
def testutils():
    return TestUtils

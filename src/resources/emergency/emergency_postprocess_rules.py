from medspacy.postprocess import postprocessing_functions
from medspacy.postprocess import PostprocessingPattern, PostprocessingRule
from ...constants import PNEUMONIA_CONCEPTS, FINDINGS_CONCEPTS, TARGET_CONCEPTS
from ..common.common_postprocess_rules import set_ignored

def disambiguate_impression(span, window_size=5):

    # First, check if the preceding section was imaging
    try:
        preceding_token = span.doc[span.start-1]
        if preceding_token._.section_category == "imaging":
            return True
    except IndexError:
        pass

    # NOw look for imaging terms in the neighborhood of the span
    rad_terms = {
        "cxr", "imaging", "image", "contrast", "ct",
        "technique", "procedure", "radiology"
        }
    window = {token.text.lower() for token in span._.window(window_size)}

    if window.intersection(rad_terms):
        return True
    return False

def change_ent_section(ent, i, value):
    ent._.section.category = value

postprocess_rules = [
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent._.section_category == "impression"),
            PostprocessingPattern(lambda ent: ent._.section_title._.contains("diagnos") is False),
            PostprocessingPattern(lambda ent: disambiguate_impression(ent._.section_title, window_size=5))
        ],
        action=change_ent_section, action_args=("imaging",),
        description="Disambiguate between 'impression' meaning imaging and A/P"
    ),
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ == "PNEUMONIA"),
            PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_text(ent, r"risk")),
            PostprocessingPattern(lambda ent: postprocessing_functions.is_followed_by(ent, target="is low", window=ent.sent.end - ent.end))
        ],
        action=postprocessing_functions.set_negated, action_args=(True,),
        description="Set the phrase 'the risk of pneumonia is low' to be negated"
    ),
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ == "RAD_PNEUMONIA"),
            (
                PostprocessingPattern(lambda ent: ent._.section_category == "imaging"),
                PostprocessingPattern(lambda ent: ent.sent._.contains(r"(chest|cxr|x-ray|imaging)", regex=True, case_insensitive=True)),
            )
        ],
        action=set_ignored, action_args=(False,),
        description="Ignore mentions of terms like 'infectious disease' unless they appear in imaging or in the context of 'chest'"
    ),

    # TODO: will need to revisit this to make it more specific
    # PostprocessingRule(
    #     patterns=[
    #         PostprocessingPattern(lambda ent: ent.label_ in FINDINGS_CONCEPTS),
    #         PostprocessingPattern(lambda ent: ent._.section_category
    #                                           not in ("observation_and_plan", "discharge_diagnoses")),
    #     ],
    #     action=postprocessing_functions.set_uncertain,
    #     action_args=(True,),
    #     description="Only count findings like consolidation in a discharge summary if they are included"
    #                 " in a section like assessment/plan or discharge diagnoses "
    #                 "to avoid using evidence from radiology reports"
    # ),
]
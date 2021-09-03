from medspacy.postprocess import postprocessing_functions
from medspacy.postprocess import PostprocessingPattern, PostprocessingRule

from ...constants import TARGET_CONCEPTS, FINDINGS_CONCEPTS, PNEUMONIA_CONCEPTS

def set_ignored(ent, i, value=True):
    ent._.is_ignored = value

postprocess_rules = [
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ in PNEUMONIA_CONCEPTS),
            PostprocessingPattern(lambda ent: ent._.section_category == "medications"),

        ],
        action=postprocessing_functions.remove_ent,
        description="Ignore mentions of pneumonia in the 'medications' section"
    ),

    # PostprocessingRule(
    #     patterns=[
    #         PostprocessingPattern(lambda ent: ent.lower_ == "cap"),
    #         (
    #             # This condition is redundant with the previous rule
    #             # PostprocessingPattern(lambda ent: ent._.section_category == "medications"),
    #             PostprocessingPattern(lambda ent: ent.sent._.contains("mg|medication")),
    #          )
    #     ],
    #     action=postprocessing_functions.remove_ent,
    #     description="In the medications, disambiguate 'CAP'."
    # ),
]
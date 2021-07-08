from medspacy.postprocess import postprocessing_functions
from medspacy.postprocess import PostprocessingPattern, PostprocessingRule

from ...constants import TARGET_CONCEPTS, FINDINGS_CONCEPTS

def set_custom_attribute(ent, i, attr, value=True):
    setattr(ent._, attr, value)

postprocess_rules = [
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ in TARGET_CONCEPTS),
            PostprocessingPattern(lambda ent: ent._.section_category == "indication"),
            PostprocessingPattern(postprocessing_functions.is_modified_by_category,
                                  condition_args=("POSITIVE_EXISTENCE",),
                                  success_value=False
                                  ),
        ],
        action=set_custom_attribute, action_args=("is_ignored", True,),
        description="If a mention of pneumonia occurs in 'INDICATION' and is not modified by a positive modifier, "
                    "set is_ignored to True."
    ),

]
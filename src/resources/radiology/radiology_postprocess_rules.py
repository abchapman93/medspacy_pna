from medspacy.postprocess import postprocessing_functions
from medspacy.postprocess import PostprocessingPattern, PostprocessingRule

from ...constants import TARGET_CONCEPTS, FINDINGS_CONCEPTS

def set_custom_attribute(ent, i, attr, value=True):
    setattr(ent._, attr, value)

def check_anatomy(ent, target, regex=True):
    anatomy = ent._.anatomy
    if anatomy is None:
        return False
    return anatomy._.contains(target, regex=regex)

def get_literal(span):
    rule = span._.target_rule
    if rule is None:
        return span.text.lower()
    return rule.literal

postprocess_rules = [
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ in TARGET_CONCEPTS),
            PostprocessingPattern(lambda ent: ent._.section_category in ("indication",
                                                                         # "report_text"
                                                                         )),
            PostprocessingPattern(postprocessing_functions.is_modified_by_category,
                                  condition_args=("POSITIVE_EXISTENCE",),
                                  success_value=False
                                  ),
        ],
        action=set_custom_attribute, action_args=("is_ignored", True,),
        description="If a mention of pneumonia occurs in 'INDICATION' and is not modified by a positive modifier, "
                    "set is_ignored to True. This will also include the first line of the report text if it is not given a section."
    ),
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent:ent.label_ in TARGET_CONCEPTS),
            PostprocessingPattern(lambda ent: check_anatomy(ent, r"pulmonary arter", regex=True)),
        ],
        action=set_custom_attribute, action_args=("is_ignored", True,),
        description="If a mention of a term like opacified refers to pulmonary artery, ignore it."
    ),

    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: get_literal(ent) == "acute chest disease"),
            PostprocessingPattern(lambda ent: ent._.is_negated is True),
        ],
        action=set_custom_attribute, action_args=("is_ignored", False,),
        description="If the phrase 'acute chest disease' is negated, consider it a negative finding. Otherwise ignore it."
    ),

]
from medspacy.postprocess import postprocessing_functions
from medspacy.postprocess import PostprocessingPattern, PostprocessingRule
from ...constants import PNEUMONIA_CONCEPTS, FINDINGS_CONCEPTS, TARGET_CONCEPTS
from ..common.common_postprocess_rules import set_ignored


postprocess_rules = [

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


]
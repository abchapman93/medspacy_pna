from medspacy.postprocess import postprocessing_functions
from medspacy.postprocess import PostprocessingPattern, PostprocessingRule

from ...constants import TARGET_CONCEPTS, FINDINGS_CONCEPTS, PNEUMONIA_CONCEPTS

def set_ignored(ent, i, value=True):
    ent._.is_ignored = value




postprocess_rules = [
    # 2/8/2022: Moved this to clinical_postprocess_rules.py
    # PostprocessingRule(
    #     patterns=[
    #         PostprocessingPattern(lambda ent: ent.label_ in PNEUMONIA_CONCEPTS),
    #         PostprocessingPattern(lambda ent: ent._.section_category == "medications"),
    #
    #     ],
    #     action=set_ignored,
    #     description="Ignore mentions of pneumonia in the 'medications' section"
    # ),

]
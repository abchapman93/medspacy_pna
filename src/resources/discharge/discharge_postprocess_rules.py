from medspacy.postprocess import postprocessing_functions
from medspacy.postprocess import PostprocessingPattern, PostprocessingRule
from ...constants import PNEUMONIA_CONCEPTS, FINDINGS_CONCEPTS, TARGET_CONCEPTS

postprocess_rules = [
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ in TARGET_CONCEPTS),
            PostprocessingPattern(lambda ent: ent._.section_category in ("history_of_present_illness", "admission_diagnoses")),
        ],
        action=postprocessing_functions.set_historical, action_args=(True,),
        description="If a mention of pneumonia occurs in the HPI in a discharge summary, "
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
from medspacy.postprocess import postprocessing_functions
from medspacy.postprocess import PostprocessingPattern, PostprocessingRule
from ...constants import PNEUMONIA_CONCEPTS, FINDINGS_CONCEPTS, TARGET_CONCEPTS
from ..common.common_postprocess_rules import set_ignored

RAD_TERMS = {
        "cxr", "imaging", "image", "contrast", "ct",
        "technique", "procedure", "radiology",
        "clinical correlation", "reading physician",
    "x-ray", "xray"
        }

RELEVANT_SECTIONS = {

        "observation_and_plan",
        "discharge_diagnoses",
        "addendum",
        "impression", # May need to disambiguate this from imaging

        "medical_decision_making",
        "hospital_course",
        "admission_diagnoses"
}

def disambiguate_impression(span, section_title, window_size=5):
    """Disambiguate whether the sections 'Impression' and 'Addendum:' are referring to
    radiology or clinical sections.

    Returns True if 'impression' should refer to imaging.

    span: The target
    section_title: The section title to look at for disambiguation. Will check the preceding section to attempt and make a decision based on the note structure
    window_size: The window around span to look for radiology terms
    """
    # print("Here!")
    # First, check if the preceding section was imaging
    preceding_idx = section_title.start-1
    if preceding_idx >= 0:
    # try:
        preceding_token = section_title.doc[section_title.start-1]
        # print(span, section_title)
        # print(preceding_token, preceding_token._.section_title)
        # print(preceding_token)
        # print(preceding_token._.section_category)
        # If it's preceded by 'Impression', then this will need to be disambiguated as well
        # so go back another section
        if preceding_token._.section_title.text.lower().startswith("impression") and preceding_token._.section_category == "impression":
            # return
            return disambiguate_impression(span, preceding_token._.section_title, window_size=window_size)
        if preceding_token._.section_category in (
                "imaging",
                # "labs_and_studies",
            "procedures"
        ):
            return True
        if preceding_token._.section_title._.contains(r"indication|finding|studies", case_insensitive=True, regex=True):
            return True
    # except IndexError:
    #     pass

    # NOw look for imaging terms in the neighborhood of the span
    window_span = span._.window(window_size)
    window_title = section_title._.window(window_size, left=True, right=False)
    # print("IMpression:", window, window_size)
    # print(window)
    # window = {token.text.lower() for token in span._.window(window_size)}
    # print(RAD_TERMS)
    # print("WSD:", window)
    for window in (window_span, window_title):
        # print(window)
        if window._.contains("|".join(RAD_TERMS), regex=True, case_insensitive=True):
            return True

    return False

def change_ent_section(ent, i, value):
    ent._.section.category = value

def disambiguate_cap(ent):
    """Attempt to disambiguate whether 'CAP' refers to a medication or community-acquired pneumonia.
    Returns False if it appears to be medication-related.
    Returns True if it appears to be pneumonia.
    """
    if ent._.section_category == "medications":
        return False
    if ent.sent._.contains(r"mg|medication|capsule|mouth|po|oral|qday|zole|refill", regex=True, case_insensitive=True):
        return False
    if ent._.window(3)._.contains(r"[0-9]", regex=True):
        return False
    return True

postprocess_rules = [
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent._.section_category in ("impression", "addendum")),
            PostprocessingPattern(lambda ent: ent._.section_title._.contains("(diagnos|<<ADDENDUM>>)", regex=True, case_insensitive=True) is False),
            PostprocessingPattern(lambda ent: disambiguate_impression(ent, ent._.section_title, window_size=5)),
            # PostprocessingPattern(lambda ent: section_preceding(ent) == "")
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
            PostprocessingPattern(lambda ent: ent.text.lower() == "cap"),
            PostprocessingPattern(disambiguate_cap),
        ],
        action=set_ignored,
        action_args=(False,),
        description="In the medications, disambiguate 'CAP'."
    ),

    # PostprocessingRule(
    #     patterns=[
    #         PostprocessingPattern(lambda ent: ent.text.lower() == "cap"),
    #         PostprocessingPattern(lambda ent: ent._.is_ignored is True),
    #     ],
    #     action=postprocessing_functions.remove_ent,
    #     description="Ignore disambiguated mentions of CAP"
    # ),


]
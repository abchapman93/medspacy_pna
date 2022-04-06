from spacy.language import Language

from .document_classifier import BaseDocumentClassifier

TARGET_CLASSES = {"PNEUMONIA", "HOSPITAL_ACQUIRED_PNEUMONIA"}

ENTITY_ATTRIBUTES = {
        "is_negated": False, # Keep negations as part of the classification logic
        "is_hypothetical": False,
        "is_historical": False,
        "is_family": False,
        # "is_uncertain": False,
        "is_ignored": False
}

CLINICAL_CLASSES = {
    "PNEUMONIA", "HOSPITAL_ACQUIRED_PNEUMONIA"

}

RADIOGRAPHIC_CLASSES = {
    "INFILTRATE",
    "OPACITY",
    "CONSOLIDATION",
    "RAD_PNEUMONIA", # Terms for pneumonia specific to radiology
}

RELEVANT_SECTIONS = {

    # "observation_and_plan",

    # "addendum",
    # "impression", # May need to disambiguate this from imaging
    "diagnoses",
    "discharge_diagnoses",
    "hospital_course",
}

TIER_1_SECTIONS = {
    "diagnoses",
    "discharge_diagnoses",
}

TIER_2_SECTIONS = {
    "hospital_course"
}

@Language.factory("pneumonia_dischargedocumentclassifier")
class DischargeDocumentClassifier(BaseDocumentClassifier):
    domain = "discharge"

    schemas = ("full", "keywords", "attributes", "diagnoses")

    def __init__(self, nlp, name="pneumonia_dischargedocumentclassifier", classification_schema=None, debug=False):
        self.nlp = nlp
        self.name = name
        if classification_schema is None:
            classification_schema = "full"
        super().__init__(classification_schema=classification_schema, debug=debug)

    @property
    def relevant_classes(self):
        return TARGET_CLASSES

    def is_relevant_class(self, label):
        return label in self.relevant_classes.union(RADIOGRAPHIC_CLASSES)

    def gather_ent_data(self, doc):

        ent_data = {
            "TIER_1": {
            "asserted": [],
            "uncertain": [],
            "negated": []
        },
            "TIER_2": {
            "asserted": [],
            "uncertain": [],
            "negated": []
        },
            "TIER_3": {
            "asserted": [],
            "uncertain": [],
            "negated": []
        },
        }


        for ent in doc.ents:
            if not self.is_relevant_class(ent.label_):
                continue
            if ent._.section_category in TIER_1_SECTIONS:
                tier = "TIER_1"
            elif ent._.section_category in TIER_2_SECTIONS:
                # print("Here!!!")
                # print(ent, ent._.section_category)
                tier = "TIER_2"
            else:
                tier = "TIER_3"
            # print(ent._.section_category, tier)
            # if ent._.section_category not in RELEVANT_SECTIONS:
            #    continue
            # print(ent, label_domain)
            is_excluded = False
            # Check if any of the attributes don't match required values (ie., is_negated == True)
            for (attr, req_value) in ENTITY_ATTRIBUTES.items():
                # This entity won't count as positive evidence, move onto the next one
                if getattr(ent._, attr) != req_value:
                    is_excluded = True
                    break

            if not is_excluded:
                # 10/2: only allow clinical classes to be positive/asserted
                if ent.label_ in CLINICAL_CLASSES:
                    if ent._.is_uncertain:
                        ent_data[tier]["uncertain"].append(ent)

                    else:
                        ent_data[tier]["asserted"].append(ent)
            # But keep negated mentions
            elif ent._.is_negated and not ent._.is_ignored:
                ent_data[tier]["negated"].append(ent)

        return ent_data

    # TODO: move this to base class
    def is_excluded_attr(self, ent):
        for (attr, req_value) in ENTITY_ATTRIBUTES.items():
            # This entity won't count as positive evidence, move onto the next one
            if getattr(ent._, attr) != req_value:
                return True
        return False

    def gather_sects(self, doc):
        # Check whether there is a Tier 1 section
        tiers_in_doc = set()
        for sect in doc._.section_categories:
            if sect in TIER_1_SECTIONS:
                tiers_in_doc.add("TIER_1")
            elif sect in TIER_2_SECTIONS:
                tiers_in_doc.add("TIER_2")
            else:
                tiers_in_doc.add("TIER_3")
        return tiers_in_doc


    def classify_document_discharge(self, doc, sect_tiers=("TIER_1", "TIER_2"), invalidate_lower_tier=False):
        """
        10/7/2021:
        - Split sections into two types: 'TIER_1' includes 'Diagnoses', 'Final Dx:', 'Tier_2' includes 'Hospital Course'
        - If only 'Tier_1' is passed in, then we will just look at those sections
        - If there are any asserted mention in any allowed sections --> 'POS'
        - If there is uncertain: 
            -If there is uncertain in a lower tier and negated in a higher tier, --> 'NEG'
            - Otherwise, --> 'POSSIBLE'
        - --> 'NEG'
        """
        ent_data = self.gather_ent_data(doc)

        sects_in_doc = self.gather_sects(doc)

        # print(ent_data)
        if self.debug:
            print(ent_data)
        asserted = []
        uncertain = []
        negated = []
        for tier in sect_tiers:
            # IF there is a higher tier like 'Final Diagnoses' in the doc, don't consider any lower tiers
            if invalidate_lower_tier and tier == "TIER_2" and "TIER_1" in sects_in_doc:
                continue
            asserted += ent_data[tier]["asserted"]
            uncertain += ent_data[tier]["uncertain"]
            negated += ent_data[tier]["negated"]
        # print(sect_tiers)
        # print(asserted)
        # print(uncertain)

        if asserted:
            return "POS"
        if uncertain:
            # if there was uncertainty in a lower tier and negation in a higher tier, return negative
            if ent_data["TIER_2"]["uncertain"] and ent_data["TIER_1"]["negated"]:
                return "NEG"
            else:
                return "POSSIBLE"
        return "NEG"

        # 2. If there is uncertain evidence in Tier 1/Tier 2 or asserted evidence in Tier 2,
        # check if these mentions are followed by any negated entities. If so, "NEG"
        # IF there are no final negations, "POSSIBLE"
        # ie., "MDM: Possible pneumonia... A/P: No pneumonia"
        negated_ents = (
                ent_data["TIER_1"]["radiographic"]["negated"]
                + ent_data["TIER_2"]["radiographic"]["negated"]
                + ent_data["TIER_3"]["radiographic"]["negated"] # TODO: This might be bad
                + ent_data["TIER_1"]["clinical"]["negated"]
                + ent_data["TIER_2"]["clinical"]["negated"]
                + ent_data["TIER_3"]["clinical"]["negated"] # TODO: This might be bad
        )
        negated_ents = sorted(negated_ents, key=lambda x: x.start)
        uncertain_ents = ent_data["TIER_1"]["clinical"]["uncertain"] + ent_data["TIER_2"]["clinical"]["asserted"] + ent_data["TIER_2"]["clinical"]["uncertain"]
        uncertain_ents = sorted(uncertain_ents, key=lambda x:x.start)
        if uncertain_ents:
            # Check for Tier 2 evidence after the last uncertain mention
            # Then we should call this negative
            final_uncertain = uncertain_ents[-1]
            try:
                final_tier_2_negated = negated_ents[-1]
                if final_tier_2_negated.start > final_uncertain.start:
                    return "NEG"
            except IndexError:
                pass
            return "POSSIBLE"
        if ent_data["TIER_1"]["clinical"]["negated"]:
            return "NEG"

        # # 2.
        # if ent_data["TIER_2"]["clinical"]["asserted"] or ent_data["TIER_2"]["clinical"]["uncertain"]:
        #     if ent_data["TIER_1"]["radiographic"]["negated"] or ent_data["TIER_2"]["radiographic"]["negated"]:
        #         return "NEG"
        #     else:
        #         return "POSSIBLE"
        return "NEG"

    def classify_document_attributes(self, doc):
        """Document logic:
        1. Is there clinical evidence in the A/P or another Tier 1 section: --> 'POS' or 'POSSIBLE'
        2. If absent, is there any clinical evidence in other relevant sections?
            2a. If no or negative --> 'NEG'
            2b. If there is + or possible evidence, is there radiographic evidence in a relevant section?
                If negative, --> 'NEG'
                Otherwise, 'POSSIBLE'
        """
        ent_data = self.gather_ent_data(doc)
        asserted = ent_data["TIER_1"]["asserted"] + ent_data["TIER_2"]["asserted"] + ent_data["TIER_3"]["asserted"]
        uncertain = ent_data["TIER_1"]["uncertain"] + ent_data["TIER_2"]["uncertain"] + ent_data["TIER_3"]["uncertain"]
        # negated = ent_data["TIER_1"]["negated"] + ent_data["TIER_2"]["negated"] + ent_data["TIER_3"]["negated"]

        if asserted:
            return "POS"
        elif uncertain:
            return "POSSIBLE"
        return "NEG"

    def classify_document_keywords(self, doc):
        for ent in doc.ents:
            if ent.label_ == "PNEUMONIA":
                return "POS"
        return "NEG"

    def _classify_document(self, doc, classification_schema=None, **kwargs):
        if classification_schema is None:
            classification_schema = self.classification_schema
        # print(schema)
        if classification_schema == "full":
            return self.classify_document_discharge(doc)
        elif classification_schema == "keywords":
            return self.classify_document_keywords(doc)
        elif classification_schema == "attributes":
            return self.classify_document_attributes(doc)
        elif classification_schema == "diagnoses":
            return self.classify_document_discharge(doc, sect_tiers=("TIER_1",))
        else:
            raise ValueError("Invalid classification_schema:", classification_schema)

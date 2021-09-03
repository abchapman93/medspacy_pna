from .document_classifier import BaseDocumentClassifier

TARGET_CLASSES = {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"}

CLINICAL_CLASSES = {
    "PNEUMONIA",

}

RADIOGRAPHIC_CLASSES = {
    "INFILTRATE",
    "OPACITY",
    "CONSOLIDATION",
    "RAD_PNEUMONIA", # Terms for pneumonia specific to radiology
}

ENTITY_ATTRIBUTES = {
        "is_negated": False, # Keep negations as part of the classification logic
        "is_hypothetical": False,
        "is_historical": False,
        "is_family": False,
        # "is_uncertain": False,
        "is_ignored": False
}

RELEVANT_SECTIONS = {
    "TIER_1": {
        "observation_and_plan",
        "discharge_diagnoses",
        "addendum",
        "impression", # May need to disambiguate this from imaging
        "diagnoses",
    },
    "TIER_2": {
        "medical_decision_making",
        "hospital_course",
        "admission_diagnoses"
    }
}

class EmergencyDocumentClassifier(BaseDocumentClassifier):
    domain = "radiology"

    def __init__(self):
        super().__init__()

    @property
    def relevant_classes(self):
        return CLINICAL_CLASSES.union(RADIOGRAPHIC_CLASSES)

    def is_relevant_class(self, label):
        return label in self.relevant_classes

    def gather_ent_data(self, doc):
        # TODO: Clean this up
        ent_data = {
            "TIER_1": {
                "clinical": {
                    "asserted": [],
                    "uncertain": [],
                    "negated": []
                },
                "radiographic": {
                    "asserted": [],
                    "uncertain": [],
                    "negated": []
                },
            },
         "TIER_2": {
             "clinical": {
                 "asserted": [],
                 "uncertain": [],
                 "negated": []
             },
             "radiographic": {
                 "asserted": [],
                 "uncertain": [],
                 "negated": []
             },
            },
            "TIER_3": {
                "clinical": {
                    "asserted": [],
                    "uncertain": [],
                    "negated": []
                },
                "radiographic": {
                    "asserted": [],
                    "uncertain": [],
                    "negated": []
                },
            }, "TIER_3": {
             "clinical": {
                 "asserted": [],
                 "uncertain": [],
                 "negated": []
             },
             "radiographic": {
                 "asserted": [],
                 "uncertain": [],
                 "negated": []
             },
            }
        }

        for ent in doc.ents:
            if ent.label_ in CLINICAL_CLASSES:
                label_domain = "clinical"
            elif ent.label_ in RADIOGRAPHIC_CLASSES:
                label_domain = "radiographic"
            else:
                continue
            if ent._.section_category in RELEVANT_SECTIONS["TIER_1"]:
                sec_tier = "TIER_1"
            elif ent._.section_category in RELEVANT_SECTIONS["TIER_2"]:
                sec_tier = "TIER_2"
            else:
                sec_tier = "TIER_3"
                # continue
            # print(ent, label_domain)
            is_excluded = False
            # Check if any of the attributes don't match required values (ie., is_negated == True)
            for (attr, req_value) in ENTITY_ATTRIBUTES.items():
                # This entity won't count as positive evidence, move onto the next one
                if getattr(ent._, attr) != req_value:
                    is_excluded = True
                    break
            if not is_excluded:
                if ent._.is_uncertain:
                    ent_data[sec_tier][label_domain]["uncertain"].append(ent)
                else:
                    ent_data[sec_tier][label_domain]["asserted"].append(ent)
            elif ent._.is_negated:
                ent_data[sec_tier][label_domain]["negated"].append(ent)
        return ent_data

    # TODO: move this to base class
    def is_excluded_attr(self, ent):
        for (attr, req_value) in ENTITY_ATTRIBUTES.items():
            # This entity won't count as positive evidence, move onto the next one
            if getattr(ent._, attr) != req_value:
                return True
        return False

    def classify_document_emergency(self, doc):
        """Document logic:
        1. Is there clinical evidence in the A/P or another Tier 1 section: --> 'POS' or 'POSSIBLE'
        2. If absent, is there any clinical evidence in other relevant sections?
            2a. If no or negative --> 'NEG'
            2b. If there is + or possible evidence, is there radiographic evidence in a relevant section?
                If negative, --> 'NEG'
                Otherwise, 'POSSIBLE'
        """
        ent_data = self.gather_ent_data(doc)
        # print(ent_data)
        # 1.
        if ent_data["TIER_1"]["clinical"]["asserted"]:
            return "POS"
        if ent_data["TIER_1"]["clinical"]["uncertain"]:

            return "POSSIBLE" # TODO: Do we need to look at tier 2 evidence here?
        if ent_data["TIER_1"]["clinical"]["negated"]:
            return "NEG"

        # 2.
        if ent_data["TIER_2"]["clinical"]["asserted"] or ent_data["TIER_2"]["clinical"]["uncertain"]:
            if ent_data["TIER_1"]["radiographic"]["negated"] or ent_data["TIER_2"]["radiographic"]["negated"]:
                return "NEG"
            else:
                return "POSSIBLE"
        return "NEG"

    def classify_document_emergency_attributes(self, doc):
        """Document logic:
        1. Is there clinical evidence in the A/P or another Tier 1 section: --> 'POS' or 'POSSIBLE'
        2. If absent, is there any clinical evidence in other relevant sections?
            2a. If no or negative --> 'NEG'
            2b. If there is + or possible evidence, is there radiographic evidence in a relevant section?
                If negative, --> 'NEG'
                Otherwise, 'POSSIBLE'
        """
        ent_data = self.gather_ent_data(doc)
        asserted = ent_data["TIER_1"]["clinical"]["asserted"] + ent_data["TIER_2"]["clinical"]["asserted"] + ent_data["TIER_3"]["clinical"]["asserted"]
        uncertain = ent_data["TIER_1"]["clinical"]["uncertain"] + ent_data["TIER_2"]["clinical"]["uncertain"] + ent_data["TIER_3"]["clinical"]["uncertain"]
        negated = ent_data["TIER_1"]["clinical"]["negated"] + ent_data["TIER_2"]["clinical"]["negated"] + ent_data["TIER_3"]["clinical"]["negated"]

        if asserted:
            return "POS"
        elif uncertain:
            return "POSSIBLE"
        return "NEG"

    def classify_document_emergency_keywords(self, doc):
        for ent in doc.ents:
            if ent.label_ == "PNEUMONIA":
                return "POS"
        return "NEG"




    def classify_document_emergency_old(self, doc):
        section_ents = {
            "TIER_1": {"POSSIBLE": [], "POS": [], "NEG": []},
            "TIER_2": {"POSSIBLE": [], "POS": [], "NEG": []},
        }
        # First, sort the ents into relevant sections
        for ent in doc.ents:
            if not self.is_relevant_class(ent.label_):
                continue
            # See if the ent is excluded by attributes
            if self.is_excluded_attr(ent):
                continue

            sect = ent._.section_category
            for tier in ["TIER_1", "TIER_2"]:
                if sect in RELEVANT_SECTIONS[tier]:
                    if ent._.is_negated is True:
                        section_ents[tier]["NEG"].append(ent)
                    elif ent._.is_uncertain is True:
                        section_ents[tier]["POSSIBLE"].append(ent)
                    else:
                        section_ents[tier]["POS"].append(ent)

        # Now first check tier 1, then tier 2 sections for positive/uncertain
        if section_ents["TIER_1"]["POS"]:
            return "POS"
        if section_ents["TIER_1"]["POSSIBLE"]:
            return "POSSIBLE"
        if section_ents["TIER_2"]["POS"] or section_ents["TIER_2"]["POSSIBLE"]:
            # Check if there are any negated entities

            return "POSSIBLE"
        # for tier in ["TIER_1", "TIER_2"]:
        #     if section_ents[tier]["POS"]:
        #         return "POS"
        #     if section_ents[tier]["POSSIBLE"]:
        #         return "POSSIBLE"
        return "NEG"

    def _classify_document(self, doc, **kwargs):
        schema = kwargs.get("schema", "full")
        if schema == "full":
            return self.classify_document_emergency(doc)
        elif schema == "keywords":
            return self.classify_document_emergency_keywords(doc)
        elif schema == "attributes":
            return self.classify_document_emergency_attributes(doc)
        else:
            raise ValueError("Invalid schema:", schema)

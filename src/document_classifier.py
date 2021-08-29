# Classes which can be counted as positive evidence
# Currently all identical but may change to be more specific (ie., don't allow opacity in DC)
DOMAIN_TARGET_CLASSES = {
    "emergency": {"PNEUMONIA",
                  # "CONSOLIDATION", "INFILTRATE", "OPACITY"
                  },
    "radiology": {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"
                  },
    "discharge": {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"},
}

TIER_1_CLASSES = {
    "PNEUMONIA",
    "CONSOLIDATION",

}

TIER_2_CLASSES = {
    "INFILTRATE",
    "OPACITY",
}

ALTERNATE_DIAGNOSES = {
        "ATELECTASIS",
        "PULMONARY_EDEMA",
        # "SOFT_TISSUE_ATTENUATION",
        # "PLEURAL_EFFUSION",
        # "EMPHYSEMA",
        "INTERSTITIAL_LUNG_DISEASE",
        "FIBROSIS",

}
# For each domain, define what values these attributes must have.
# Otherwise a mention of pneumonia won't count as positive evidence
DOMAIN_ENTITY_ATTRIBUTES = {
    "emergency": {
        # "is_negated": False, # Keep negations as part of the classification logic
        "is_hypothetical": False,
        "is_historical": False,
        "is_family": False,
        # "is_uncertain": False,
        "is_ignored": False
    },
    "radiology": {
        "is_negated": False,
        "is_hypothetical": False,
        "is_historical": False,
        "is_family": False,
        # "is_uncertain": True, # Allow uncertain mentions to count as positive in radiology
        "is_ignored": False
    },
    "discharge":  {
        "is_negated": False,
        "is_hypothetical": False,
        "is_historical": False,
        "is_family": False,
        "is_uncertain": False,
        "is_ignored": False
    }
}

link_phrases = [
    "may represent",
    "may be",
    "may be related to",
    "related to",
    "r/t",
    "likely",
    "likely representing",
    "likely represents",
    "consistent with",
    "compatible with",
    "c/w",
    "suggest",
    "may represent",
    "associated",
    "comptaible",
    "due to",
    "worrisome for",
    "suspicious for",
    "secondary to",
    "suggesting",
    "suggests",
]

EMERGENCY_SECTIONS = {
    "TIER_1": {
        "observation_and_plan",
        "discharge_diagnoses",
        "addendum",
        "impression", # May need to disambiguate this from imaging
    },
    "TIER_2": {
        "medical_decision_making",
        "hospital_course",
        "diagnoses",
        "admission_diagnoses"
    }
}

def link_evidence(doc):
    for ent in doc.ents:
        ent._.linked_ents = tuple()
    for (ent, modifier) in doc._.context_graph.edges:
        if ent.label_ in ALTERNATE_DIAGNOSES and modifier.span.lower_ in link_phrases:
            # print(ent, modifier)
            sent = ent.sent
            span = doc[sent.start:ent.start]
            other_ents = span.ents
            for other in other_ents:
                if other.label_ in TIER_2_CLASSES:
                    ent._.linked_ents += (other,)
                    other._.linked_ents += (ent,)


def classify_document_keywords(doc, link_ents=False, domain=None):
    """Classify based *only* on the presence of target entity labels."""
    ent_data = gather_ent_data(doc, link_ents, domain)
    ent_labels = set()
    for (_, sub_ent_labels) in ent_data.items():
        ent_labels.update(sub_ent_labels)
    if ent_labels.intersection(DOMAIN_TARGET_CLASSES[domain]):
        return "POS"
    return "NEG"

def classify_document_radiology_linked(doc, link_ents=True, domain="radiology"):
    """
    """
    return classify_document_attributes(doc, link_ents=True, domain=domain)

def classify_document_radiology_full(doc, link_ents=False, domain="radiology"):
    """
    Radiology logic:
        1. Look for asserted (+ or ?) Tier 1 Evidence --> POS/POSSIBLE
        2. Look for negated (-) Tier 1 Evidence --> NEG
        3. Look for asserted (+ or ?) alternate diagnosis --> NEG
        4. Look for asserted Tier 2 evidence --> POS/POSSIBLE
        5. If nothing, return Neg --> NEG
    """
    ent_data = gather_ent_data(doc, link_ents, domain)
    asserted_ent_labels = ent_data["asserted"]
    uncertain_ent_labels = ent_data["uncertain"]
    negated_ent_labels = ent_data["negated"]

    if asserted_ent_labels.intersection(TIER_1_CLASSES):
        document_classification = "POS"
    elif uncertain_ent_labels.intersection(TIER_1_CLASSES):
        document_classification = "POSSIBLE"
    elif negated_ent_labels.intersection(TIER_1_CLASSES):
        document_classification = "NEG"
    elif asserted_ent_labels.union(uncertain_ent_labels).intersection(ALTERNATE_DIAGNOSES):
        document_classification = "NEG"
    elif asserted_ent_labels.intersection(TIER_2_CLASSES):
        document_classification = "POS"
    elif uncertain_ent_labels.intersection(TIER_2_CLASSES):
        document_classification = "POSSIBLE"
    else:
        document_classification = "NEG"
    return document_classification

def classify_document_attributes(doc, link_ents=False, domain="radiology"):
    ent_data = gather_ent_data(doc, link_ents, domain)
    # print(ent_data)
    asserted_ent_labels = ent_data["asserted"]
    uncertain_ent_labels = ent_data["uncertain"]
    negated_ent_labels = ent_data["negated"]

    if asserted_ent_labels.intersection(TIER_1_CLASSES):
        document_classification = "POS"
    elif uncertain_ent_labels.intersection(TIER_1_CLASSES):
        document_classification = "POSSIBLE"
    elif negated_ent_labels.intersection(TIER_1_CLASSES):
        document_classification = "NEG"
    elif asserted_ent_labels.intersection(TIER_2_CLASSES):
        document_classification = "POS"
    elif uncertain_ent_labels.intersection(TIER_2_CLASSES):
        document_classification = "POSSIBLE"
    else:
        document_classification = "NEG"
    return document_classification

def _is_excluded_attr(ent, domain):
    for (attr, req_value) in DOMAIN_ENTITY_ATTRIBUTES[domain].items():
        # This entity won't count as positive evidence, move onto the next one
        if getattr(ent._, attr) != req_value:
            return True
    return False

def gather_ent_data(doc, link_ents=False, domain="radiology"):
    asserted_ent_labels = set()
    uncertain_ent_labels = set()
    negated_ent_labels = set()
    if link_ents:
        link_evidence(doc)
    for ent in doc.ents:
        if ent.label_ not in TIER_1_CLASSES.union(TIER_2_CLASSES).union(ALTERNATE_DIAGNOSES):
            continue
        is_excluded = _is_excluded_attr(ent, domain)
        # TODO: this is an additional piece of logic around alternate dx, should maybe go somewhere else
        if not is_excluded:
            if link_ents and ent.label_ in TIER_2_CLASSES and len(ent._.linked_ents):
                is_excluded = True
        if not is_excluded:
            if ent._.is_uncertain:
                uncertain_ent_labels.add(ent.label_)
            else:
                asserted_ent_labels.add(ent.label_)

        elif ent._.is_negated:
            negated_ent_labels.add(ent.label_)
    return {
        "asserted": asserted_ent_labels,
        "uncertain": uncertain_ent_labels,
        "negated": negated_ent_labels
    }

def classify_document_emergency(doc, domain="emergency"):
    section_ents = {
        "TIER_1": {"POSSIBLE": [], "POS": [], "NEG": []},
        "TIER_2": {"POSSIBLE": [], "POS": [], "NEG": []},
    }
    # First, sort the ents into relevant sections
    for ent in doc.ents:
        if ent.label_ not in DOMAIN_TARGET_CLASSES[domain]:
            continue
        # See if the ent is excluded by attributes
        if _is_excluded_attr(ent, domain):

            continue

        sect = ent._.section_category
        for tier in ["TIER_1", "TIER_2"]:
            if sect in EMERGENCY_SECTIONS[tier]:
                if ent._.is_negated is True:
                    section_ents[tier]["NEG"].append(ent)
                if ent._.is_uncertain is True:
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
    # return "NEG"



class DocumentClassifier:
    name = "document_classifier"
    classification_algorithms = {
        "radiology": {
            "keywords": classify_document_keywords,
            "attributes": classify_document_attributes,
            "full": classify_document_radiology_full, # also consider alternate diagnoses
            "linked": classify_document_radiology_linked, # also consider alternate diagnoses
        },
        "emergency": {
            "default": classify_document_emergency,
        }
    }

    def __init__(self, domain):
        self.domain = domain


    def gather_ent_data(self, doc, link_ents=False, domain="radiology"):
        asserted_ent_labels = set()
        uncertain_ent_labels = set()
        negated_ent_labels = set()
        if link_ents:
            link_evidence(doc)
        for ent in doc.ents:
            if ent.label_ not in TIER_1_CLASSES.union(TIER_2_CLASSES).union(ALTERNATE_DIAGNOSES):
                continue
            is_excluded = False
            # Check if any of the attributes don't match required values (ie., is_negated == True)
            for (attr, req_value) in DOMAIN_ENTITY_ATTRIBUTES[self.domain].items():
                # This entity won't count as positive evidence, move onto the next one
                if getattr(ent._, attr) != req_value:
                    is_excluded = True
                    # print("Excluding", ent)
                    # print(attr, getattr(ent._, attr))
                    break
            # TODO: this is an additional piece of logic around alternate dx, should maybe go somewhere else
            if not is_excluded:
                if link_ents and ent.label_ in TIER_2_CLASSES and len(ent._.linked_ents):
                    is_excluded = True
            if not is_excluded:
                if ent._.is_uncertain:
                    uncertain_ent_labels.add(ent.label_)
                else:
                    asserted_ent_labels.add(ent.label_)

            elif ent._.is_negated:
                negated_ent_labels.add(ent.label_)
        return {
            "asserted": asserted_ent_labels,
            "uncertain": uncertain_ent_labels,
            "negated": negated_ent_labels
        }

    def classify_document(self, doc, schema="full", normalized=False, link_ents=False):

        if self.domain == "radiology":
            document_classification = self.classification_algorithms["radiology"][schema](doc, link_ents=link_ents, domain="radiology")
        elif self.domain == "emergency":
            document_classification = classify_document_emergency(doc, "emergency")

        elif self.domain == "discharge": # Temporary, not implemented yet
            document_classification = classify_document_emergency(doc, "discharge")
        # if schema == "linked":
        #     ent_data = self.gather_ent_data(doc, link_ents=True)
        # else:
        #     ent_data = self.gather_ent_data(doc, link_ents=link_ents)
        # if self.domain == "radiology":
        #     document_classification = self.classification_algorithms["radiology"][schema](ent_data, "radiology")
        #     # doc._.document_classification = classify_document_radiology_full(doc, ent_data)
        # else:
        #     document_classification = classify_document_radiology_full(ent_data, self.domain)
        if normalized:
            document_classification = self.normalize_classification(document_classification)
        return document_classification

    def normalize_classification(self, document_classification):
        if document_classification == "POSSIBLE":
            return "POS"
        return document_classification



    def __call__(self, doc, schema="linked", normalized=False, link_ents=False):
        doc._.document_classification = self.classify_document(doc, schema, normalized, link_ents)
        return doc





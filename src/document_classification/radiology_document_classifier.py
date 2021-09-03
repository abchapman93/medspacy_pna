from .document_classifier import BaseDocumentClassifier

TARGET_CLASSES = {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"}

ENTITY_ATTRIBUTES = {
        "is_negated": False,
        "is_hypothetical": False,
        "is_historical": False,
        "is_family": False,
        # "is_uncertain": True, # Allow uncertain mentions to count as positive in radiology
        "is_ignored": False
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

LINK_PHRASES = [
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


class RadiologyDocumentClassifier(BaseDocumentClassifier):
    domain = "radiology"

    def __init__(self):
        super().__init__()

    @property
    def relevant_classes(self):
        return TARGET_CLASSES.union(ALTERNATE_DIAGNOSES)

    @property
    def target_classes(self):
        return TARGET_CLASSES

    def is_relevant_class(self, label):
        return label in self.relevant_classes

    def link_evidence(self, doc):
        for ent in doc.ents:
            ent._.linked_ents = tuple()
        for (ent, modifier) in doc._.context_graph.edges:
            if ent.label_ in ALTERNATE_DIAGNOSES and modifier.span.lower_ in LINK_PHRASES:
                # print(ent, modifier)
                sent = ent.sent
                span = doc[sent.start:ent.start]
                other_ents = span.ents
                for other in other_ents:
                    if other.label_ in TIER_2_CLASSES:
                        ent._.linked_ents += (other,)
                        other._.linked_ents += (ent,)

    def gather_ent_data(self, doc, link_ents=False):
        asserted_ent_labels = set()
        uncertain_ent_labels = set()
        negated_ent_labels = set()
        if link_ents:
            self.link_evidence(doc)
        for ent in doc.ents:
            if ent.label_ not in self.relevant_classes:
                continue
            is_excluded = False
            # Check if any of the attributes don't match required values (ie., is_negated == True)
            for (attr, req_value) in ENTITY_ATTRIBUTES.items():
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

    def classify_document_keywords(self, doc):
        """Classify based *only* on the presence of target entity labels."""
        ent_data = self.gather_ent_data(doc, link_ents=False)
        ent_labels = set()
        for (_, sub_ent_labels) in ent_data.items():
            ent_labels.update(sub_ent_labels)
        if ent_labels.intersection(TARGET_CLASSES):
            return "POS"
        return "NEG"

    def classify_document_attributes(self, doc, link_ents=False):
        ent_data = self.gather_ent_data(doc, link_ents=link_ents)
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

    def classify_document_radiology_full(self, doc):
        """
        Radiology logic:
            1. Look for asserted (+ or ?) Tier 1 Evidence --> POS/POSSIBLE
            2. Look for negated (-) Tier 1 Evidence --> NEG
            3. Look for asserted (+ or ?) alternate diagnosis --> NEG
            4. Look for asserted Tier 2 evidence --> POS/POSSIBLE
            5. If nothing, return Neg --> NEG
        """
        ent_data = self.gather_ent_data(doc, link_ents=False)
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

    def classify_document_radiology_linked(self, doc):
        """
        """
        return self.classify_document_attributes(doc, link_ents=True)


    def _classify_document(self, doc, **kwargs):
        schema = kwargs.get("schema", "full")
        if schema == "full":
            return self.classify_document_radiology_full(doc,)
        elif schema == "keywords":
            return self.classify_document_keywords(doc)
        elif schema == "attributes":
            return self.classify_document_attributes(doc)
        elif schema == "linked":
            return self.classify_document_radiology_linked(doc)
        else:
            raise ValueError()

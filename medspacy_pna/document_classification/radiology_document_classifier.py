# Note: To see detailed documentation about these schemas, see the file "nlp_classification_documentation" in Box

from spacy.language import Language

from .document_classifier import BaseDocumentClassifier


DEFAULT_SCHEMA = "linked"

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

@Language.factory("pneumonia_radiologydocumentclassifier")
class RadiologyDocumentClassifier(BaseDocumentClassifier):
    domain = "radiology"
    schemas = (
        "full",
        "attributes", "linked", "keywords")

    def __init__(self, nlp, name="pneumonia_radiologydocumentclassifier", classification_schema=None):
        self.nlp = nlp
        self.name = name
        if classification_schema is None:
            classification_schema = DEFAULT_SCHEMA
        super().__init__(classification_schema=classification_schema)

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
            if ent.label_ in ALTERNATE_DIAGNOSES and modifier.span.text.lower() in LINK_PHRASES:
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
                    # print(ent, attr)
                    is_excluded = True
                    # print("Excluding", ent)
                    # print(attr, getattr(ent._, attr))
                    break
            # TODO: this is an additional piece of logic around alternate dx, should maybe go somewhere else
            if not is_excluded:
                if link_ents and ent.label_ in TIER_2_CLASSES and len(ent._.linked_ents):

                    is_excluded = True
            if not is_excluded:
                # print(ent)
                if ent._.is_uncertain:
                    uncertain_ent_labels.add(ent.label_)
                else:
                    asserted_ent_labels.add(ent.label_)
                    # print(ent, ent.sent, ent._.modifiers)

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
        if self.debug:
            print(ent_data)
        # print(ent_data)
        asserted_ent_labels = ent_data["asserted"]
        uncertain_ent_labels = ent_data["uncertain"]
        negated_ent_labels = ent_data["negated"]

        # print(negated_ent_labels)
        # print(asserted_ent_labels)

        if 0 == 1:
            pass
        # NOTE 9/27: If there is an uncertain Tier 2, bump up to Positive
        elif uncertain_ent_labels.intersection(TIER_1_CLASSES) and asserted_ent_labels.intersection(TIER_2_CLASSES):
            document_classification = "POS"
        # 9/27: prioritize possible over positive
        elif uncertain_ent_labels.intersection(TIER_1_CLASSES):
            document_classification = "POSSIBLE"
        elif asserted_ent_labels.intersection(TIER_1_CLASSES):
            document_classification = "POS"


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
        # raise NotImplementedError("Need to sync with attribute classification")
        ent_data = self.gather_ent_data(doc, link_ents=False)
        asserted_ent_labels = ent_data["asserted"]
        uncertain_ent_labels = ent_data["uncertain"]
        negated_ent_labels = ent_data["negated"]

        if asserted_ent_labels.intersection(TIER_1_CLASSES):
            document_classification = "POS"
        # NOTE 9/27: If there is an uncertain Tier 2, bump up to Positive
        elif uncertain_ent_labels.intersection(TIER_1_CLASSES) and asserted_ent_labels.intersection(TIER_2_CLASSES):
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


    def _classify_document(self, doc, classification_schema=None, **kwargs):
        if classification_schema is None:
            classification_schema = self.classification_schema
        if classification_schema == "full":
            return self.classify_document_radiology_full(doc,)
        elif classification_schema == "keywords":
            return self.classify_document_keywords(doc)
        elif classification_schema == "attributes":
            return self.classify_document_attributes(doc)
        elif classification_schema == "linked":
            return self.classify_document_radiology_linked(doc)
        else:
            raise ValueError("Invalid classification_schema", classification_schema)

# Classes which can be counted as positive evidence
# Currently all identical but may change to be more specific (ie., don't allow opacity in DC)
DOMAIN_TARGET_CLASSES = {
    "emergency": {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"},
    "radiology": {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"},
    "discharge": {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"},
}

# For each domain, define what values these attributes must have.
# Otherwise a mention of pneumonia won't count as positive evidence
DOMAIN_ENTITY_ATTRIBUTES = {
    "emergency": {
        "is_negated": False,
        "is_hypothetical": False,
        "is_historical": False,
        "is_family": False,
        "is_uncertain": False,
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

class DocumentClassifier:
    name = "document_classifier"

    def __init__(self, domain):
        self.domain = domain

    def classify_document(self, doc):
        has_concept = False
        document_classification = "NEG"
        for ent in doc.ents:
            if ent.label_ not in DOMAIN_TARGET_CLASSES[self.domain]:
                continue
            has_concept = True
            is_excluded = False
            # Check if any of the attributes don't match required values (ie., is_negated == True)
            for (attr, req_value) in DOMAIN_ENTITY_ATTRIBUTES[self.domain].items():
                # This entity won't count as positive evidence, move onto the next one
                if getattr(ent._, attr) != req_value:
                    is_excluded = True
                    break
            if not is_excluded:
                # This counts as positive
                document_classification = "POS"
                break
        if has_concept:
            return document_classification
        return "IRREL"

    def __call__(self, doc):
        doc._.document_classification = self.classify_document(doc)
        return doc

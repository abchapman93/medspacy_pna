import textacy
from spacy.tokens import Doc

Doc.set_extension("feature_dict", default=dict(), force=True)

from sklearn.feature_extraction.text import TfidfVectorizer

TARGET_LABELS = {
    # "PN"
}

def extract_ngram(doc_df):
    return doc_df.iloc[0]["bow"]

def extract_label_counts(ents_df):
    return {
        "ASSERTED:"+label: count for (label, count) in
        ents_df["label_"].value_counts().items()
    }

def extract_context_attr_counts(ents_df):
    context_attr_dict = dict()
    for attr in [
        "is_negated",
        "is_hypothetical",
        "is_historical",
        "is_uncertain",
        "is_ignored",
        "is_family"
    ]:
        sub_df = ents_df[ents_df[attr] == True]
        for label in sub_df["label_"]:
            feature_name = f"{attr}:{label}"
            context_attr_dict.setdefault(feature_name, 0)
            context_attr_dict[feature_name] += 1
    return context_attr_dict

def extract_ent_literals(ents_df):
    return {
        "literal:"+literal: count for (literal, count) in
        ents_df["literal"].value_counts().items()
    }

def extract_ent_sections(ents_df):
    return {
        f"SECTION={section}:{label}": count for ((label, section), count) in
    ents_df.groupby(["label_", "section_category"]).size().items()
    }

def extract_section_categories(sections_df):
    sections_df = sections_df[sections_df["section_category"] != "UNK"]
    return {
        f"SECTION:{section}": count for (section, count) in
    sections_df.groupby("section_category").size().items()
    }

def extract_section_titles(sections_df):
    return {
        f"SECTION:{section}": count for (section, count) in
    sections_df.groupby("section_title_text").size().items()
    }

def extract_context_edges_text(context_df):
    return {
        f"{modifier.lower()}==>{ent.lower()}": count for (ent, modifier), count in
    context_df.groupby(["ent_text", "modifier_text", ]).size().items()
    }

def extract_doc_classification(doc_df):
    return {"nlp_document_classification": doc_df.iloc[0]["document_classification"]}

def tokenize_ngrams(text, n=3):
    ngrams = []
    for i in range(1, n+1):
        ngrams += list(textacy.extract.ngrams(nlp.tokenizer(text), i, filter_stops=False, filter_punct=False))
    return ngrams

def doc2tokens(doc):
    tokens = textacy.extract.ngrams(doc, 1, filter_stops=True, filter_punct=True)
    return [token.text.lower() for token in tokens]

def build_idx2word(vectorizer):
    feature_names_arr = vectorizer.get_feature_names()
    idx2word = {i: word for (i, word) in enumerate(feature_names_arr)}
    return idx2word

def doc2bow(doc, vectorizer, idx2word):
    X = vectorizer.transform([doc])
    token_dict = dict()
    rows, cols = X.nonzero()
    for row, col in zip(rows, cols):
        ngram = idx2word[col]
        count = X[row, col]
        token_dict["NGRAM:"+ngram] = count
    return token_dict


class FeatureExtractor:
    name = "feature_extractor"

    def __init__(self, cfg):
        self.cfg = cfg

    def extract_ent_features(self, ents_df, feature_dict=None):
        if feature_dict is None:
            feature_dict = dict()
        for func_dict in self.cfg["ent"]:
            func = func_dict["func"]
            is_asserted = func_dict.get("is_asserted", False)

            feature_dict.update(self._extract_ent_features(func, ents_df, is_asserted=is_asserted))
        return feature_dict

    def _extract_ent_features(self, func, ents_df, is_asserted=False, **kwargs):
        if is_asserted:
            ents_df = ents_df[ents_df["is_asserted"] == True]
        return func(ents_df, **kwargs)

    def extract_section_features(self, sections_df, feature_dict=None):
        if feature_dict is None:
            feature_dict = dict()
        for func_dict in self.cfg["section"]:
            func = func_dict["func"]
            feature_dict.update(self._extract_section_features(func, sections_df))
        return feature_dict

    def _extract_section_features(self, func, section_df, **kwargs):
        return func(section_df, **kwargs)

    def extract_context_features(self, context_df, feature_dict=None):
        if feature_dict is None:
            feature_dict = dict()
        for func_dict in self.cfg["context"]:
            func = func_dict["func"]
            feature_dict.update(self._extract_context_features(func, context_df))
        return feature_dict

    def _extract_context_features(self, func, context_df, **kwargs):
        return func(context_df, **kwargs)

    def extract_doc_features(self, doc_df, feature_dict=None):
        if feature_dict is None:
            feature_dict = dict()
        for func_dict in self.cfg["doc"]:
            func = func_dict["func"]
            feature_dict.update(self._extract_doc_features(func, doc_df))
        return feature_dict

    def _extract_doc_features(self, func, doc_df, **kwargs):
        return func(doc_df, **kwargs)

    def __call__(self, doc):
        feature_dict = {}
        if "ent" in self.cfg:
            ents_df = doc._.to_dataframe("ent")
            ents_df = ents_df[ents_df["label_"].isin(TARGET_LABELS)]
            feature_dict.update(self.extract_ent_features(ents_df, feature_dict))
        if "section" in self.cfg:
            sections_df = doc._.to_dataframe("section")
            self.extract_section_features(sections_df, feature_dict)
        if "context" in self.cfg:
            context_df = doc._.to_dataframe("context")
            self.extract_context_features(context_df, feature_dict)
        if "doc" in self.cfg:
            doc_df = doc._.to_dataframe("doc")
            feature_dict.update(self.extract_doc_features(doc_df, feature_dict))

        doc._.feature_dict = feature_dict
        return doc

cfg = {
    "ent": [
    {"func": extract_label_counts, "is_asserted": True},
    {"func": extract_context_attr_counts},
    {"func": extract_ent_literals, "is_asserted": True},
    {"func": extract_ent_sections}],
    "doc": [
        # {"func": extract_doc_classification},
        {"func": extract_ngram},
    ],
    "section": [
        {"func": extract_section_categories},
        {"func": extract_section_titles}
    ],
    "context": [
          {"func": extract_context_edges_text},
    ],
}
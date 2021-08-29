import medspacy

from medspacy.preprocess import Preprocessor
from medspacy.target_matcher import ConceptTagger
from medspacy.context import ConTextComponent
from medspacy.section_detection import Sectionizer
from medspacy.postprocess import Postprocessor

# from src.resources import callbacks
from medspacy.preprocess import PreprocessingRule
from medspacy.target_matcher import TargetRule
from medspacy.context import ConTextRule
from medspacy.section_detection import SectionRule

# from src.resources import concept_tag_rules, context_rules, target_rules
from src._extensions import set_extensions
from src.resources.common import common_preprocess_rules
from src.resources.common import common_postprocess_rules
from src.resources.emergency import emergency_preprocess_rules, emergency_postprocess_rules
from src.resources.discharge import discharge_postprocess_rules
from src.resources.radiology import radiology_postprocess_rules
from src.document_classifier import DocumentClassifier

import os
from pathlib import Path
import warnings

from src.constants import DOMAINS, CONFIG_FILES

import pytest

RESOURCES_FOLDER = os.path.join(Path(__file__).resolve().parents[0], "resources")

RULE_CLASSES = {
    "concept_tagger": TargetRule,
    "target_matcher": TargetRule,
    "context": ConTextRule,
    "sectionizer": SectionRule
}

SECTION_ATTRS = {
    "emergency": {
        "problem_list": {"is_historical": True},
        "history_of_present_illness": {"is_historical": True},
        "past_medical_history": {"is_historical": True},
        "patient_instructions": {"is_hypothetical": True},
        "medical_decision_making": {"is_uncertain": True}
    }
}

def build_nlp(domain=None, cfg_file=None, model="en_core_web_sm"):
    set_extensions()

    if domain is None and cfg_file is None:
        raise ValueError("Either domain or cfg_file must be provided.")
    elif domain:
        if domain not in DOMAINS:
            raise ValueError("Invalid domain:", domain)
        cfg_file = CONFIG_FILES[domain]
    cfg = load_cfg_file(cfg_file)

    if domain is None:
        domain = cfg.get(domain)
    if domain not in DOMAINS:
        raise warnings.warn("Warning: invalid domain found in config file: " + domain)
    rules = load_rules_from_cfg(cfg)

    if model == "default":
        nlp = medspacy.load(enable=["tokenizer", "sentencizer", "target_matcher"])
    elif model == "en_core_web_sm":
        nlp = medspacy.load("en_core_web_sm", enable=["tokenizer", "target_matcher"])
        nlp.remove_pipe("ner")



    # Add components which aren't loaded by default
    preprocessor = Preprocessor(nlp.tokenizer)
    nlp.tokenizer = preprocessor





    concept_tagger = ConceptTagger(nlp)
    nlp.add_pipe(concept_tagger, before="target_matcher")

    context = ConTextComponent(nlp, rules=None)
    nlp.add_pipe(context, after="target_matcher")

    section_attrs = SECTION_ATTRS.get(domain, False)
    sectionizer = Sectionizer(nlp, rules=None, phrase_matcher_attr="LOWER", add_attrs=section_attrs)
    nlp.add_pipe(sectionizer, after="context")

    debug = False
    postprocessor = Postprocessor(debug=debug)
    nlp.add_pipe(postprocessor)

    clf = DocumentClassifier(domain)
    nlp.add_pipe(clf)

    # Add the rules loaded from the config file
    for (name, component_rules) in rules.items():
        try:
            component = nlp.get_pipe(name)
        except KeyError:
            raise ValueError("Invalid component:", name)
        component.add(component_rules)

    # Don't know how to load the pre/postprocess rules from a config file
    # Maybe something like this: https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    # In the meantime, just manually add
    preprocessor.add(common_preprocess_rules.preprocess_rules)
    postprocessor.add(common_postprocess_rules.postprocess_rules)

    if domain == "discharge":
        postprocessor.add(discharge_postprocess_rules.postprocess_rules)
    if domain == "emergency":
        preprocessor.add(emergency_preprocess_rules.preprocess_rules)
        postprocessor.add(emergency_postprocess_rules.postprocess_rules)
    elif domain == "radiology":
        postprocessor.add(radiology_postprocess_rules.postprocess_rules)
    return nlp

def load_rules_from_cfg(cfg, resources_dir=None):
    if resources_dir is None:
        resources_dir = RESOURCES_FOLDER
    rules = _load_cfg_rules(cfg, resources_dir)
    return rules

def load_cfg_file(filepath):
    import json
    with open(filepath) as f:
        cfg = json.loads(f.read())
    return cfg

def _load_cfg_rules(cfg, resources_dir):
    rules = dict()
    for component, filepaths in cfg["resources"][0].items():
        rule_cls = RULE_CLASSES[component]
        rules[component] = []
        for filepath in filepaths:
            rules[component].extend(rule_cls.from_json(os.path.join(resources_dir, filepath)))
    return rules

def create_connection_sql13(autocommit=True):
    import pyodbc
    conn = pyodbc.connect(
        r'Driver={SQL Server};'
        r'Server=vhacdwsql13.vha.med.va.gov;'
        r'Database=csde_bsv;'
        r'Trusted_connection=yes;',
        autocommit=autocommit # Avoid locking
    )
    return conn

import medspacy

from medspacy.preprocess import Preprocessor
from medspacy.target_matcher import ConceptTagger
from medspacy.context import ConTextComponent
from medspacy.section_detection import Sectionizer
from medspacy.postprocess import Postprocessor

from medspacy.target_matcher import TargetRule
from medspacy.context import ConTextRule
from medspacy.section_detection import SectionRule
from medspacy.preprocess import PreprocessingRule


from medspacy_pna._extensions import set_extensions
from medspacy_pna.resources.common import common_preprocess_rules
from medspacy_pna.resources.emergency import emergency_preprocess_rules, emergency_postprocess_rules
from medspacy_pna.resources.discharge import discharge_postprocess_rules
from medspacy_pna.resources.radiology import radiology_postprocess_rules
from medspacy_pna.resources.clinical import clinical_postprocess_rules

from medspacy_pna.document_classification import RadiologyDocumentClassifier
from medspacy_pna.document_classification import EmergencyDocumentClassifier
from medspacy_pna.document_classification import DischargeDocumentClassifier

import os
from pathlib import Path
import warnings

from medspacy_pna.constants import DOMAINS, CONFIG_FILES

from medspacy.io import DocConsumer

RESOURCES_FOLDER = os.path.join(Path(__file__).resolve().parents[0], "resources")

RULE_CLASSES = {
    "concept_tagger": TargetRule,
    "target_matcher": TargetRule,
    "context": ConTextRule,
    "sectionizer": SectionRule,
    "preprocessor": PreprocessingRule
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

DOC_CONSUMER_ATTRS = {
    "doc": ["document_classification"],
    "ent": [

        "text",
        "literal",
        "start_char",
        "end_char",
        "label_",
        "section_category" ,
        "is_negated",
        "is_uncertain",
        "is_historical",
        "is_hypothetical",
        "is_family",
        "is_ignored",
        "snippet"

            ],
    "section": DocConsumer.get_default_attrs()["section"],
    "context": DocConsumer.get_default_attrs()["context"],
}

def build_all_nlps(domains=("emergency", "radiology", "discharge")):
    """Returns a dict mapping domain names (emergency, radiology, and discharge) to respective NLP models."""
    from collections import OrderedDict
    nlps = OrderedDict()
    for domain in domains:
        nlps[domain] = build_nlp(domain)
    return nlps

# Filter out unnecessary rules to improve efficiency
# This set can be modified or filtering   can be disabled
# in build_nlp if you would like to keep all the categories
TARGET_RULE_CATEGORIES = {
     #    'ABNORMALITY',
     # 'ACTIVE',
     # 'ACUTE',
     # 'AERATION',
     # 'ANATOMY',
     # 'ARTHRITIS',
     'ATELECTASIS',
     # 'ATHEROSCLEROSIS',
     # 'BLUNTING',
     # 'CALCIFICATION',
     'CARDIOPULMONARY_PROCESS',
     # 'CAVITATION',
     # 'CHRONIC',
     # 'COMPRESSIVE',
     'CONSOLIDATION',
     'COVID',
     # 'DENSE',
     # 'DENSITY',
     # 'DESCRIPTOR',
     # 'DIFFUSE',
     # 'EFFUSION',
     # 'EMPHYSEMA',
     'FIBROSIS',
     # 'FOCAL',
     'HOSPITAL_ACQUIRED_PNEUMONIA',
     'IGNORE',
     # 'ILLDEFINED',
     'INFECTION',
     'INFILTRATE',
     # 'INFLAMMATION',
     'INTERSTITIAL_LUNG_DISEASE',
     # 'LINEAR',
     # 'LOCALIZED',
     # 'LOCATION',
     # 'MAXIMAL',
     # 'METASTATIC',
     # 'MINIMAL',
     # 'MODERATE',
     # 'OBSCURATION',
     'OPACITY',
     # 'PATCHY',
     # 'PLEURAL_EFFUSION',
     'PNEUMONIA',
     # 'PULMONARY_EDEMA',
     'RAD_PNEUMONIA',
     # 'ROUNDED',
     # 'SILHOUETTE',
     # 'SOFT_TISSUE_ATTENUATION',
     # 'STRANDY',
     # 'STREAKY',
     'TEMPLATE',
     # 'TORTUOUS',
     # 'TREATMENT'
}

CONTEXT_RULE_CATEGORIES = {
    'DECREASED',
     # 'DESCRIPTOR',
     'FAMILY',
     'HISTORICAL',
     'HYPOTHETICAL',
     'IMPROVED',
     # 'INCREASED',
     # 'LOCALIZED_ANATOMY',
     # 'LOCATION',
     'NEGATED_EXISTENCE',
     'POSITIVE_EXISTENCE',
     'POSSIBLE_EXISTENCE',
     'PSEUDO',
     'RELATION',
     'TERMINATE',
     'UNCHANGED',
    'IGNORE'
     # 'WORSENED'

}

def _filter_target_rules(rules):
    return [r for r in rules if r.category in TARGET_RULE_CATEGORIES]

def _filter_context_rules(rules):
    return [r for r in rules if r.category in CONTEXT_RULE_CATEGORIES]

def build_nlp(domain=None, doc_cls_schema=None, cfg_file=None, model=None, doc_consumer=False,
              filter_categories=True):
    """Loads an NLP model for a specified domain.
    Params:
        domain (str): The name of the clinical domain for the model.
            Valid domain names are "emergency", "radiology", or "discharge".
            If a domain name is provided, one of the default config files contained in `resources/configs` will be loaded.
            If None, a filepath to a config file should be supplied in cfg_file.
        doc_cls_schema (str): Optional name of the document classification schema to use.
            If None, the default values for the document classifiers will be used.
        cfg_file (str): The filepath to a config file to replace the default config file.
            This should be json file with the same format as the default configs.
        model (str): The name of a spaCy model to use as the base model.
            If None, will attempt to load 'en_core_web_sm' and remove unneeded pipes,
                keeping only the tagger and parser which are used for concept extraction and sentence segmentation.
        doc_consumer (bool): Whether to include medspaCy's doc_consumer component, which is useful for
            writing data from processed docs but not needed for the main logic.
            Default False.
        filter_categories (bool): Whether to filter unneeded categories of entities and context rules.

    """
    if domain == "radiology":
        filter_categories = False
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

    if model is None:
        nlp = medspacy.load("en_core_web_sm", enable=["tokenizer", "medspacy_target_matcher"])
        for pipe in ('attribute_ruler', 'ner', 'lemmatizer'):
            nlp.remove_pipe(pipe)
    elif model == "medspacy":
        nlp = medspacy.load(enable=["tokenizer", "sentencizer", "medspacy_target_matcher"])
    else:
        nlp = medspacy.load(model, enable=["medspacy_target_matcher"])

    # Add components which aren't loaded by default
    preprocessor = Preprocessor(nlp.tokenizer)
    nlp.tokenizer = preprocessor





    nlp.add_pipe("medspacy_concept_tagger", before="medspacy_target_matcher")

    context_config = {"rules": None}
    nlp.add_pipe("medspacy_context", after="medspacy_target_matcher", config=context_config)

    # TODO: Cannot figure out how this is getting disabled within the call above to add_pipe()
    # Very confusing how this is happening....
    nlp.enable_pipe("medspacy_context")

    section_attrs = SECTION_ATTRS.get(domain, False)
    sectionizer_config = {"rules": None, 'phrase_matcher_attr': "LOWER", 'add_attrs': section_attrs}
    nlp.add_pipe("medspacy_sectionizer", config = sectionizer_config, after="medspacy_context")

    debug = False
    postprocessor_config = {'debug': debug}
    postprocessor = nlp.add_pipe("medspacy_postprocessor", config = postprocessor_config)

    classifier_pipe_name = None
    if domain == "radiology":
        classifier_pipe_name = "pneumonia_radiologydocumentclassifier"
    elif domain == "emergency":
        classifier_pipe_name = "pneumonia_emergencydocumentclassifier"
    elif domain == "discharge":
        classifier_pipe_name = "pneumonia_dischargedocumentclassifier"
    else:
        raise ValueError("Invalid domain:", domain)

    nlp.add_pipe(classifier_pipe_name, config={"classification_schema": doc_cls_schema})

    # Add the rules loaded from the config file
    for (name, component_rules) in rules.items():
        try:
            # NOTE: This is a bit strange, but it prevents changing lots of references in code
            # to prefix with "medspacy_" when it is only needed here.
            pipe_name = name
            if name in ['concept_tagger', 'context', 'target_matcher', 'sectionizer', 'postprocessor']:
                pipe_name = 'medspacy_' + name

            component = nlp.get_pipe(pipe_name)
        except KeyError:
            raise ValueError("Invalid component:", name)
        if filter_categories and len(component_rules):
            if isinstance(component_rules[0], TargetRule):
                component_rules = _filter_target_rules(component_rules)
            elif isinstance(component_rules[0], ConTextRule):
                component_rules = _filter_context_rules(component_rules)
        component.add(component_rules)

    # Don't know how to load the pre/postprocess rules from a config file
    # Maybe something like this: https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    # In the meantime, just manually add
    preprocessor.add(common_preprocess_rules.preprocess_rules)



    if domain == "discharge":
        postprocessor.add(discharge_postprocess_rules.postprocess_rules)
        postprocessor.add(clinical_postprocess_rules.postprocess_rules)
    if domain == "emergency":
        preprocessor.add(emergency_preprocess_rules.preprocess_rules)
        postprocessor.add(clinical_postprocess_rules.postprocess_rules)
        postprocessor.add(emergency_postprocess_rules.postprocess_rules)
    elif domain == "radiology":
        postprocessor.add(radiology_postprocess_rules.postprocess_rules)

    if doc_consumer:
        consumer_config = {'dtypes': ("ent", "doc"), 'dtype_attrs': DOC_CONSUMER_ATTRS}
        nlp.add_pipe("medspacy_doc_consumer", config = consumer_config)
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
            abspath = os.path.abspath(os.path.join(resources_dir, filepath))

            rules[component].extend(rule_cls.from_json(abspath))
    return rules

def add_additional_resources(nlp, domain, resources_dir):
    """Add custom rules to a pipeline to augment those loaded by build_nlp.
    Params:
        nlp: A spaCy NLP model containing the required components.
        domain: The name of the relevant clinical setting ("emergency", "radiology", or "discharge")
        resources_dir: The folder containing new resources. Should mimic the structure and file name convention
            in resources/. For example:
            - resource_dir/
                - configs/
                    - emergency.json
                    - discharge.json
                - emergency/
                    - emergency_context_rules.json
                ...
    """
    cfg_file = os.path.join(resources_dir, "configs", domain+".json")
    cfg = load_cfg_file(cfg_file)

    rules = _load_cfg_rules(cfg, resources_dir)

    for (name, component_rules) in rules.items():
        if name == "preprocessor":
            component = nlp.tokenizer
        else:
            try:

                # NOTE: This is a bit strange, but it prevents changing lots of references in code
                # to prefix with "medspacy_" when it is only needed here.
                pipe_name = name
                if name in ['concept_tagger', 'context', 'target_matcher', 'sectionizer', 'postprocessor']:
                    pipe_name = 'medspacy_' + name

                component = nlp.get_pipe(pipe_name)
            except KeyError:
                raise ValueError("Invalid component:", name)
        component.add(component_rules)


def get_document_classifier_pipe_name(nlp):
    pipe_name = None
    for pipe_name in nlp.pipe_names:
        if 'document_classifier' in pipe_name or 'documentclassifier' in pipe_name:
            return pipe_name

    return pipe_name

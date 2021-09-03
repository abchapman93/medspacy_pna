import pytest

from src.util import build_nlp, load_cfg_file, load_rules_from_cfg, RESOURCES_FOLDER

import os

class TestLoadPipeline:
    pass
    # def test_load_pipeline(self):
    #     domain = "emergency"
    #     nlp = build_nlp(domain)

    # def test_load_config_file(self):
    #     filepath = "./src/resources/configs/discharge.json"
    #     cfg = load_cfg_file(filepath)
    #     assert cfg

    # def test_load_config_file_new_wd(self):
    #     """Test that the relative paths of the resource files work from another working directory"""
    #     filepath = "./moore-pna/src/resources/configs/discharge.json"
    #     os.chdir("..")
    #     cfg = load_cfg_file(filepath)
    #     assert cfg
    #
    # def test_load_rules_from_config(self):
    #     filepath = "./src/resources/configs/discharge.json"
    #     cfg = load_config_file(filepath)
    #     rules = load_rules_from_cfg(cfg)
    #     assert set(rules.keys()) == {"context", "sectionizer", "target_matcher", "concept_tagger"}
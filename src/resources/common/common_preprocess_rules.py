from medspacy.preprocess import PreprocessingRule
import re

preprocess_rules = [
    PreprocessingRule(re.compile(r"([a-z/])([\r\n\s]{2,})([a-z])"),
                      repl=lambda match: match.group(1) + " " + match.group(3),
                      desc="Replace carriage returns in the middle of sentences with a single space"),
]
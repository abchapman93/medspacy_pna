from medspacy.preprocess import PreprocessingRule
import re

preprocess_rules = [
    PreprocessingRule(re.compile(r"(\*\s|--){2,}[\s]*[\n\r]"),
                      repl=":\n",
                      desc="Sometimes asterisks/dashes are used to indiciate section headers, replace with colons and a newline"),
PreprocessingRule(re.compile(r"[\s ]*\*[\s ]*[\n\r][\s ]*[*]{4,}"),
                      repl=":\n",
                      desc="Sometimes blocks of asterisks are used to indiciate section headers, replace with colons and a newline"),
]
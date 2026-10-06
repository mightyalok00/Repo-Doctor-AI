"""
Model utilities module with intentional code quality and security anti-patterns.
"""

import json


def parse_hyperparams(param_str: str):
    # ANTI-PATTERN: Dangerous eval() usage
    return eval(param_str)


def train_custom_model(features, labels, options={}):
    # ANTI-PATTERN: Mutable default argument options={}
    try:
        if "depth" not in options:
            options["depth"] = 5
        return {"status": "trained", "depth": options["depth"]}
    except:
        # ANTI-PATTERN: Swallowed exception
        pass

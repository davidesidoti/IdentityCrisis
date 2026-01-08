"""
Nickname transformation rules for custom channels.
"""

# Upside down character mapping
UPSIDE_DOWN_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    "ɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz∀qƆpƎℲפHIſʞ˥WNOԀQɹS┴∩ΛMX⅄Z0ƖᄅƐㄣϛ9ㄥ86"
)

# Mirror character mapping
MIRROR_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ɒdɔbɘʇǫʜiįʞlmnoqpɿꙅƚυvwxyzAdƆbƎꟻGHIJʞ⅃MᴎOꟼQЯƧTUVWXYZ"
)

# Leetspeak mapping
LEET_MAP = str.maketrans(
    "aAeEiIoOsStTlL",
    "44331100$$7711"
)


def transform_reverse(nickname: str, value: str = None) -> str:
    """Reverse the nickname."""
    return nickname[::-1]


def transform_upside_down(nickname: str, value: str = None) -> str:
    """Flip the nickname upside down."""
    return nickname.translate(UPSIDE_DOWN_MAP)[::-1]


def transform_mirror(nickname: str, value: str = None) -> str:
    """Mirror the nickname."""
    return nickname.translate(MIRROR_MAP)[::-1]


def transform_leetspeak(nickname: str, value: str = None) -> str:
    """Convert to leetspeak."""
    return nickname.translate(LEET_MAP)


def transform_sarcastic(nickname: str, value: str = None) -> str:
    """AlTeRnAtInG cAsE."""
    result = []
    upper = False
    for char in nickname:
        if char.isalpha():
            result.append(char.upper() if upper else char.lower())
            upper = not upper
        else:
            result.append(char)
    return "".join(result)


def transform_uppercase(nickname: str, value: str = None) -> str:
    """UPPERCASE."""
    return nickname.upper()


def transform_lowercase(nickname: str, value: str = None) -> str:
    """lowercase."""
    return nickname.lower()


def transform_prefix(nickname: str, value: str = None) -> str:
    """Add a prefix."""
    if value:
        return f"{value} {nickname}"
    return nickname


def transform_suffix(nickname: str, value: str = None) -> str:
    """Add a suffix."""
    if value:
        return f"{nickname} {value}"
    return nickname


# Registry of available transformers
TRANSFORMERS = {
    "reverse": transform_reverse,
    "upside_down": transform_upside_down,
    "mirror": transform_mirror,
    "leetspeak": transform_leetspeak,
    "sarcastic": transform_sarcastic,
    "uppercase": transform_uppercase,
    "lowercase": transform_lowercase,
    "prefix": transform_prefix,
    "suffix": transform_suffix,
}

# Human-readable names for the UI
TRANSFORMER_NAMES = {
    "reverse": "Reverse (Mario → oiraM)",
    "upside_down": "Upside Down (Mario → oᴉɹɐW)",
    "mirror": "Mirror (Mario → oiɿɒM)",
    "leetspeak": "Leetspeak (Mario → M4r10)",
    "sarcastic": "Sarcastic (Mario → mArIo)",
    "uppercase": "UPPERCASE",
    "lowercase": "lowercase",
    "prefix": "Add Prefix",
    "suffix": "Add Suffix",
}


def apply_rules(nickname: str, rules: list[dict]) -> str:
    """
    Apply a list of transformation rules to a nickname.
    
    Args:
        nickname: The original nickname
        rules: List of rule dicts, e.g. [{"type": "reverse"}, {"type": "prefix", "value": "[AFK]"}]
    
    Returns:
        Transformed nickname
    """
    result = nickname
    
    for rule in rules:
        rule_type = rule.get("type")
        rule_value = rule.get("value")
        
        if rule_type in TRANSFORMERS:
            result = TRANSFORMERS[rule_type](result, rule_value)
    
    # Discord nickname limit is 32 characters
    return result[:32]
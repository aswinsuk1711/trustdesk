import re


SECRET_PATTERNS = [
    r"reveal\s+(the\s+)?(system|hidden)\s+prompt",
    r"show\s+(me\s+)?(the\s+)?api\s*key",
    r"tell\s+me\s+your\s+secret",
    r"ignore\s+(all\s+)?previous\s+instructions",
]

IDENTITY_BYPASS = [
    r"skip\s+(the\s+)?identity",
    r"bypass\s+(the\s+)?identity",
    r"without\s+verification",
    r"no\s+identity\s+check",
]

COUPON_INJECTION = [
    r"hidden\s+coupon",
    r"internal\s+coupon",
    r"create\s+coupon.*without",
    r"ignore.*policy.*coupon",
]

PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b(?:\d[ -]*?){13,16}\b",
]


def inspect_untrusted(text: str) -> tuple[bool, str]:
    normalized = text.lower()

    for pattern in SECRET_PATTERNS:
        if re.search(pattern, normalized):
            return False, "blocked_secret_or_prompt_disclosure"

    for pattern in IDENTITY_BYPASS:
        if re.search(pattern, normalized):
            return False, "blocked_identity_check_bypass"

    for pattern in COUPON_INJECTION:
        if re.search(pattern, normalized):
            return False, "blocked_hidden_coupon_injection"

    for pattern in PII_PATTERNS:
        if re.search(pattern, text):
            return False, "blocked_possible_pii"

    return True, "passed"

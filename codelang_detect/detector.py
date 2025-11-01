from collections import defaultdict
from ._patterns import PATTERNS 

def detect(code: str) -> str:
    """
    Detects the programming language of a code snippet.

    Args:
        code: A string containing the code to analyze.

    Returns:
        The file extension of the detected language as a lowercase string
        (e.g., 'py', 'js', 'cs'), or 'unknown' if no language could be
        confidently identified.
    """
    if not code or not code.strip():
        return 'unknown'

    match_counts = defaultdict(int)
    for lang, rules in PATTERNS.items():
        for regex, weight in rules:
            if regex.search(code):
                match_counts[lang] += weight

    if not match_counts or all(v == 0 for v in match_counts.values()):
        return 'unknown'

    return max(match_counts, key=match_counts.get)
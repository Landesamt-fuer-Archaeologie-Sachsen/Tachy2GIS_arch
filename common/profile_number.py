
# Field length of prof_nr in profildata_gcp_points (plan.py creates the field with it).
PROFILE_NUMBER_MAX_LENGTH = 20

# Character classes from least to most important
_RANK_PUNCTUATION, _RANK_UNDERSCORE, _RANK_LETTER, _RANK_DIGIT = range(4)


def _rank(char: str) -> int:
    if char.isdigit():
        return _RANK_DIGIT
    if char.isalpha():
        return _RANK_LETTER
    if char == "_":
        return _RANK_UNDERSCORE
    return _RANK_PUNCTUATION


def shorten_profile_number(name: str, max_length: int = PROFILE_NUMBER_MAX_LENGTH) -> str:
    """Shorten ``name`` to ``max_length`` characters by dropping the least important ones.

    Characters are removed one at a time, least important class first and within a class
    from the right, and only as many as needed. ``max_length`` <= 0 means no limit.

    >>> shorten_profile_number("AZB-16_131_AZB-16_136", 20)
    'AZB-16_131_AZB16_136'
    """

    if max_length <= 0 or len(name) <= max_length:
        return name
    chars = list(name)
    for rank in (_RANK_PUNCTUATION, _RANK_UNDERSCORE, _RANK_LETTER, _RANK_DIGIT):
        for i in range(len(chars) - 1, -1, -1):
            if len(chars) <= max_length:
                return "".join(chars)
            if _rank(chars[i]) == rank:
                del chars[i]
    return "".join(chars)

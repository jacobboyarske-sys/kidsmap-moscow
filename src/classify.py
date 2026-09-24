import re

from src.models import AgeLimit

_AGE_BUCKETS = [
    (16, AgeLimit.SIXTEEN_PLUS),
    (12, AgeLimit.TWELVE_PLUS),
    (6, AgeLimit.SIX_PLUS),
    (0, AgeLimit.ZERO_PLUS),
]


def age_text_to_bucket(text: str) -> AgeLimit:
    match = re.search(r"\d+", text)
    age = int(match.group()) if match else 0
    for threshold, bucket in _AGE_BUCKETS:
        if age >= threshold:
            return bucket
    return AgeLimit.ZERO_PLUS

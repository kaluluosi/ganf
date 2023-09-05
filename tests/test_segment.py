import pytest
import nltk
from ganf.segment import segments
from ganf.exceptions import OutOfMaxTokensError


def test_iter(sample: str):
    max_tokens = 1000
    doc = sample

    segs = segments(doc)
    for line in segs:
        tokens = nltk.word_tokenize(line)
        assert len(tokens) < max_tokens


def test_raise_max_tokens_error(sample: str):
    max_tokens = 1
    with pytest.raises(OutOfMaxTokensError):
        doc = sample
        segs = segments(doc, max_tokens=max_tokens)
        for _ in segs:
            continue

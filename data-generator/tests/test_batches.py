from itertools import count, islice

import pytest

from projectbi_generator.repositories.batches import iter_batches


def test_batches_keep_a_strict_bound_and_preserve_input_order():
    batches = iter_batches(count(), 4)
    first = next(batches)
    second = next(batches)
    assert first == [0, 1, 2, 3]
    assert second == [4, 5, 6, 7]
    assert len(first) <= 4 and len(second) <= 4


def test_batches_include_final_partial_chunk():
    assert list(iter_batches(range(10), 4)) == [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]


def test_batches_reject_non_positive_size():
    with pytest.raises(ValueError, match="positivo"):
        list(iter_batches(islice(count(), 1), 0))

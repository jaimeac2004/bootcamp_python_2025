import pytest

from cards_against_humanity.main import (
    CAHDrawingListEmpty,
    T,
    random_subset_choice_with_tracking,
)

"""
types:
- unit -> a * X = b
- integration --> Deck --> draw_black_cards draw_white_cards and random_subset_choice_with_tracking
- regression --> prevent old bugs from coming back
- e2e --> emulates dev infra
- smoke --> 
- stress --> 
- ...
"""


@pytest.mark.parametrize(
    "drawing_list, tracking_list, total, expected_output, expected_drawing_list, expected_tracking_list",
    [
        ([1], [], 1, [1], [], [1]),
        ([1, 1], [2], 1, [1], [1], [2, 1]),
        ([1, 1], [2], 2, [1, 1], [], [2, 1, 1]),
    ],
)
def test_random_subset_choice_with_tracking(
    drawing_list: list[T],
    tracking_list: list[T],
    total: int,
    expected_output: list[T],
    expected_drawing_list: list[T],
    expected_tracking_list: list[T],
):
    real = random_subset_choice_with_tracking(drawing_list, tracking_list, total)

    assert real == expected_output, f"The output is not the expected amount {real=}"
    assert drawing_list == expected_drawing_list
    assert tracking_list == expected_tracking_list


def test_random_subset_choice_with_tracking_error():
    with pytest.raises(CAHDrawingListEmpty):
        _ = random_subset_choice_with_tracking([], [], 1)

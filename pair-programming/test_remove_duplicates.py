import pytest 

def remove_duplicates(nums: list[int]) -> int:
    num_non_duplicates = 0
    for i  in len(nums):
        for j in len(nums):
            if nums[i]!=nums[j] and i!=j:
                nums[i]= nums[j]
                num_non_duplicates += 1
    return num_non_duplicates



def test_remove_duplicates():
    nums = [2,2,22142,31232,22,2,2,2,2,22,2]
    _ = any
    assert remove_duplicates(nums) == 4
    assert nums == [2,22142,31232,22, _, _, _, _, _, _, _]
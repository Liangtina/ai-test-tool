#!/usr/bin/env python3
"""
Bubble Sort Implementation
A simple sorting algorithm that repeatedly steps through the list,
compares adjacent elements and swaps them if they are in wrong order.
"""

def bubble_sort(arr):
    """
    Sort an array using bubble sort algorithm.
    
    Args:
        arr: List of comparable elements to be sorted
        
    Returns:
        Sorted list in ascending order
    """
    n = len(arr)
    
    # Traverse through all array elements
    for i in range(n):
        # Flag to optimize by detecting if array is already sorted
        swapped = False
        
        # Last i elements are already in place
        for j in range(0, n - i - 1):
            # Swap if the element found is greater than the next element
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        
        # If no swapping happened, array is already sorted
        if not swapped:
            break
    
    return arr


def main():
    """Demonstrate bubble sort with example arrays."""
    # Example 1: Unsorted array
    test_array_1 = [64, 34, 25, 12, 22, 11, 90]
    print("Original array:", test_array_1)
    sorted_array_1 = bubble_sort(test_array_1.copy())
    print("Sorted array:", sorted_array_1)
    print()
    
    # Example 2: Reverse sorted array
    test_array_2 = [5, 4, 3, 2, 1]
    print("Original array:", test_array_2)
    sorted_array_2 = bubble_sort(test_array_2.copy())
    print("Sorted array:", sorted_array_2)
    print()
    
    # Example 3: Already sorted array
    test_array_3 = [1, 2, 3, 4, 5]
    print("Original array:", test_array_3)
    sorted_array_3 = bubble_sort(test_array_3.copy())
    print("Sorted array:", sorted_array_3)


if __name__ == "__main__":
    main()

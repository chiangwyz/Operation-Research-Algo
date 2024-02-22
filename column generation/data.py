import numpy as np

# Generate 100 random integers within the range [5, 50]
random_numbers = np.random.randint(5, 51, size=100)

# Convert the array to a string with ', ' as the separator between numbers
random_numbers_str = ', '.join(map(str, random_numbers))


print(random_numbers_str)


elements_int = np.arange(20, 71, 5)
# Generate 100 integers within the [20, 70] range with a step of 5, allowing repetitions
elements_repeated = np.random.choice(elements_int, 100, replace=True)
elements_repeated_str = ', '.join(map(str, elements_repeated))
print(elements_repeated_str)


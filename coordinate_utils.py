import math
import numpy as np

def array_coords_to_square_spiral_index(coords):
    x = coords[..., 0]
    y = coords[..., 1]

    radius = np.maximum(np.abs(x), np.abs(y))
    s = 2 * radius - 1

    out = np.zeros_like(radius)

    mask = radius != 0

    m = mask & (x == radius)
    out[m] = s[m]**2 + (y[m] + radius[m] - 1)

    m = mask & (x == -radius)
    out[m] = (s[m] + 1)**2 + (-y[m] + radius[m])

    m = mask & (y == radius)
    out[m] = s[m]**2 + (2 * radius[m] - 1) + (-x[m] + radius[m])

    m = mask & (y == -radius)
    out[m] = (s[m] + 2)**2 - (-x[m] + radius[m] + 1)

    return out

def coords_to_square_spiral_index(x, y):
	radius = max(abs(x), abs(y))
	if radius == 0: return 0
	starting_perfect_square_root = (radius * 2 - 1)

	spiral_index = 0

	if x == radius:
		spiral_index = (starting_perfect_square_root ** 2) + (y + radius - 1)
	if x == -radius:
		spiral_index = (starting_perfect_square_root + 1) ** 2 + (-y + radius)
	if y == radius:
		spiral_index = (starting_perfect_square_root ** 2) + (2 * radius - 1) + (-x + radius)
	if y == -radius:
		spiral_index = (starting_perfect_square_root + 2) ** 2 - (-x + radius + 1)

	return spiral_index


def square_spiral_index_to_coords(spiral_index):
	# compute coordinates based on square number
	radius = math.floor(math.sqrt(spiral_index))
	if radius % 2 == 0:
		radius -= 1

	radius = math.floor(radius / 2) + 1

	starting_perfect_square_root = (radius * 2 - 1)

	x = radius
	y = -(radius - 1)


	inner_radius = radius - 1

	top_right = (starting_perfect_square_root ** 2) + (2 * inner_radius) + 1
	top_left = (starting_perfect_square_root + 1) ** 2
	bottom_left = (starting_perfect_square_root + 1) ** 2 + (2 * inner_radius) + 2

	if spiral_index <= top_right:
		y = y + (spiral_index - (starting_perfect_square_root ** 2))
	if top_right < spiral_index <= top_left:
		y = radius
		x = x - (spiral_index - top_right)
	if top_left < spiral_index <= bottom_left:
		x = -radius
		y = radius - (spiral_index - top_left)
	if bottom_left < spiral_index < (starting_perfect_square_root + 2) ** 2:
		y = -radius
		x = -radius + (spiral_index - bottom_left)

	return np.array([x, y])


def knight_coords(l_length_multipliers: list[int] = [1]):
	# for a knight attack pattern of len `l_len`
	# times longer than the standard 2-1 
	# hook (i.e. a (l_len * 2, l_len) hook)
	# we need a square-shaped array that is 
	# 2 * (2 * l_len) - 1 long on both sides
	max_l_len = max(l_length_multipliers)
	side = 2 * (2 * max_l_len) + 1
	arr = np.zeros(shape = (side, side))

	center = 2 * max_l_len

	for xm in [-1, 1]:
		for ym in [-1, 1]:
			for l_len_mult in l_length_multipliers:
				arr[center + 2 * l_len_mult * xm, center + 1 * l_len_mult * ym] = 1
				arr[center + 1 * l_len_mult * xm, center + 2 * l_len_mult * ym] = 1

	return arr
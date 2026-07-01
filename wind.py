from PIL import Image
import cv2
import numpy as np
import time
import os
import colorsys
from coordinate_utils import (
	square_spiral_index_to_coords,
	coords_to_square_spiral_index,
	array_coords_to_square_spiral_index
)

def param_sine(array, f = 1, a = 1, power_x = 1.0, power_sine = 1.0):
	return a * (np.sin(f * 2 * np.pi * (array ** power_x)) + 1) ** power_sine

def is_multiple_transform(array, n):
	return ((array % n) == 0)

def mod_scale_power_transform(array, mod, power):
	return (((array % mod) / mod) ** power)

def transform_func(array):
	terms = [
		param_sine(array, power_x = 0.5, f = 2, power_sine = 4) * param_sine(array, power_x = 0.5, f = 0.001, power_sine = 4)
	]

	summed = np.sum(terms, axis = 0)
	zero_min = summed - np.amin(summed)
	scaled = 179 * zero_min / np.amax(zero_min)
	scaled_sv = np.ones_like(scaled) * 255

	hsv_image = np.stack((scaled, scaled_sv, scaled_sv), axis = -1).astype(np.uint8)
	rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)

	rval = np.array(rgb_image, dtype = np.uint8)

	return rval

sidelen = 7001
coords = np.moveaxis(np.indices((sidelen,) * 2), 0, -1) - np.array([sidelen // 2, sidelen // 2])

spiral_coords_array = array_coords_to_square_spiral_index(coords)
transformed = transform_func(spiral_coords_array)

t = int(time.time() * 1000)
os.makedirs(f'outputs/{t}')
img = Image.fromarray(transformed)
img.save(f'outputs/{t}/img.png')
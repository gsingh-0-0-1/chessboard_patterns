from PIL import Image
import cv2
import numpy as np
import time
import os
import colorsys
import matplotlib.pyplot as plt
import inspect
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

def sigmoid(array, k1 = 1):
	return 1 / (1 + np.exp(-array))

def sine_transform(array, p_x = 1, f = 0.001, p_sine = 1):
	terms = [
		param_sine(array, power_x = p_x, f = f, power_sine = p_sine)
	]

	summed = np.sum(terms, axis = 0)
	zero_min = summed - np.amin(summed)
	return zero_min

def multiplied_sine_transform(array, f1 = 1, f2 = 0.001):
	terms = [
		param_sine(array, power_x = 0.5, f = f1, power_sine = 10) *
		param_sine(array, power_x = 0.5, f = f2, power_sine = 10)
	]

	summed = np.sum(terms, axis = 0)
	zero_min = summed - np.amin(summed)
	return zero_min

def two_sine_transform(array, f1 = 1, f2 = 0.001):
	terms = [
		param_sine(array, power_x = 0.5, f = f1, power_sine = 10),
		param_sine(array, power_x = 0.5, f = f2, power_sine = 2)
	]

	summed = np.sum(terms, axis = 0)
	zero_min = summed - np.amin(summed)
	return zero_min

def n_rootx_sines(array, freqs):
	summed = np.sum([param_sine(array, power_x = 0.5, f = f) for f in freqs], axis = 0)
	zero_min = summed - np.amin(summed)


def colorize_hsv(array):
	scaled = (179 * 255 * 255) * array / np.amax(array)
	hue = (scaled / (255 * 255)).astype(np.uint8)
	sat = ((scaled - (hue * 255 * 255)) / 255).astype(np.uint8)
	# i don't want values that are too dark, so i'll scale from 127 to 255
	# val = ((scaled - (hue * 255 * 255) - (sat * 255)) / 2 + 127.5).astype(np.uint8)
	val = ((scaled - (hue * 255 * 255) - (sat * 255))).astype(np.uint8)

	hsv_image = np.stack((hue, sat, val), axis = -1).astype(np.uint8)
	rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)

	rval = np.array(rgb_image, dtype = np.uint8)

	return rval

def colorize_hue(array):
	scaled = 179 * array / np.amax(array)
	scaled_sv = np.ones_like(scaled) * 255

	hsv_image = np.stack((scaled, scaled_sv, scaled_sv), axis = -1).astype(np.uint8)
	rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)

	rval = np.array(rgb_image, dtype = np.uint8)

	return rval

def transformer(array, f, args, compositions = 1):
	transformed = f(array, *args)
	for i in range(1, compositions):
		transformed = f(transformed, *args)

	colored = colorize_hsv(transformed)

	return colored

sidelen = 2001
coords = np.moveaxis(np.indices((sidelen,) * 2), 0, -1) - np.array([sidelen // 2, sidelen // 2])

spiral_coords_array = array_coords_to_square_spiral_index(coords) / 3.0

images = []

for f in np.arange(0.001, 0.015, 0.0001):
	transformed = transformer(spiral_coords_array, two_sine_transform, [2, f])
	images.append(Image.fromarray(transformed))

# add a black screen to the end of the gif
black_frame = Image.fromarray(np.zeros_like(transformed))
for i in range(10):
	images.append(black_frame)

t = int(time.time() * 1000)
os.makedirs(f'outputs/{t}')


images[0].save(
	f'outputs/{t}/img.gif',
	save_all=True,
	append_images=images[1:],
	duration=40,
	loop=0
)

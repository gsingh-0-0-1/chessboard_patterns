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

def colorize_hue(array, s, v):
	scaled = 179 * array / np.amax(array)
	scaled_s = s * np.ones_like(scaled) * 255
	scaled_v = v * np.ones_like(scaled) * 255

	hsv_image = np.stack((scaled, scaled_s, scaled_v), axis = -1).astype(np.uint8)
	rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)

	rval = np.array(rgb_image, dtype = np.uint8)

	return rval

def colorize_sat(array, h, v):
	scaled_h = h * np.ones_like(array) * 255
	scaled_s = 179 * array / np.amax(array)
	scaled_v = v * np.ones_like(array) * 255

	hsv_image = np.stack((scaled_h, scaled_s, scaled_v), axis = -1).astype(np.uint8)
	rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)

	rval = np.array(rgb_image, dtype = np.uint8)

	return rval

def colorize_val(array, h, s):
	scaled_h = h * np.ones_like(array) * 255
	scaled_s = s * np.ones_like(array) * 255
	scaled_v = 179 * array / np.amax(array)

	hsv_image = np.stack((scaled_h, scaled_s, scaled_v), axis = -1).astype(np.uint8)
	rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)

	rval = np.array(rgb_image, dtype = np.uint8)

	return rval

def mandelbrot(array):
	colors = np.zeros_like(array)
	iterations = 30
	bound = 4
	escapes = []
	for i in range(iterations):
		array = array * array + coords
		escapes.append(np.where(array > bound))
		array = np.where(array > bound, 0, array)

	for idx, escape in enumerate(escapes):
		colors[escape] = idx

	return colors

half_sidelen = 2
interval = 0.0005
dim = 2
x = np.arange(-half_sidelen, half_sidelen, interval)
X, Y = np.meshgrid(x, x)
coords = X + 1j * Y



transformed = mandelbrot(coords)
colored = colorize_hsv(np.abs(transformed))
image = Image.fromarray(colored)


t = int(time.time() * 1000)
os.makedirs(f'outputs/{t}')

image.save(f'outputs/{t}/img.png')



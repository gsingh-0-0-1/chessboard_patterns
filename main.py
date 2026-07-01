# import matplotlib.pyplot as plt
import numpy as np
import math
from collections import defaultdict
import copy
import colorsys
import time
import shutil
import os
import json
from PIL import Image
from coordinate_utils import (
	coords_to_square_spiral_index,
	square_spiral_index_to_coords
)


def board_square_dict(attacked_by: set = set(), played_by: int = -1):
	return {
		'attacked_by' : attacked_by,
		'played_by' : played_by
	}

DEFAULT_BOARD_SQUARE_DICT = {'attacked_by' : set(), 'played_by' : -1}

white = np.array([1.0, 1.0, 1.0])

class Board:
	def __init__(self, config):
		self.config = config
		self.radius = config['radius']
		
		self.remove = False if 'remove' not in self.config else True

		self.nplayers = len(config['relative_attack_positions'])

		# I know, I know, "eval is evil"... but I don't care. Eval is easy
		self.relative_attack_positions = [
			eval(item) if type(item) == str else item for item in config['relative_attack_positions']
		]

		self.board = defaultdict(lambda : {'attacked_by' : set(), 'played_by' : -1})
		for i in range(self.radius ** 2):
			if i not in self.board:
				pass
		self.lowest_playables = [0 for i in range(self.nplayers)]
		self.arr = np.zeros(shape = (2 * self.radius + 1, 2 * self.radius + 1, 3)) + 1

		self.colors = np.random.random(size = (self.nplayers, 3)) if config['colors'] == 'random' else np.array(config['colors'])
		assert len(self.relative_attack_positions) == len(self.colors)

		print("Board initialized.")

	def get_attacked_positions(self, n, player_ind):
		coords = square_spiral_index_to_coords(n)
		positions = []

		for pos in self.relative_attack_positions[player_ind]:
			positions.append((coords[0] + pos[0], coords[1] + pos[1]))
		return positions

	def recompute_lowest_playable(self, player_ind):
		# if we have one player, recompute the lowest playable
		# position as needed
		if self.nplayers == 1:
			while self.board[self.lowest_playables[0]] != -1 or self.board[self.lowest_playables[0]]['attacked_by'] != set([]):
				self.lowest_playables[player_ind] += 1
				if self.board[self.lowest_playables[player_ind]] == DEFAULT_BOARD_SQUARE_DICT:
					break
			return

		# if this position happened to be another player's
		# lowest playable position, recompute that player's
		# lowest playable position
		while self.board[self.lowest_playables[player_ind]]['played_by'] != -1 or not (self.board[self.lowest_playables[player_ind]]['attacked_by'] == set() or self.board[self.lowest_playables[player_ind]]['attacked_by'] == set([player_ind])):
			self.lowest_playables[player_ind] += 1

	def attack_position(self, n, player_ind):
		self.board[n]['attacked_by'].add(player_ind)
		if self.remove:
			arrpos = square_spiral_index_to_coords(n)
			self.board[n]['played_by'] = -1
			self.arr[arrpos[0], arrpos[1]] = white
		for p_ind in range(self.nplayers):
			self.recompute_lowest_playable(p_ind)

	def play(self, player_ind):
		if self.board[self.lowest_playables[player_ind]]['played_by'] != -1:
			raise Exception(f"Position {self.lowest_playables[player_ind]} already played by player {self.board[self.lowest_playables[player_ind]]['played_by']}")
			return

		index_to_play = self.lowest_playables[player_ind]
		self.board[index_to_play]['played_by'] = player_ind
		arrpos = square_spiral_index_to_coords(self.lowest_playables[player_ind])
		
		self.arr[arrpos[1] + self.radius, arrpos[0] + self.radius] = self.colors[player_ind]

		for pos in self.get_attacked_positions(self.lowest_playables[player_ind], player_ind):
			self.attack_position(coords_to_square_spiral_index(pos[0], pos[1]), player_ind)

	def clear_old_entries(self, n):
		# helps with saving memory for large generations
		# if we are at spiral index n, we probably don't need to keep
		# entries from spiral index < n

		radius = math.floor(math.sqrt(n))
		thresh = n - 10 * 4 * radius

		deletes = []
		for key in self.board:
			if key < thresh:
				deletes.append(key)

		for d in deletes:
			del self.board[d]



def circle_coords(r, theta_max = 2 * np.pi):
	return list(set([(int(r * math.cos(theta)), int(r * math.sin(theta))) for theta in np.arange(0, theta_max, 0.1 / r)]))

def filled_circle_coords(r):
	l = []
	for x in range(-r, r + 1):
		for y in range(-r, r + 1):
			if x**2 + y**2 <= r ** 2:
				l.append([x, y])

	return l

def knight_coords(l_len = 1):
	l = []

	for xm in [-l_len, l_len]:
		for ym in [-l_len, l_len]:
			l.append([2 * xm, 1 * ym])
			l.append([1 * xm, 2 * ym])

	return l

def plus_shape_coords(length = 1):
	return [[-length, 0], [length, 0], [0, -length], [0, length]]

def main_diagonal_coords(x, y):
	return [[x, y], [-x, -y]]

def off_diagonal_coords(x, y):
	return [[-x, y], [x, -y]]

def x_shape_coords(length = 1):
	return main_diagonal_coords(length, length) + off_diagonal_coords(length, length)
	# return [[-length, -length], [-length, length], [length, -length], [length, length]]

def rook_coords(maxlen = 1):
	l = []
	for i in range(1, maxlen + 1):
		l.append([-i, 0])
		l.append([i, 0])
		l.append([0, -i])
		l.append([0, i])

	return l

def bishop_coords(maxlen = 1):
	l = []
	for i in range(1, maxlen + 1):
		l.append([-i, -i])
		l.append([-i, i])
		l.append([i, -i])
		l.append([i, i])

	return l

def main():
	'''
	CONFIGS = [
		{
		"radius": 2500,
		"nplayers": 3,
		"relative_attack_positions": [
			[
				[7, 1],
				[-7, -1]
			],
			[
				[3, 1],
				[-3, -1]
			],
			[
				[2, 1],
				[-2, -1],
				[11, 0],
				[-11, 0]
			]
			]
		}
	]
	'''

	CONFIGS = [
		{
		"radius": 1000,
		"relative_attack_positions": [
			'knight_coords()',
			'knight_coords()'
		],
		"colors": 'random'
		},
	]


	for config in CONFIGS:
		board = Board(config = config)

		t = int(time.time() * 1000)
		os.makedirs(f'outputs/{t}')
		with open(f'outputs/{t}/config.json', 'w') as f:
			json.dump(board.config, f)

		i = 0
		while True:
			try:
				for player in range(board.nplayers):
					board.play(player)
			except IndexError as e:
				print(e)
				break

			i += 1
			if i % 1000 == 0:
				board.clear_old_entries(min(board.lowest_playables))


			# plt.figure(figsize = (8, 8))
			# plt.imshow(board.arr[::-1])
			#plt.savefig(f'outputs/{t}/board.png')

		array = (board.arr[::-1] * 255).astype(np.uint8)
		img = Image.fromarray(array)
		img.save(f'outputs/{t}/board.png')

		# plt.imshow(board.arr)
		# plt.show()

main()

import matplotlib.pyplot as plt
import numpy as np
import math
from collections import defaultdict
import copy
import colorsys
import time
import shutil
import os

def coords_to_spiral_index(x, y):
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


def spiral_index_to_coords(spiral_index):
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

	return (x, y)


def board_square_dict(attacked_by: set = set(), played_by: int = -1):
	return {
		'attacked_by' : attacked_by,
		'played_by' : played_by
	}

DEFAULT_BOARD_SQUARE_DICT = {'attacked_by' : set(), 'played_by' : -1}

RELATIVE_ATTACK_POSITIONS = np.loadtxt('relative_attack_positions.txt')

class Board:
	def __init__(self, radius = 100, nplayers = 1):
		self.radius = radius
		self.board = defaultdict(lambda : {'attacked_by' : set(), 'played_by' : -1})
		self.lowest_playables = [0 for i in range(nplayers)]
		self.nplayers = nplayers
		self.arr = np.zeros(shape = (2 * radius + 1, 2 * radius + 1, 3)) + 1

	def get_attacked_positions(self, n):
		coords = spiral_index_to_coords(n)
		positions = []

		for pos in RELATIVE_ATTACK_POSITIONS:
			positions.append((coords[0] + pos[0], coords[1] + pos[1]))
		return positions

	def recompute_lowest_playable(self, player_ind):
		# if we have one player, recompute the lowest playable
		# position as needed
		if self.nplayers == 1:
			if self.board[self.lowest_playables[player_ind]] != DEFAULT_BOARD_SQUARE_DICT:
				while True:
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
		for p_ind in range(self.nplayers):
			self.recompute_lowest_playable(p_ind)

	def play(self, player_ind):
		if self.board[self.lowest_playables[player_ind]]['played_by'] != -1:
			raise Exception(f"Position {self.lowest_playables[player_ind]} already played by player {self.board[self.lowest_playables[player_ind]]['played_by']}")
			return

		self.board[self.lowest_playables[player_ind]]['played_by'] = player_ind
		arrpos = spiral_index_to_coords(self.lowest_playables[player_ind])
		
		color = np.array(colorsys.hsv_to_rgb(player_ind / self.nplayers, 1, 1))
		self.arr[arrpos[1] + self.radius, arrpos[0] + self.radius] = color

		for pos in self.get_attacked_positions(self.lowest_playables[player_ind]):
			self.attack_position(coords_to_spiral_index(pos[0], pos[1]), player_ind)


def main():
	board = Board(nplayers = 2, radius = 400)

	while True:
		try:
			for player in range(board.nplayers):
				board.play(player)
		except Exception as e:
			print(e)
			break

	t = int(time.time() * 1000)
	os.makedirs(f'outputs/{t}')
	shutil.copy('relative_attack_positions.txt', f'outputs/{t}/relative_attack_positions.txt')
	plt.imshow(board.arr)
	plt.savefig(f'outputs/{t}/board.png')


	# plt.imshow(board.arr)
	plt.show()

main()

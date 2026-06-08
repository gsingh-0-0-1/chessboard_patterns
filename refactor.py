from dataclasses import dataclass
import numpy as np
import math
from enum import Enum
from coordinate_utils import (
	coords_to_square_spiral_index,
	square_spiral_index_to_coords,
	knight_coords
)
from PIL import Image
import time
import os
import matplotlib.pyplot as plt


class Ordering(Enum):
    SQUARE_SPIRAL_2D = 1
    LINEAR_1D = 2

@dataclass
class BoardMetric:
	extent: list[int]
	ordering: Ordering


class Board:
	def __init__(self, board_metric: BoardMetric, players: list):
		self.board_metric = board_metric
		# each player is represented by an array that shows its attack
		# pattern
		# eg. [0 1 0 1 0
		#      1 0 0 0 1
		#      0 0 0 0 0
		#      1 0 0 0 1
		#      0 1 0 1 0]
		# we will assume that the array will have odd dimension lengths
		# and that the piece is centered in the array
		# So `self.players` a list, since it will have nonuniform
		# dimensions, as there is no need for each player's array
		# to be of the same dimensions. (They should, however, have the 
		# same *dimensionality*).
		self.players = players
		self.nplayers = len(self.players)
		self.lowest_playables = np.zeros(shape = (self.nplayers,), dtype = np.uint32)
		

		# We want the size of the board in the (nplayers + 1)st dimension
		# to have enough space to store:
		# - one space to hold whether or not the board is played
		# - `nplayers` values as flags to indicate if space is attacked by a given player
		#
		# The second through penultimate values will hold potential
		# values of attacking players (default -1)
		# The final value will store the value of the playing piece,
		# if any (default -1)
		board_array_dimensions = tuple(board_metric.extent) + (1 + self.nplayers,)
		self.board = np.zeros(shape = board_array_dimensions)
		self.board[..., 0] = -1

		self.coordinate_ordering = np.zeros(
			shape = (math.prod(self.board_metric.extent), len(self.board_metric.extent)),
			dtype = np.int64
		)

		self.board_metric.half_extent = [int(el / 2) for el in self.board_metric.extent]

		if self.board_metric.ordering == Ordering.SQUARE_SPIRAL_2D:
			for i in range(math.prod(self.board_metric.extent)):
				self.coordinate_ordering[i] = square_spiral_index_to_coords(i) + np.array(self.board_metric.half_extent)

		if self.board_metric.ordering == Ordering.LINEAR_1D:
			for i in range(self.board_metric.extent[0]):
				self.coordinate_ordering[i] = i

		self.turn = 0

	def increment_turn(self):
		self.turn = (self.turn + 1) % self.nplayers

	def recompute_lowest_playables(self):
		for i in range(len(self.players)):
			while True:
				coords = tuple(self.coordinate_ordering[self.lowest_playables[i]])

				# check if the board is played here
				if self.board[coords][0] != -1:
					self.lowest_playables[i] += 1
					continue

				# check if the board is attacked by another player
				# i.e. if the sum of the attacks array is zero
				# OR if the only attackers are itself
				if np.sum(self.board[coords][1:]) == self.board[coords][1 + i]:
					break

				self.lowest_playables[i] += 1


	def play(self):
		player = self.players[self.turn]

		# if self.lowest_playables[self.turn] > self.coordinate_ordering.shape[0]:
		#	return False

		play_at = self.coordinate_ordering[self.lowest_playables[self.turn]]
		# set board
		self.board[tuple(play_at)][0] = self.turn

		# indicate attacks
		half_lengths = tuple([int(el / 2) for el in player.shape])
		print(half_lengths)
		attack_indices = [
			slice(
				max(play_at[i] - half_lengths[i], 0), 
				min(play_at[i] + half_lengths[i] + 1, self.board_metric.extent[i])
			)
			for i in range(len(half_lengths))
		]

		player_indices = [
			slice(
				-min(play_at[i] - half_lengths[i], 0), 
				player.shape[i] - max(play_at[i] + half_lengths[i] + 1 - self.board_metric.extent[i], 0)
			)
			for i in range(len(half_lengths))
		]

		print(tuple(attack_indices))
		print(tuple(player_indices))
		print((self.board[..., 1 + self.turn]).shape)
		self.board[..., 1 + self.turn][tuple(attack_indices)] += player[tuple(player_indices)]

		self.recompute_lowest_playables()
		self.increment_turn()

		# return True



metric = BoardMetric(extent = [101, 101], ordering = Ordering.SQUARE_SPIRAL_2D)

board = Board(metric, [
	knight_coords(),
	knight_coords()
	# np.array([0, 0, 0, 0, 1]),
	# np.array([0, 0, 0, 0, 1])
])

while True:
	try:
		r = board.play()
	except IndexError as e:
		print(e)
		break

t = int(time.time() * 1000)
os.makedirs(f'outputs/{t}')

array = board.board[..., 0] + 1
img = Image.fromarray((255 * array / np.amax(array)).astype(np.uint8))
img.save(f'outputs/{t}/board.png')

plt.imshow(board.board[..., 0] + 1)
plt.show()
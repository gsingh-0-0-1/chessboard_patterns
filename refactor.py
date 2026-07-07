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
import colorsys
import json


class Ordering(Enum):
    SQUARE_SPIRAL_2D = 'SQUARE_SPIRAL_2D'
    LINEAR_1D = 'LINEAR_1D'

@dataclass
class BoardMetric:
	extent: list[int]
	ordering: Ordering


class Board:
	def __init__(self, config: dict): #board_metric: BoardMetric, players: list):
		self.config = config
		self.board_metric = BoardMetric(config['metric']['extent'], Ordering(config['metric']['ordering']))
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
		self.players_raw = self.config['players']

		self.players = []
		for player_raw in self.players_raw:
			if player_raw['type'] == 'knight':
				self.players.append(knight_coords(*player_raw['arguments']))

		self.nplayers = len(self.players)
		self.half_lengths = [tuple([int(el / 2) for el in player.shape]) for player in self.players]
		
		self.lowest_playables = np.zeros(shape = (self.nplayers,), dtype = np.uint32)

		self.colors = np.array(
			[
				[
					int(255 * el) for el in colorsys.hsv_to_rgb(i / self.nplayers, 1.0, 1.0)
				] 
				for i in range(self.nplayers)
			],
			dtype = np.uint8
		)
		

		# We want the size of the board in the (nplayers + 1)st dimension
		# to have enough space to store:
		# - one space to hold whether or not the board is played
		# - `nplayers` values as flags to indicate if space is attacked by a given player
		#
		# The second through penultimate values will hold potential
		# values of attacking players (default -1)
		# The final value will store the value of the playing piece,
		# if any (default -1)
		board_array_dimensions = tuple(self.board_metric.extent) + (1 + self.nplayers,)
		self.board = np.zeros(shape = board_array_dimensions)
		self.board[..., 0] = -1

		self.image = np.zeros(shape = (self.board_metric.extent[0], self.board_metric.extent[1], 3), dtype = np.uint8) + 255

		# self.coordinate_ordering = np.zeros(
		# 	shape = (math.prod(self.board_metric.extent), len(self.board_metric.extent)),
		# 	dtype = np.int64
		# )
		self.coordinate_ordering = []

		self.board_metric.half_extent = [int(el / 2) for el in self.board_metric.extent]

		if self.board_metric.ordering == Ordering.SQUARE_SPIRAL_2D:
			for i in range(math.prod(self.board_metric.extent)):
				# self.coordinate_ordering[i] = square_spiral_index_to_coords(i) + np.array(self.board_metric.half_extent)
				self.coordinate_ordering.append(tuple(square_spiral_index_to_coords(i) + np.array(self.board_metric.half_extent)))

		if self.board_metric.ordering == Ordering.LINEAR_1D:
			for i in range(self.board_metric.extent[0]):
				self.coordinate_ordering.append(i) #[i] = i

		self.turn = 0

	def increment_turn(self):
		self.turn = (self.turn + 1) % self.nplayers

	def recompute_lowest_playables(self):
		for i in range(len(self.players)):
			idx = self.lowest_playables[i]
			while True:
				coords = self.coordinate_ordering[idx]

				# check if the board is played here
				if self.board[coords][0] != -1:
					idx += 1
					continue

				# check if the board is not attacked by another player
				# i.e. if the sum of the attacks array is zero
				# OR if the only attackers are itself
				if np.sum(self.board[coords][1:]) == self.board[coords][1 + i]:
					self.lowest_playables[i] = idx
					break

				idx += 1


	def play(self):
		player = self.players[self.turn]

		play_at = self.coordinate_ordering[self.lowest_playables[self.turn]]

		# set board
		self.board[play_at][0] = self.turn
		self.image[play_at[0], play_at[1]] = self.colors[self.turn]

		# indicate attacks
		half_lengths = self.half_lengths[self.turn]

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

		# print(tuple(attack_indices))
		# print(tuple(player_indices))
		# print((self.board[..., 1 + self.turn]).shape)
		self.board[..., 1 + self.turn][tuple(attack_indices)] += player[tuple(player_indices)]

		self.recompute_lowest_playables()
		self.increment_turn()

		# return True

	def save(self):
		t = int(time.time() * 1000)
		os.makedirs(f'outputs/{t}')

		img = Image.fromarray(board.image)
		img.save(f'outputs/{t}/board.png')

		with open(f'outputs/{t}/config.json', "w") as f:
			json.dump(self.config, f)


config = {
	'metric' : {
		'extent' : [2001, 2001],
		'ordering' : 'SQUARE_SPIRAL_2D'
	},
	'players' : [
		{
			'type' : 'knight',
			'arguments' : []
		},
		{
			'type' : 'knight',
			'arguments' : []
		}
	]
}


board = Board(config)

while True:
	try:
		r = board.play()
	except IndexError as e:
		break

board.save()

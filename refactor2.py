from dataclasses import dataclass
import numpy as np
import math
from enum import Enum
import colorsys
import json
import time
import os
from PIL import Image

from coordinate_utils import (
    square_spiral_index_to_coords,
    knight_coords,
    plus_shape_coords,
    x_shape_coords
)


class Ordering(Enum):
    SQUARE_SPIRAL_2D = 'SQUARE_SPIRAL_2D'
    LINEAR_1D = 'LINEAR_1D'


@dataclass
class BoardMetric:
    extent: list[int]
    ordering: Ordering


class Board:
    def __init__(self, config):

        self.config = config
        self.board_metric = BoardMetric(
            config['metric']['extent'],
            Ordering(config['metric']['ordering'])
        )

        H, W = self.board_metric.extent
        self.H, self.W = H, W
        self.N = H * W

        # ----------------------------
        # Players
        # ----------------------------
        self.players_raw = config['players']
        self.players = []
        self.attack_masks = []

        for p in self.players_raw:
            arr = eval(f"{p['type']}_coords(*p['arguments'])")
            self.players.append(arr)
            self.attack_masks.append(arr.astype(np.int16))

            #if p['type'] == 'knight':
            #    arr = knight_coords(*p['arguments'])
            #    self.players.append(arr)
            #    self.attack_masks.append(arr.astype(np.int16))

        self.nplayers = len(self.players)

        # ----------------------------
        # State
        # ----------------------------
        self.occupied = np.zeros((H, W), dtype=bool)
        self.attack_sum = np.zeros((H, W), dtype=np.int16)
        self.self_attack = np.zeros((self.nplayers, H, W), dtype=np.int16)

        # ----------------------------
        # Coordinates
        # ----------------------------
        half = np.array(self.board_metric.extent) // 2

        self.coords = np.zeros((self.N, 2), dtype=np.int32)

        if self.board_metric.ordering == Ordering.SQUARE_SPIRAL_2D:
            for i in range(self.N):
                self.coords[i] = square_spiral_index_to_coords(i) + half
        else:
            for i in range(self.N):
                self.coords[i] = (i, 0)

        # ----------------------------
        # FAST POINTERS (NEW CORE FIX)
        # ----------------------------
        self.ptr = np.zeros(self.nplayers, dtype=np.int32)
        self.next_ptr = np.zeros(self.nplayers, dtype=np.int32)

        # ----------------------------
        # Render
        # ----------------------------
        self.image = np.full((H, W, 3), 255, dtype=np.uint8)

        self.colors = np.array([
            [int(255 * c) for c in colorsys.hsv_to_rgb(i / self.nplayers, 0.7, 0.7)]
            for i in range(self.nplayers)
        ], dtype=np.uint8)

        self.turn = 0

    # ----------------------------
    # O(1) validity
    # ----------------------------
    def is_valid(self, y, x, pid):
        return self.attack_sum[y, x] == self.self_attack[pid, y, x]

    # ----------------------------
    # FAST STENCIL UPDATE (correct)
    # ----------------------------
    def apply_attack(self, pid, y, x):

        mask = self.attack_masks[pid]
        h, w = mask.shape
        cy, cx = h // 2, w // 2

        y0 = max(0, y - cy)
        y1 = min(self.H, y - cy + h)
        x0 = max(0, x - cx)
        x1 = min(self.W, x - cx + w)

        my0 = max(0, cy - y)
        my1 = my0 + (y1 - y0)
        mx0 = max(0, cx - x)
        mx1 = mx0 + (x1 - x0)

        sub = mask[my0:my1, mx0:mx1]

        self.attack_sum[y0:y1, x0:x1] += sub
        self.self_attack[pid, y0:y1, x0:x1] += sub

    # ----------------------------
    # NO SCAN FINDER (FINAL FIX)
    # ----------------------------
    def find_next(self, pid):

        i = self.next_ptr[pid]

        while i < self.N:

            y, x = self.coords[i]

            if self.occupied[y, x]:
                i += 1
                continue

            if self.is_valid(y, x, pid):
                self.ptr[pid] = i
                self.next_ptr[pid] = i + 1
                return i

            i += 1

        raise IndexError("No valid moves")

    # ----------------------------
    # Step
    # ----------------------------
    def play(self):

        pid = self.turn

        idx = self.find_next(pid)
        y, x = self.coords[idx]

        self.occupied[y, x] = True
        self.image[y, x] = self.colors[pid]

        self.apply_attack(pid, y, x)

        self.turn = (self.turn + 1) % self.nplayers

    # ----------------------------
    # Save
    # ----------------------------
    def save(self):
        t = int(time.time() * 1000)
        os.makedirs(f'outputs/{t}', exist_ok=True)

        Image.fromarray(self.image).save(f'outputs/{t}/board.png')

        with open(f'outputs/{t}/config.json', "w") as f:
            json.dump(self.config, f)


# ----------------------------
# CONFIG
# ----------------------------

config = {
    'metric': {
        'extent': [20001, 20001],
        'ordering': 'SQUARE_SPIRAL_2D'
    },
    "players": [
    	{"type": "x_shape", "arguments": [[1]]},
    	{"type": "plus_shape", "arguments": [[2]]},
    	{"type": "x_shape", "arguments": [[4]]},
    ]
}


board = Board(config)

while True:
    try:
        board.play()
    except IndexError:
        break

board.save()
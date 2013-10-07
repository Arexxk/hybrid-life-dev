#!/usr/bin/env python

# Example of how to determine neighboring grids
# (or tiles) in a periodic domain

# Call like: $ ./get_neighbors.py <nx tiles> <ny tiles> <rank>
# Where <nx tiles> is the number of tiles along the x-axis,
# <ny tiles> is the number along the y-axis, and <rank>
# is the rank of a task owning a tile.

import sys
import numpy
nx = int(sys.argv[1])
ny = int(sys.argv[2])
n_tiles = nx*ny
rank = int(sys.argv[3])

# establish 2D array of ranks
tile_ranks = numpy.arange(0, n_tiles).reshape((ny, nx))

# determine the x and y indexes of rank
x_index = rank % nx
y_index = rank / nx

print x_index
print y_index
print tile_ranks
print tile_ranks[y_index, x_index]

# neighbors is a simple dictionary holding the rank
# of the neighboring tile in the following directions:
# 't' : top
# 'b' : bottom
# 'l' : left
# 'r' : right
# 'tl' : top left
# 'tr' : top right
# 'bl' : bottom left
# 'br' : bottom right

neighbors = {}
neighbors['t'] = tile_ranks[(y_index + 1) % ny, x_index]
neighbors['b'] = tile_ranks[(y_index - 1) % ny, x_index]
neighbors['l'] = tile_ranks[y_index, (x_index - 1) % nx]
neighbors['r'] = tile_ranks[y_index, (x_index + 1) % nx]
neighbors['tl'] = tile_ranks[(y_index + 1) % ny, (x_index - 1) % nx]
neighbors['tr'] = tile_ranks[(y_index + 1) % ny, (x_index + 1) % nx]
neighbors['bl'] = tile_ranks[(y_index - 1) % ny, (x_index - 1) % nx]
neighbors['br'] = tile_ranks[(y_index - 1) % ny, (x_index + 1) % nx]

print neighbors

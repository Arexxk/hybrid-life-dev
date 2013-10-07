#! /usr/bin/python
""" GPU doing conways game of life. ESC to quit
this shows how it is possible to recycle images from the renderbuffer
and use the very fast processing speed of the GPU to do certain tasks.
"""
#import SDSC_functions
import sys
import ctypes
import demo
import pi3d
import Image
import numpy
import numpy.ctypeslib
import time
import math
from pi3d.constants import *
from mpi4py import MPI

comm = MPI.COMM_WORLD # opens up the MPI world. Looks at the network
nprocs = comm.Get_size() # the number of cores. Don't worry, it's single core.
rank = comm.Get_rank() # the number of nodes. You only care about this for boundaries. 
#print "nprocs is: " + str(nprocs)
#print "rank is: " + str(rank)

# converts the PIL to image buffer for shader
def numpy_pil_to_buf(arr, w, h):
	img = (ctypes.c_char * (w * h * 3))()
	idx = 0
	for row in arr:
		for RGB_object in row:
			for RGB_val in RGB_object:
				img[idx] = ctypes.c_char( chr(RGB_val) )
				idx += 1
	return img


WIDTH = int(sys.argv[1])/nprocs
HEIGHT = int(sys.argv[1])/nprocs
EVOLUTIONS = int(sys.argv[2]) 
DISPLAY = pi3d.Display.create(w=WIDTH, h=HEIGHT)
CAMERA = pi3d.Camera(is_3d=False)
shader = pi3d.Shader("shaders/conway")

#open("/export/home/akissing/strongtime_hybrid/strongtime"+str(nprocs)+"on"+
#str(WIDTH*nprocs)+"x"+str(HEIGHT*nprocs)+".txt", "w").write("")

nx = WIDTH 
ny = HEIGHT
n_tiles = nx*ny 


# establish 2D array of ranks
tile_ranks = numpy.arange(0, n_tiles).reshape((ny, nx))

# determine the x and y indexes of rank
x_index = rank % nx
y_index = rank / nx

#print x_index
#print y_index
#print tile_ranks
#print tile_ranks[y_index, x_index]

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

nb = neighbors

tex = []
tex.append(pi3d.Texture("textures/Roof.png", mipmap=False))
tex.append(pi3d.Texture("textures/Roof.png", mipmap=False))
sprite = pi3d.Sprite(camera=CAMERA, w=WIDTH, h=HEIGHT, x=0.0, y=0.0, z=1.0)
sprite.set_draw_details(shader, [tex[0]])# how to call the conway.vs basically
sprite.set_2d_size(WIDTH, HEIGHT, 0.0, 0.0) # used to get pixel scale by shader

ti = 0 # variable to toggle between two textures
img = (ctypes.c_char * (WIDTH * HEIGHT * 3))() # to hold pixels, make 1x1 larger maybe?
evolutions = 0
timetotal0 = time.clock()
while DISPLAY.loop_running() and evolutions < EVOLUTIONS:
	# Draw the buffer
	sprite.draw()

	# Calc index to swap textures
	ti = (ti+1) % 2 

	# img <- read in image from OpenGL buffer
	pi3d.opengles.glReadPixels(0, 0, WIDTH, HEIGHT, GL_RGB, GL_UNSIGNED_BYTE, 
			ctypes.byref(img))# can you do a python slice? Will make border calculation easy

	# Turn buffer img array ctype into a PIL 
	timeim0 = time.clock()
	# look this up
	im = Image.frombuffer('RGB', (WIDTH, HEIGHT), img, 'raw', 'RGB', 0, 1)
	timeim1 = time.clock()

	#Turn PIL into a numpy matrix
	timearr0 = time.clock()
	arr = numpy.array(im)
	timearr1 = time.clock()
	
	# Assign and Send it's edges
	my_top = arr[0]
	my_bot = arr[len(arr[0][0])]
	my_lef = arr[:,0]
	my_rig = arr[:,len(arr[0])-1]
	
	timesend0 = time.clock()

	if nprocs > 8:
		top_rank = nb['t']
		bot_rank = nb['b']
		lef_rank = nb['l']
		rig_rank = nb['r']
		comm.send(my_top, dest=top_rank, tag=rank+top_rank)
		comm.send(my_bot, dest=bot_rank, tag=rank+bot_rank)
		comm.send(my_lef, dest=lef_rank, tag=rank+lef_rank)
		comm.send(my_rig, dest=rig_rank, tag=rank+rig_rank)
	elif nprocs == 1:
		top_rank = 0
		bot_rank = 0
		lef_rank = 0
		rig_rank = 0
		comm.send(my_top, dest=top_rank, tag=0)
		comm.send(my_bot, dest=bot_rank, tag=1)
		comm.send(my_lef, dest=lef_rank, tag=2)
		comm.send(my_rig, dest=rig_rank, tag=3)

	# Assign and Send it's corners
	my_tlf = arr[0][0]
	my_trt = arr[0][len(my_top)-1]
	my_blf = arr[len(my_lef)-1][0]
	my_brt = arr[len(my_lef)-1][len(my_top)-1]
	
	if nprocs > 8:
		tlf_rank = nb['tl']
		trt_rank = nb['tr']
		blf_rank = nb['bl']
		brt_rank = nb['br']
		comm.send(my_tlf, dest=tlf_rank, tag=rank+tlf_rank)
		comm.send(my_trt, dest=trt_rank, tag=rank+trt_rank)
		comm.send(my_blf, dest=blf_rank, tag=rank+blf_rank)
		comm.send(my_brt, dest=brt_rank, tag=rank+brt_rank)
	elif nprocs == 1:
		tlf_rank = 0
		trt_rank= 0
		blf_rank = 0
		brt_rank = 0
		comm.send(my_tlf, dest=top_rank, tag=4)
		comm.send(my_trt, dest=bot_rank, tag=5)
		comm.send(my_blf, dest=lef_rank, tag=6)
		comm.send(my_brt, dest=rig_rank, tag=7)

	timesend1 = time.clock()
	# Receive edges and apply them to matrix
	timerecv0 = time.clock()
	
	if nprocs > 8:
		arr[0] = comm.recv(source=top_rank, tag=rank*top_rank)
		arr[len(arr[0][0])]= comm.recv(source=bot_rank, tag=rank*bot_rank)
		arr[:,0] = comm.recv(source=lef_rank, tag=rank*lef_rank)
		arr[:,len(arr[0])-1] = comm.recv(source=rig_rank, tag=rank*rig_rank)
	elif nprocs == 1:
		arr[0] = comm.recv(source=top_rank, tag=0)
		arr[len(arr[0][0])]= comm.recv(source=bot_rank, tag=1)
		arr[:,0] = comm.recv(source=lef_rank, tag=2)
		arr[:,len(arr[0])-1] = comm.recv(source=rig_rank, tag=3)

	# Receive corners and apply them to matrix
	if nprocs > 8:
		arr[0][0] = comm.recv(source=tlf_rank, tag=rank*tlf_rank)
		arr[0][len(my_top)-1] = comm.recv(source=trt_rank, tag=rank*trt_rank)
		arr[len(my_lef)-1][0] = comm.recv(source=blf_rank, tag=rank*blf_rank)
		arr[len(my_lef)-1][len(my_top)-1] = comm.recv(source=brt_rank, tag=rank*brt_rank)
	elif nprocs == 1:
		arr[0][0] = comm.recv(source=tlf_rank, tag=4)
		arr[0][len(my_top)-1] = comm.recv(source=trt_rank, tag=5)
		arr[len(my_lef)-1][0] = comm.recv(source=blf_rank, tag=6)
		arr[len(my_lef)-1][len(my_top)-1] = comm.recv(source=brt_rank, tag=7)
	
	timerecv1 = time.clock()
	
	# Matrix to ctype char array for buf, then back to GPU
	timerecon0 = time.clock()
	img = numpy_pil_to_buf(arr, WIDTH, HEIGHT)
	timerecon1 = time.clock()

	#print "buf to PIL: "+str(timeim1-timeim0)+" PIL to Numpy: "+str(timearr1-timearr0)+\
	# " MPI send:"+str(timesend1-timesend0)+" MPI recv: "+str(timerecv1-timerecv0)+\
	# " Reconstruct: "+str(timerecon1-timerecon0)

	# Tell OpenGL to use the swapped texture
	pi3d.opengles.glBindTexture(GL_TEXTURE_2D, tex[ti]._tex)

	# Give OpenGL the picture params and the last image (img) 	
	pi3d.opengles.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, WIDTH, HEIGHT, 0, GL_RGB,
			GL_UNSIGNED_BYTE, img)

	# Apply the shader to the swapped texture
	sprite.set_draw_details(shader, [tex[ti]])
	evolutions += 1

timetotal1 = time.clock()
print "Time for "+str(EVOLUTIONS)+" number of evolutions was: "+str(timetotal1-timetotal0)
#open("/export/home/akissing/strongtime_hybrid/strongtime"+str(nprocs)+"on"+str(WIDTH*nprocs)+"x"+
#str(HEIGHT*nprocs)+".txt", "a")\
#.write(str(rank)+'\t'+str(timetotal1-timetotal0)+'\n')

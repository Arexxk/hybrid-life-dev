""" GPU doing conways game of life. ESC to quit
this shows how it is possible to recycle images from the renderbuffer
and use the very fast processing speed of the GPU to do certain tasks.
"""
import sys
import ctypes
import demo
import pi3d
import time
from pi3d.constants import *

print sys.argv[1]
print sys.argv[2]

WIDTH = int(sys.argv[1]) 
HEIGHT = int(sys.argv[1]) 
DISPLAY = pi3d.Display.create(w=WIDTH, h=HEIGHT)
CAMERA = pi3d.Camera(is_3d=False)
shader = pi3d.Shader("shaders/conway")

tex = []
tex.append(pi3d.Texture("textures/Roof.png", mipmap=False))
tex.append(pi3d.Texture("textures/Roof.png", mipmap=False))
sprite = pi3d.Sprite(camera=CAMERA, w=WIDTH, h=HEIGHT, x=0.0, y=0.0, z=1.0)
sprite.set_draw_details(shader, [tex[0]])
sprite.set_2d_size(WIDTH, HEIGHT, 0.0, 0.0) # used to get pixel scale by shader

ti = 0 # variable to toggle between two textures
img = (ctypes.c_char * (WIDTH * HEIGHT * 3))() # to hold pixels

#open("time_serialGPU/time_serial"+"on"+str(WIDTH)+"x"+str(HEIGHT)+".txt", "w").write("")
timetotal0 = time.clock()
evolutions = 0
#while DISPLAY.loop_running() and evolutions < int(argv[2]):
while DISPLAY.loop_running():
  sprite.draw()
  
  ti = (ti+1) % 2
  pi3d.opengles.glReadPixels(0, 0, WIDTH, HEIGHT, GL_RGB, GL_UNSIGNED_BYTE,
                        ctypes.byref(img))
  pi3d.opengles.glBindTexture(GL_TEXTURE_2D, tex[ti]._tex)
  opengles.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, WIDTH, HEIGHT, 0, GL_RGB,
                        GL_UNSIGNED_BYTE, img)
  sprite.set_draw_details(shader, [tex[ti]])
  evolutions += 1

timetotal1 = time.clock()
#open("time_serialGPU/time_serial"+"on"+str(WIDTH)+"x"+str(HEIGHT)+".txt", "a")\
#.write('serial\t'+str(timetotal1-timetotal0)+'\n')

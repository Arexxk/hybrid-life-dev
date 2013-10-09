""" GPU doing conways game of life. ESC to quit
this shows how it is possible to recycle images from the renderbuffer
and use the very fast processing speed of the GPU to do certain tasks.
"""
import sys, traceback
import ctypes
import demo
import pi3d
import time
import Image
import socket, struct, threading # for networking
import numpy
import cPickle
from pi3d.constants import *

def numpy_pil_to_buf(arr, w, h):
  img = (ctypes.c_char * (w * h * 3))()
  idx = 0
  for row in arr:
    for RGB_object in row:
      for RGB_val in RGB_object:
        img[idx] = ctypes.c_char( chr(RGB_val) )
        idx += 1
  # [row for row in arr for RGB_object in row for RGB_val in RGB_object ]
  return img

def receive_data(recv_sock):
  # Parameter : recv_sock - the socket where we want to receive data
  # return : the entire pickled string
  # TODO: rather than use a delimiter, it is better to specify how many bytes
  # will be sent by the socket
  rdbuf = ''
  while True:
    rdbuf += recv_sock.recv(150000)
    # print 'rdbuff is ' + rdbuf
    split = rdbuf.split(SOCKET_DEL) # split at newline, as per our custom protocol
    if len(split) != 2: # it should be 2 elements big if it got the whole message
      pass
    else:
      return split[0] # it will be the first element, the newline will be 
                      # removed so it should pickle correctly
def logtimes(time0, time1, the_dict):
  the_dict['time'] += time1 - time0
  the_dict['ev'] += 1

# logging files and varibles
LOGFILE = open('demos/logfile.txt', 'w')
glpixel = {'time' : 0, 'ev' : 0, 'name': 'GLREADPIXELS'} # tuple to make sure we divide by the true evolutions
num_mat_time = {'time' : 0, 'ev' : 0, 'name': 'Making numpy matrix'}
picklepack = {'time' : 0, 'ev' : 0, 'name': 'Packing data as pickle'}
recvdata = {'time' : 0, 'ev' : 0, 'name': 'Receving the data through the socket'}
unpickle = {'time' : 0, 'ev' : 0, 'name': 'Unpacking data as pickle'}
numpy_pil_buf_time = {'time' : 0, 'ev' : 0, 'name': 'Numpy to pil to buffer loop'}

logvars = (glpixel, num_mat_time, picklepack, recvdata, unpickle, numpy_pil_buf_time)

MY_IP = str(sys.argv[1])
THERE_IP = str(sys.argv[2])
RECV_PORT = 20000
SEND_PORT = 20001
SOCKET_DEL = '$*etisawesome*$'
WIDTH = 100
HEIGHT = 100
DISPLAY = pi3d.Display.create(w=WIDTH, h=HEIGHT)
CAMERA = pi3d.Camera(is_3d=False)
shader = pi3d.Shader("shaders/conway") # How the game is calculated.

# # logging files and varibles
# LOGFILE = open('logfile.txt', 'w')
# GLREADPIXELS = {'time' : 0, 'ev' : 0, 'name': 'GLREADPIXELS'} # tuple to make sure we divide by the true evolutions
# logvars = [GLREADPIXELS]


# some logic to see where it is, will have to be read from somewhere I think
if MY_IP == '10.10.0.1':
  position = 'l'
else:
  position = 'r'


# initialize sockets and bind them
host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_sock.bind((MY_IP, RECV_PORT))
send_sock.bind((MY_IP, SEND_PORT))

# listen to connections coming in
host_sock.listen(5)

# try for 10 seconds to connect to the other socket, need to try because may not have 
# reached the listen yet
t = 0
while t < 100:
  try:
    send_sock.connect((THERE_IP, RECV_PORT))
  except:
    t = t + 1
    time.sleep(.1)
    pass

# accept the connection that should be queued from above
recv_sock, addr = host_sock.accept()
print addr

try:

  tex = []
  tex.append(pi3d.Texture("images/hqdefault.jpg", mipmap=False))
  tex.append(pi3d.Texture("images/hqdefault.jpg", mipmap=False))

  sprite = pi3d.Sprite(camera=CAMERA, w=WIDTH, h=HEIGHT, x=0.0, y=0.0, z=1.0)
  sprite.set_draw_details(shader, [tex[0]])
  sprite.set_2d_size(WIDTH, HEIGHT, 0.0, 0.0) # used to get pixel scale by shader

  ti = 0 # variable to toggle between two textures
  img = (ctypes.c_char * (WIDTH * HEIGHT * 3))() # to hold pixels

  # open("time_serialGPU/time_serial"+"on"+str(WIDTH)+"x"+str(HEIGHT)+".txt", "w").write("")
  timetotal0 = time.clock()
  evolutions = 0

  # one last handshake to make sure the nodes are in sync
  send_sock.send('let''s do this')
  print recv_sock.recv(1024)
  buf = ''

  #while DISPLAY.loop_running() and evolutions < int(argv[2]):
  while DISPLAY.loop_running():
    sprite.draw()
    # send_sock.send('we are at the start of the loop')
    # print recv_sock.recv(1024)
    
    ti = (ti+1) % 2
    # read image from buffer
    timetotal0 = time.clock()
    pi3d.opengles.glReadPixels(0, 0, WIDTH, HEIGHT, GL_RGB, GL_UNSIGNED_BYTE,
                          ctypes.byref(img))
    logtimes(timetotal0, time.clock(), glpixel) 

    im_from_buf = Image.frombuffer('RGB', (WIDTH, HEIGHT), img, 'raw', 'RGB', 0, 1)

    # turn to numpy matrix for easy manipulation?
    timetotal0 = time.clock()
    num_mat = numpy.array(im_from_buf)
    logtimes(timetotal0, time.clock(), num_mat_time)

    # Assign it's edges remember the outer edges are the other edges, the nodes real
    # edges are actually one pixel in
    my_top = num_mat[1]
    my_bot = num_mat[len(num_mat[1][1])]
    my_lef = num_mat[:,1]
    my_rig = num_mat[:,len(num_mat[0])-2]

    if position == 'l':
      timetotal0 = time.clock()
      my_rig = cPickle.dumps(my_rig, cPickle.HIGHEST_PROTOCOL) + SOCKET_DEL
      logtimes(timetotal0, time.clock(), picklepack)

      send_sock.sendall(my_rig)

      timetotal0 = time.clock()
      x = receive_data(recv_sock)
      logtimes(timetotal0, time.clock(), recvdata)

      timetotal0 = time.clock()
      num_mat[:,1] = cPickle.loads(x)
      logtimes(timetotal0, time.clock(), unpickle)
      # print num_mat[:,1]

    else:
      timetotal0 = time.clock()
      my_lef = cPickle.dumps(my_lef, cPickle.HIGHEST_PROTOCOL) + SOCKET_DEL
      logtimes(timetotal0, time.clock(), picklepack)

      send_sock.sendall(my_lef)

      timetotal0 = time.clock()
      x = receive_data(recv_sock)
      logtimes(timetotal0, time.clock(), recvdata)

      timetotal0 = time.clock()
      num_mat[:,len(num_mat[0])-1] = cPickle.loads(x)
      logtimes(timetotal0, time.clock(), unpickle)

    timetotal0 = time.clock()
    img = numpy_pil_to_buf(num_mat, WIDTH, HEIGHT)
    logtimes(timetotal0, time.clock(), numpy_pil_buf_time)


    pi3d.opengles.glBindTexture(GL_TEXTURE_2D, tex[ti]._tex)
    opengles.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, WIDTH, HEIGHT, 0, GL_RGB,
                          GL_UNSIGNED_BYTE, img)
    sprite.set_draw_details(shader, [tex[ti]])
    evolutions += 1
    send_sock.send('sync') # sync the nodes
    recv_sock.recv(30)
    # time.sleep(1)
except cPickle.UnpicklingError as u:
  print 'pickle error'
  traceback.print_exc(file=sys.stdout)
  print 'x(the pickled module to be loaded is '
  print x
  print '\n end of pickle '
  send_sock.close()
  recv_sock.close()
except:
  traceback.print_exc(file=sys.stdout)
  print 'exception happened, printing traceback, writing to the log and closing network connections'
  for var in logvars:
    var['time'] = var['time']/var['ev']
    LOGFILE.write(var['name'] + ' = ' + str(var['time']) + '\n') 
  LOGFILE.close()
  send_sock.close()
  recv_sock.close()
  print 'exiting'
timetotal1 = time.clock()
#open("time_serialGPU/time_serial"+"on"+str(WIDTH)+"x"+str(HEIGHT)+".txt", "a")\
#.write('serial\t'+str(timetotal1-timetotal0)+'\n')

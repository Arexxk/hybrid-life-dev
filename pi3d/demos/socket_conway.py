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
  return img

# rdbuf = ''
# while True:
#     rdbuf += sock.recv(4096)
#     lines = rdbuf.split('\n')
#     rdbuf = lines[-1]
#     for line in lines[:-1]:
#         dostuff(line)  
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
    # print 'split is ' 
    # print split
    # print len(split)
    # time.sleep(1)
    if len(split) != 2: # it should be 2 elements big if it got the whole message
      pass
    else:
      return split[0] # it will be the first element, the newline will be 
                      # removed so it should pickle correctly


MY_IP = str(sys.argv[1])
THERE_IP = str(sys.argv[2])
RECV_PORT = 20000
SEND_PORT = 20001
SOCKET_DEL = '$*etisawesome*$'
WIDTH = 1000
HEIGHT = 1000
DISPLAY = pi3d.Display.create(w=WIDTH, h=HEIGHT)
CAMERA = pi3d.Camera(is_3d=False)
shader = pi3d.Shader("shaders/conway") # How the game is calculated.

# print sys.argv[1]

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

try:

  tex = []
  tex.append(pi3d.Texture("images/hqdefault.jpg", mipmap=False))
  tex.append(pi3d.Texture("images/hqdefault.jpg", mipmap=False))

  sprite = pi3d.Sprite(camera=CAMERA, w=WIDTH, h=HEIGHT, x=0.0, y=0.0, z=1.0)
  sprite.set_draw_details(shader, [tex[0]])
  sprite.set_2d_size(WIDTH, HEIGHT, 0.0, 0.0) # used to get pixel scale by shader

  ti = 0 # variable to toggle between two textures
  img = (ctypes.c_char * (WIDTH * HEIGHT * 3))() # to hold pixels

  #open("time_serialGPU/time_serial"+"on"+str(WIDTH)+"x"+str(HEIGHT)+".txt", "w").write("")
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
    pi3d.opengles.glReadPixels(0, 0, WIDTH, HEIGHT, GL_RGB, GL_UNSIGNED_BYTE,
                          ctypes.byref(img))

    im_from_buf = Image.frombuffer('RGB', (WIDTH, HEIGHT), img, 'raw', 'RGB', 0, 1)

    # turn to numpy matrix for easy manipulation?
    num_mat = numpy.array(im_from_buf)
    # Assign it's edges remember the outer edges are the other edges, the nodes real
    # edges are actually one pixel in
    my_top = num_mat[1]
    my_bot = num_mat[len(num_mat[1][1])]
    my_lef = num_mat[:,1]
    my_rig = num_mat[:,len(num_mat[0])-2]

    if position == 'l':
      # output = open('data.pkl', 'wb')
      # my_rig = reveive_data(recv_sock) # receive the right data
      my_rig = cPickle.dumps(my_rig, cPickle.HIGHEST_PROTOCOL) + SOCKET_DEL
      send_sock.sendall(my_rig)
      x = receive_data(recv_sock)
      num_mat[:,1] = cPickle.loads(x)
      # print num_mat[:,1]
      # num_mat[:,0] = recv_sock.recv(1024)
    else:
      my_lef = cPickle.dumps(my_lef, cPickle.HIGHEST_PROTOCOL) + SOCKET_DEL
      send_sock.sendall(my_lef)
      x = receive_data(recv_sock)
      num_mat[:,len(num_mat[0])-1] = cPickle.loads(x)
      # print num_mat[:,len(num_mat[0])-1]
      # num_mat[:,len(num_mat[0])-1] = recv_sock.recv(1024)

    # img = numpy_pil_to_buf(num_mat, WIDTH, HEIGHT)


    pi3d.opengles.glBindTexture(GL_TEXTURE_2D, tex[ti]._tex)
    opengles.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, WIDTH, HEIGHT, 0, GL_RGB,
                          GL_UNSIGNED_BYTE, img)
    sprite.set_draw_details(shader, [tex[ti]])
    evolutions += 1
    send_sock.send('sync') # sync the nodes
    recv_sock.recv(30)
    # time.sleep(1)
except UnpicklingError as u:
  print 'pickle error'
  traceback.print_exc(file=sys.stdout)
  print 'x(the pickled module to be loaded is '
  print x
  print '\n end of pickle '
  send_sock.close()
  recv_sock.close()
except:
  print 'exception happened, printing traceback and closing network connections'
  traceback.print_exc(file=sys.stdout)
  send_sock.close()
  recv_sock.close()
  print 'exiting'
timetotal1 = time.clock()
#open("time_serialGPU/time_serial"+"on"+str(WIDTH)+"x"+str(HEIGHT)+".txt", "a")\
#.write('serial\t'+str(timetotal1-timetotal0)+'\n')

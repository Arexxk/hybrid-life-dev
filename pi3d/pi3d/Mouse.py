import threading

from echomesh.util import Log

LOGGER = Log.logger(__name__)

class _Mouse(threading.Thread):
  """holds Mouse object, see also (the preferred) events methods"""
  BUTTON_1 = 1 << 1
  BUTTON_2 = 1 << 2
  BUTTONS = BUTTON_1 & BUTTON_2
  HEADER = 1 << 3
  XSIGN = 1 << 4
  YSIGN = 1 << 5
  INSTANCE = None

  def __init__(self, mouse='mice', restrict=True, width=1920, height=1200):
    """
    Arguments:
      *mouse*
        /dev/input/ device name
      *restrict*
        stops or allows the mouse x and y values to carry on going beyond:
      *width*
        mouse x limit
      *height*
        mouse y limit
    """
    super(_Mouse, self).__init__()
    self.fd = open('/dev/input/' + mouse, 'r')
    self.running = False
    self.buffer = ''
    self.lock = threading.RLock()
    self.width = width
    self.height = height
    self.restrict = restrict

    self.reset()

  def reset(self):
    with self.lock:
      self._x = self._y = self._dx = self._dy = 0
    self.button = False

  def start(self):
    if not self.running:
      self.running = True
      super(_Mouse, self).start()

  def run(self):
    while self.running:
      self._check_event()
    self.fd.close()

  def position(self):
    with self.lock:
      return self._x, self._y

  def velocity(self):
    with self.lock:
      return self._dx, self._dy

  def _check_event(self):
    if len(self.buffer) >= 3:
      buttons = ord(self.buffer[0])
      self.buffer = self.buffer[1:]
      if buttons & _Mouse.HEADER:
        dx, dy = map(ord, self.buffer[0:2])
        self.buffer = self.buffer[2:]
        self.button = buttons & _Mouse.BUTTONS
        if buttons & _Mouse.XSIGN:
          dx -= 256
        if buttons & _Mouse.YSIGN:
          dy -= 256

        x = self._x + dx
        y = self._y + dy
        if self.restrict:
          x = min(max(x, 0), self.width - 1)
          y = min(max(y, 0), self.height - 1)

        with self.lock:
          self._x, self._y, self._dx, self._dy = x, y, dx, dy

    else:
      try:
        self.buffer += self.fd.read(3)
      except:
        self.stop()
        return

  def stop(self):
    self.running = False

def Mouse(*args, **kwds):
  if not _Mouse.INSTANCE:
    _Mouse.INSTANCE = _Mouse(*args, **kwds)
  return _Mouse.INSTANCE

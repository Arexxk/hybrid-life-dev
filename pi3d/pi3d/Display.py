from ctypes import c_float

import time
import threading
import traceback

from echomesh.util import Log

from pi3d.constants import *
from pi3d.util import Utility
from pi3d.util.DisplayOpenGL import DisplayOpenGL

LOGGER = Log.logger(__name__)

ALLOW_MULTIPLE_DISPLAYS = False
RAISE_EXCEPTIONS = True
MARK_CAMERA_CLEAN_ON_EACH_LOOP = True

DEFAULT_FOV = 45.0
DEFAULT_DEPTH = 24
DEFAULT_NEAR = 1.0
DEFAULT_FAR = 1000.0
WIDTH = 0
HEIGHT = 0

class Display(object):
  """This is the central control object of the pi3d system and an instance
  must be created before some of the other class methods are called.
  """
  INSTANCE = None
  """The current unique instance of Display."""

  def __init__(self, tkwin=None):
    """
    Constructs a raw Display.  Use pi3d.Display.create to create an initialized
    Display.

    *tkwin*
      An optional Tk window.

    """
    if Display.INSTANCE:
      assert ALLOW_MULTIPLE_DISPLAYS
      LOGGER.warning('A second instance of Display was created')
    else:
      Display.INSTANCE = self

    self.tkwin = tkwin

    self.sprites = []
    self.sprites_to_load = set()
    self.sprites_to_unload = set()

    self.opengl = DisplayOpenGL()
    self.max_width, self.max_height = self.opengl.width, self.opengl.height
    self.first_time = True
    self.is_running = True
    self.lock = threading.RLock()

    LOGGER.debug(STARTUP_MESSAGE)

  def loop_running(self):
    """*loop_running* is the main event loop for the Display.

    Most pi3d code will look something like this::

      DISPLAY = Display.create()

      # Initialize objects and variables here.
      # ...

      while DISPLAY.loop_running():
        # Update the frame, using DISPLAY.time for the current time.
        # ...

        # Check for quit, then call DISPLAY.stop.
        if some_quit_condition():
          DISPLAY.stop()

    ``Display.loop_running()`` **must** be called on the main Python thread,
    or else white screens and program crashes are likely.

    The Display loop can run in two different modes - *free* or *framed*.

    If ``DISPLAY.frames_per_second`` is empty or 0 then the loop runs *free* - when
    it finishes one frame, it immediately starts working on the next frame.

    If ``Display.frames_per_second`` is a positive number then the Display is
    *framed* - when the Display finishes one frame before the next frame_time,
    it waits till the next frame starts.

    A free Display gives the highest frame rate, but it will also consume more
    CPU, to the detriment of other threads or other programs.  There is also
    the significant drawback that the framerate will fluctuate as the numbers of
    CPU cycles consumed per loop, resulting in jerky motion and animations.

    A framed Display has a consistent if smaller number of frames, and also
    allows for potentially much smoother motion and animation.  The ability to
    throttle down the number of frames to conserve CPU cycles is essential
    for programs with other important threads like audio.

    ``Display.frames_per_second`` can be set at construction in
    ``Display.create`` or changed on-the-fly during the execution of the
    program.  If ``Display.frames_per_second`` is set too high, the Display
    doesn't attempt to "catch up" but simply runs freely.

    """
    if self.is_running:
      if self.first_time:
        self.time = time.time()
        self.first_time = False
      else:
        self._loop_end()  # Finish the previous loop.
      self._loop_begin()
    else:
      self._loop_end()
      self.destroy()

    return self.is_running

  def resize(self, x=0, y=0, w=0, h=0):
    """Reshape the window with the given coordinates."""
    if w <= 0:
      w = display.max_width
    if h <= 0:
      h = display.max_height
    self.width = w
    self.height = h

    self.left = x
    self.top = y
    self.right = x + w
    self.bottom = y + h
    self.opengl.resize(x, y, w, h)

  def add_sprites(self, *sprites):
    """Add one or more sprites to this Display."""
    with self.lock:
      self.sprites_to_load.update(sprites)

  def remove_sprites(self, *sprites):
    """Remove one or more sprites from this Display."""
    with self.lock:
      self.sprites_to_unload.update(sprites)

  def stop(self):
    """Stop the Display."""
    self.is_running = False

  def destroy(self):
    """Destroy the current Display and reset Display.INSTANCE."""
    self.stop()
    try:
      self.opengl.destroy()
    except:
      pass
    try:
      self.mouse.stop()
    except:
      pass
    try:
      self.tkwin.destroy()
    except:
      pass
    Display.INSTANCE = None

  def clear(self):
    """Clear the Display."""
    # opengles.glBindFramebuffer(GL_FRAMEBUFFER,0)
    opengles.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

  def set_background(self, r, g, b, alpha):
    """Set the Display background. **NB the actual drawing of the background
    happens during the rendering of the framebuffer by the shader so if no
    draw() is done by anything during each Display loop the screen will
    remain black** If you want to see just the background you will have to
    draw() something out of view (i.e. behind) the Camera.

    *r, g, b*
      Color values for the display
    *alpha*
      Opacity of the color.  An alpha of 0 means a transparent background,
      an alpha of 1 means full opaque.
    """
    opengles.glClearColor(c_float(r), c_float(g), c_float(b), c_float(alpha))
    opengles.glColorMask(1, 1, 1, int(alpha < 1.0))
    # Switches off alpha blending with desktop (is there a bug in the driver?)

  def mouse_position(self):
    """The current mouse position as a tuple."""
    # TODO: add: Now deprecated in favor of pi3d.events
    if self.mouse:
      return self.mouse.position()
    elif self.tkwin:
      return self.tkwin.winfo_pointerxy()
    else:
      return -1, -1

  def _loop_begin(self):
    # TODO(rec):  check if the window was resized and resize it, removing
    # code from MegaStation to here.
    self.clear()
    with self.lock:
      self.sprites_to_load, to_load = set(), self.sprites_to_load
      self.sprites.extend(to_load)
    self._for_each_sprite(lambda s: s.load_opengl(), to_load)

    if MARK_CAMERA_CLEAN_ON_EACH_LOOP:
      from pi3d.Camera import Camera
      camera = Camera.instance()
      if camera:
        camera.was_moved = False

  def _loop_end(self):
    with self.lock:
      self.sprites_to_unload, to_unload = set(), self.sprites_to_unload
      if to_unload:
        self.sprites = [s for s in self.sprites if s not in to_unload]

    t = time.time()
    self._for_each_sprite(lambda s: s.repaint(t))

    self.swap_buffers()

    for sprite in to_unload:
      sprite.unload_opengl()

    if getattr(self, 'frames_per_second', 0):
      self.time += 1.0 / self.frames_per_second
      delta = self.time - time.time()
      if delta > 0:
        time.sleep(delta)

  def _for_each_sprite(self, function, sprites=None):
    if sprites is None:
      sprites = self.sprites
    for s in sprites:
      try:
        function(s)
      except:
        LOGGER.error(traceback.format_exc())
        if RAISE_EXCEPTIONS:
          raise

  def __del__(self):
    self.destroy()

  def swap_buffers(self):
    self.opengl.swap_buffers()


def create(x=None, y=None, w=None, h=None, near=None, far=None,
           fov=DEFAULT_FOV, depth=DEFAULT_DEPTH, background=None,
           tk=False, window_title='', window_parent=None, mouse=False,
           frames_per_second=None):
  """
  Creates a pi3d Display.

  *x*
    Left x coordinate of the display.  If None, defaults to the x coordinate of
    the tkwindow parent, if any.
  *y*
    Top y coordinate of the display.  If None, defaults to the y coordinate of
    the tkwindow parent, if any.
  *w*
    Width of the display.  If None, full the width of the screen.
  *h*
    Height of the display.  If None, full the height of the screen.
  *near*
    This will be used for the default instance of Camera *near* plane
  *far*
    This will be used for the default instance of Camera *far* plane
  *fov*
    Used to define the Camera lens field of view
  *depth*
    The bit depth of the display - must be 8, 16 or 24.
  *background*
    r,g,b,alpha (opacity)
  *tk*
    Do we use the tk windowing system?
  *window_title*
    A window title for tk windows only.
  *window_parent*
    An optional tk parent window.
  *mouse*
    Automatically create a Mouse.
  *frames_per_second*
    Maximum frames per second to render (None means "free running").
  """
  if tk:
    from pi3d.util import TkWin
    if not (w and h):
      # TODO: how do we do full-screen in tk?
      #LOGGER.error("Can't compute default window size when using tk")
      #raise Exception
      # ... just force full screen - TK will automatically fit itself into the screen
      w = 1920
      h = 1180
    tkwin = TkWin.TkWin(window_parent, window_title, w, h)
    tkwin.update()
    if x is None:
      x = tkwin.winx
    if y is None:
      y = tkwin.winy

  else:
    tkwin = None
    x = x or 0
    y = y or 0

  display = Display(tkwin)
  if (w or 0) <= 0:
    w = display.max_width - 2 * x
    if w <= 0:
      w = display.max_width
  if (h or 0) <= 0:
    h = display.max_height - 2 * y
    if h <= 0:
      h = display.max_height
  LOGGER.debug('Display size is w=%d, h=%d', w, h)

  display.frames_per_second = frames_per_second

  if near is None:
    near = DEFAULT_NEAR
  if far is None:
    far = DEFAULT_FAR

  display.width = w
  display.height = h
  display.near = near
  display.far = far
  display.fov = fov

  display.left = x
  display.top = y
  display.right = x + w
  display.bottom = y + h

  display.opengl.create_display(x, y, w, h, depth)
  display.mouse = None

  if mouse:
    from pi3d.Mouse import Mouse
    display.mouse = Mouse(width=w, height=h)
    display.mouse.start()

  # This code now replaced by camera 'lens'
  """opengles.glMatrixMode(GL_PROJECTION)
  Utility.load_identity()
  if is_3d:
    hht = near * math.tan(math.radians(aspect / 2.0))
    hwd = hht * w / h
    opengles.glFrustumf(c_float(-hwd), c_float(hwd), c_float(-hht), c_float(hht),
                        c_float(near), c_float(far))
    opengles.glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
  else:
    opengles.glOrthof(c_float(0), c_float(w), c_float(0), c_float(h),
                      c_float(near), c_float(far))
  """
  opengles.glMatrixMode(GL_MODELVIEW)
  Utility.load_identity()


  if background:
    display.set_background(*background)

  return display

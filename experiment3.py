from psychopy import visual, event, core
import numpy as np
import pyglet.gl as gl
from PIL import Image

# params
win_size = [800, 600]
eye_sep = 0.1
camera_z = 2.5
sphere_radius = 0.5

# main window
win = visual.Window(size=win_size, color='black', units='pix', allowGUI=False, useFBO=True)

def set_camera(eye_offset):
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.gluPerspective(60, win_size[0] / win_size[1], 0.1, 100.0)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    gl.gluLookAt(eye_offset, 0, camera_z,   # eyes
                 0, 0, 0,                   # look origin
                 0, 1, 0)                   # up vector

def draw_scene():
    quad = gl.gluNewQuadric()
    gl.glColor3f(1, 1, 1)
    gl.gluSphere(quad, sphere_radius, 48, 48) #white sphere

def capture_frame():
    buffer = (gl.GLubyte * (3 * win_size[0] * win_size[1]))()
    gl.glReadPixels(0, 0, win_size[0], win_size[1], gl.GL_RGB, gl.GL_UNSIGNED_BYTE, buffer)
    image = np.frombuffer(buffer, dtype=np.uint8).reshape((win_size[1], win_size[0], 3))
    image = np.flipud(image)  # flip vertically
    return image

# LEFT EYE RENDERING
win.clearBuffer()
set_camera(-eye_sep / 2)
draw_scene()
win.flip()
core.wait(0.05)  # give time to render
img_left = capture_frame()

# RIGHT EYE RENDERING
win.clearBuffer()
set_camera(+eye_sep / 2)
draw_scene()
win.flip()
core.wait(0.05)
img_right = capture_frame()

# Anaglyph image
anaglyph = np.zeros_like(img_left)
anaglyph[..., 0] = img_left[..., 0]  # red left eye
anaglyph[..., 1] = img_right[..., 1]  # green right
anaglyph[..., 2] = img_right[..., 2]  # blue  right for cyan

# anagplyh in psychoPy
stim = visual.ImageStim(win, image=anaglyph, size=win.size, units='pix')
stim.draw()
#win.flip()

event.waitKeys()
win.close()
core.quit()

from psychopy import visual, event, core
import numpy as np
from PIL import Image

# params
win_size = [800, 600]
n_lines = 50
disparity_pixels = 10  # Horizontal shift between left and right eye views

# setting up window
win = visual.Window(size=win_size, color='black', units='pix')

# PIL
img_size = win_size[::-1]  # PIL

# left/right images
def generate_eye_images(disparity):
    img_left = Image.new("L", img_size, color=0)
    img_right = Image.new("L", img_size, color=0)

    for _ in range(n_lines):
        x0 = np.random.randint(0, win_size[0])
        y0 = np.random.randint(0, win_size[1])
        length = np.random.randint(30, 100)
        angle = np.random.uniform(0, 2 * np.pi)

        x1 = int(x0 + length * np.cos(angle))
        y1 = int(y0 + length * np.sin(angle))

        # disparity
        x0_left = x0 - disparity // 2
        x0_right = x0 + disparity // 2
        x1_left = x1 - disparity // 2
        x1_right = x1 + disparity // 2

        # white lines in each image
        from PIL import ImageDraw
        draw_left = ImageDraw.Draw(img_left)
        draw_right = ImageDraw.Draw(img_right)
        draw_left.line((x0_left, y0, x1_left, y1), fill=255, width=2)
        draw_right.line((x0_right, y0, x1_right, y1), fill=255, width=2)

    return img_left, img_right

# anaglyph
def make_anaglyph(img_left, img_right):
    img_rgb = Image.merge("RGB", (
        img_left,        # left
        img_right,       # right
        img_right        # right (for cyan)
    ))
    return img_rgb


left, right = generate_eye_images(disparity_pixels)
anaglyph = make_anaglyph(left, right)

# saving
anaglyph.save("anaglyph_output.png")

# Psychopy image stimulus
stim = visual.ImageStim(win, image=anaglyph)

# show image
stim.draw()
win.flip()

# keypress to close everything
event.waitKeys()
win.close()
core.quit()

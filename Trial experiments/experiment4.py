from psychopy import visual, event, core
import numpy as np

# params
win_size = [800, 600]
dot_n = 500
dot_size = 4
disparity = 40  # in pixels (+ = closer, - = farther)
duration = 30  # seconds

# === Setup Normal (Mono) Window ===
win = visual.Window(
    size=win_size,
    color=[0, 0, 0],
    units='pix',
    fullscr=False
)


def generate_dots(n, xrange, yrange):
    xs = np.random.uniform(-xrange, xrange, n)
    ys = np.random.uniform(-yrange, yrange, n)
    return xs, ys

# === Generate Dot Coordinates ===
xlim = win_size[0] // 2 - 50
ylim = win_size[1] // 2 - 50
xs, ys = generate_dots(dot_n, xlim, ylim)

# === Prepare Dot Stimuli ===
dots_red = visual.ElementArrayStim(
    win=win,
    nElements=dot_n,
    elementTex=None,
    elementMask='circle',
    sizes=dot_size,
    colors=[[1, 0, 0]] * dot_n,  # RED
    colorSpace='rgb',
    units='pix'
)

dots_cyan = visual.ElementArrayStim(
    win=win,
    nElements=dot_n,
    elementTex=None,
    elementMask='circle',
    sizes=dot_size,
    colors=[[0, 1, 1]] * dot_n,  # CYAN (G+B)
    colorSpace='rgb',
    units='pix'
)

# === Display Loop ===
print("Press any key to exit early.")
clock = core.Clock()
while clock.getTime() < duration:
    # Update dot positions with disparity
    dots_red.xys = np.column_stack((xs - disparity / 2, ys))    # left eye
    dots_cyan.xys = np.column_stack((xs + disparity / 2, ys))   # right eye

    # drawing both layers
    dots_red.draw()
    dots_cyan.draw()

    win.flip()

    # Early exit
    if event.getKeys():
        break

win.close()
core.quit()

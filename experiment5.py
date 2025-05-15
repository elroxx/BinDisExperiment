from psychopy import visual, event, core
import numpy as np
import csv


win = visual.Window(size=[800, 600], color=[0, 0, 0], units='pix', fullscr=False)

# parameters
dot_n = 500
dot_size = 4
stim_duration = 2.0
response_keys = ['left', 'right']
disparity_values = [-10, -5, 0, 5, 10]  # Different disparities (negative = farther, positive = closer)
n_trials = 10

# generating the dots
def generate_dots(n, xrange, yrange):
    xs = np.random.uniform(-xrange, xrange, n)
    ys = np.random.uniform(-yrange, yrange, n)
    return xs, ys

xlim, ylim = 350, 250

# stimulus creation
dots_red = visual.ElementArrayStim(
    win=win, nElements=dot_n, elementTex=None, elementMask='circle',
    sizes=dot_size, colors=[[1, 0, 0]] * dot_n, colorSpace='rgb', units='pix'
)

dots_cyan = visual.ElementArrayStim(
    win=win, nElements=dot_n, elementTex=None, elementMask='circle',
    sizes=dot_size, colors=[[0, 1, 1]] * dot_n, colorSpace='rgb', units='pix'
)

# so that we can writerow afterwards
with open('responses.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['trial', 'disparity', 'response', 'reaction_time'])

    # each trial
    for trial_num in range(1, n_trials + 1):
        # random disparity
        disparity = np.random.choice(disparity_values)

        # generate new dots for trial
        xs, ys = generate_dots(dot_n, xlim, ylim)
        dots_red.xys = np.column_stack((xs - disparity/2, ys))
        dots_cyan.xys = np.column_stack((xs + disparity/2, ys))

        # stimulus showing
        dots_red.draw()
        dots_cyan.draw()
        #win.flip()

        core.wait(stim_duration)

        # clearing thescreen
        win.flip()

        # get response
        clock = core.Clock()
        keys = event.waitKeys(keyList=response_keys + ['escape'], timeStamped=clock)

        # handle response
        if keys:
            key, rt = keys[0]
            if key == 'escape':
                print("Experiment aborted by user.")
                break
        else:
            key, rt = 'none', 'NA'

        #print
        print(f"Trial {trial_num} | Disparity: {disparity} | Response: {key} | RT: {rt}")

        # csv
        writer.writerow([trial_num, disparity, key, rt])

win.close()
core.quit()

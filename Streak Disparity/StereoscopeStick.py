from psychopy import visual, event, core, sound
import csv
import random
import numpy as np
from datetime import datetime


#window dimensions
window_width =  300 # 600 originally
window_height = 300 #600 originally

left_win = visual.Window(
    size=[window_width, window_height],
    color=[-1, -1, -1],
    units='pix',
    fullscr=False,
    pos=[450, 300],  # left window
    screen=0
)

right_win = visual.Window(
    size=[window_width, window_height],
    color=[-1, -1, -1],
    units='pix',
    fullscr=False,
    pos=[window_width + 450, 300],  #right window
    screen=0
)

#params
stick_length = 100
stick_width = 4
stim_duration = 1.5 #either I can put 2 if I want it longer, or 1 seconds to make them speed up a little bit
response_keys = ['left', 'right']
#theta_values = [2, 4, 6, 8]
theta_values = [0.06, 0.12, 0.24, 0.6, 1, 2, 4]
#theta_values = [4, 8, 12, 16, 20, 24]
trials_per_theta = 10
n_trials = len(theta_values) * trials_per_theta  # so 40 total
separation_distance = 100
ping_sound = sound.Sound(value=400, secs=0.05, hamming=True)

# randomize my list with 10 of each
trial_list = []
for theta in theta_values:
    for _ in range(trials_per_theta):
        trial_list.append(theta)
random.shuffle(trial_list)


def create_stick_coords(center_x, center_y, angle_deg, length):
    angle_rad = np.radians(angle_deg)
    half_length = length / 2

    start_x = center_x - half_length * np.sin(angle_rad)
    start_y = center_y - half_length * np.cos(angle_rad)
    end_x = center_x + half_length * np.sin(angle_rad)
    end_y = center_y + half_length * np.cos(angle_rad)

    return [start_x, start_y], [end_x, end_y]


def create_line_stimuli(left_theta, right_theta, left_window, right_window):
    left_center_x = -separation_distance / 2
    left_center_y = 0
    right_center_x = separation_distance / 2
    right_center_y = 0

    #left == red
    left_red_start, left_red_end = create_stick_coords(left_center_x, left_center_y, -left_theta / 2, stick_length)
    right_red_start, right_red_end = create_stick_coords(right_center_x, right_center_y, -right_theta / 2, stick_length)

    left_red_line = visual.Line(left_window,
                                start=left_red_start, end=left_red_end,
                                lineWidth=stick_width, lineColor='white')
    right_red_line = visual.Line(left_window,
                                 start=right_red_start, end=right_red_end,
                                 lineWidth=stick_width, lineColor='white')

    # right == cyan
    left_cyan_start, left_cyan_end = create_stick_coords(left_center_x, left_center_y, left_theta / 2, stick_length)
    right_cyan_start, right_cyan_end = create_stick_coords(right_center_x, right_center_y, right_theta / 2,
                                                           stick_length)

    left_cyan_line = visual.Line(right_window,
                                 start=left_cyan_start, end=left_cyan_end,
                                 lineWidth=stick_width, lineColor='white')
    right_cyan_line = visual.Line(right_window,
                                  start=right_cyan_start, end=right_cyan_end,
                                  lineWidth=stick_width, lineColor='white')

    return [left_red_line, right_red_line], [left_cyan_line, right_cyan_line]


# instructions on both
instructions_left = visual.TextStim(left_win,
                                    text='STEREOSCOPE EXPERIMENT\n            LEFT EYE\n\nCompare inclination between images\nLEFT arrow: left has the bottom coming towards you (floor)\nRIGHT arrow: right has the bottom coming towards you (floor)\nESC: quit\n\nPress SPACE to start',
                                    pos=[0, 0], color='white', height=12, wrapWidth=280)

instructions_right = visual.TextStim(right_win,
                                     text='STEREOSCOPE EXPERIMENT\nRIGHT           EYE\n\nCompare inclination between images\nLEFT arrow: left has the bottom coming towards you (floor)\nRIGHT arrow: right has the bottom coming towards you (floor)\nESC: quit\n\nPress SPACE to start',
                                     pos=[0, 0], color='white', height=12, wrapWidth=280)

# instructions on both
instructions_left.draw()
instructions_right.draw()
left_win.flip()
right_win.flip()
event.waitKeys(keyList=['space'])

# csv

# timestamp for name
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
csv_filename = f'responses\stereoscope_responses_{timestamp}.csv'

with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['trial', 'left_theta', 'right_theta', 'correct_answer', 'response', 'correct', 'reaction_time'])

    for trial_num in range(1, n_trials + 1):
        #random value once, and randomly choose the one
        #theta_single_list = random.sample(theta_values, 1)
        #theta = theta_single_list[0]

        theta = trial_list[trial_num - 1] #theta is preshuffled now
        correct = random.randint(0, 1)
        if correct == 0:
            left_theta = theta
            right_theta = -theta
        else:
            left_theta= -theta
            right_theta = theta


        # correct answer
        correct_answer = 'left' if correct == 0 else 'right'

        # line stimuli
        left_lines, right_lines = create_line_stimuli(left_theta, right_theta, left_win, right_win)

        # all lines drawn
        for line in left_lines:
            line.draw()
        for line in right_lines:
            line.draw()

        trial_info_left = visual.TextStim(left_win,
                                          text=f'Trial {trial_num}/{n_trials}\nLEFT EYE\nWhich is more inclined?',
                                          pos=[0, 250], color='yellow', height=14)
        trial_info_right = visual.TextStim(right_win,
                                           text=f'Trial {trial_num}/{n_trials}\nRIGHT EYE\nWhich is more inclined?',
                                           pos=[0, 250], color='yellow', height=14)

        trial_info_left.draw()
        trial_info_right.draw()

        left_win.flip()
        right_win.flip()

        #core.wait(stim_duration)

        # clear+get response
        #left_win.flip()
        #right_win.flip()

        clock = core.Clock()
        keys = event.waitKeys(keyList=response_keys + ['escape'], timeStamped=clock)

        if keys:
            key, rt = keys[0]
            ping_sound.play()
            if key == 'escape':
                print("Experiment aborted by user.")
                break
        else:
            key, rt = 'none', 'NA'

        # if good
        is_correct = (key == correct_answer)

        # feedback
        #PROBABLY PLAY A SOUND
        """if key != 'none':
            if is_correct:
                feedback_text = f"Correct! Left: {left_theta}°, Right: {right_theta}°"
                feedback_color = 'green'
            else:
                feedback_text = f"Incorrect. Left: {left_theta}°, Right: {right_theta}°"
                feedback_color = 'red'
        else:
            feedback_text = "No response detected"
            feedback_color = 'white'

        feedback_left = visual.TextStim(left_win, text=feedback_text, pos=[0, 0],
                                        color=feedback_color, height=16)
        feedback_right = visual.TextStim(right_win, text=feedback_text, pos=[0, 0],
                                         color=feedback_color, height=16)

        feedback_left.draw()
        feedback_right.draw()
        left_win.flip()
        right_win.flip()
        core.wait(1.5)"""

        print(
            f"Trial {trial_num} | Left θ: {left_theta}° | Right θ: {right_theta}° | Correct: {correct_answer} | Response: {key} | Accuracy: {is_correct} | RT: {rt}")

        # tocsv
        writer.writerow([trial_num, left_theta, right_theta, correct_answer, key, is_correct, rt])

        core.wait(0.5)

print("\nExperiment completed!")
results_text_left = visual.TextStim(left_win,
                                    text='Experiment completed!\nStereoscope rendering complete\nCheck stereoscope_responses.csv\nPress any key to exit',
                                    pos=[0, 0], color='white', height=16)
results_text_right = visual.TextStim(right_win,
                                     text='Experiment completed!\nStereoscope rendering complete\nCheck stereoscope_responses.csv\nPress any key to exit',
                                     pos=[0, 0], color='white', height=16)

results_text_left.draw()
results_text_right.draw()
left_win.flip()
right_win.flip()
event.waitKeys()

#close everything
left_win.close()
right_win.close()
core.quit()
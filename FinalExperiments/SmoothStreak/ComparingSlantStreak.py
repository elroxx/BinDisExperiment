from psychopy import visual, event, core, sound
import csv
import random
import os
import re
from datetime import datetime
import numpy as np

# window dimensions
window_width = 740
window_height = 920

left_win = visual.Window(
    size=[window_width, window_height],
    color=[-1, -1, -1],
    units='pix',
    fullscr=False,
    pos=[5, 0],  # left window
    screen=0
)

right_win = visual.Window(
    size=[window_width, window_height],
    color=[-1, -1, -1],
    units='pix',
    fullscr=False,
    pos=[window_width + 5, 0],  # right window
    screen=0
)

# params
stim_duration = 600  # stimulus display duration
inter_trial_interval = 0.8  # black screen duration between trials
response_keys = ['left', 'right']
repetitions_per_comparison = 2  # number of repetitions per comparison pair
image_folder = 'StreakImages'

# fixation point parameters
fixation_size = 20  # size of fixation cross in pixels

# pings
ping_sound = sound.Sound(value=400, secs=0.05, hamming=True)  # feedback on keypress
change_sound = sound.Sound(value=800, secs=0.1, hamming=True)  # when timeout

# create red fixation crosses for both windows
fixation_h_left = visual.Line(left_win, start=[-fixation_size / 2, 0], end=[fixation_size / 2, 0],
                              lineColor='red', lineWidth=3, pos=[0, 0])
fixation_v_left = visual.Line(left_win, start=[0, -fixation_size / 2], end=[0, fixation_size / 2],
                              lineColor='red', lineWidth=3, pos=[0, 0])

fixation_h_right = visual.Line(right_win, start=[-fixation_size / 2, 0], end=[fixation_size / 2, 0],
                               lineColor='red', lineWidth=3, pos=[0, 0])
fixation_v_right = visual.Line(right_win, start=[0, -fixation_size / 2], end=[0, fixation_size / 2],
                               lineColor='red', lineWidth=3, pos=[0, 0])

# create blue border lines between images
border_left = visual.Line(left_win, start=[0, -window_height / 2], end=[0, window_height / 2],
                          lineColor='blue', lineWidth=2, pos=[0, 0])
border_right = visual.Line(right_win, start=[0, -window_height / 2], end=[0, window_height / 2],
                           lineColor='blue', lineWidth=2, pos=[0, 0])


def get_image_pairs():
    if not os.path.exists(image_folder):
        raise FileNotFoundError(f"Image folder '{image_folder}' not found!")

    image_files = os.listdir(image_folder)
    theta_values = set()

    # pattern matching
    pattern = r'theta_(\d+_\d+)_roughness_(\d+_\d+)_left_eye\.png'

    for filename in image_files:
        match = re.match(pattern, filename)
        if match:
            theta_str = match.group(1)
            roughness_str = match.group(2)

            # need right eye as well
            right_eye_filename = f'theta_{theta_str}_roughness_{roughness_str}_right_eye.png'
            if right_eye_filename in image_files:
                theta_values.add((theta_str.replace('_', '.'), roughness_str.replace('_', '.')))

    return list(theta_values)


def create_trial_list():
    image_pairs = get_image_pairs()

    if not image_pairs:
        raise ValueError("No valid image pairs found in the StreakImages folder!")

    trial_list = []

    # every pair
    for i, (theta1, roughness1) in enumerate(image_pairs):
        for j, (theta2, roughness2) in enumerate(image_pairs):
            if i < j:  # avoid duplicates
                for _ in range(repetitions_per_comparison):
                    if random.random() < 0.5:
                        trial_list.append(((theta1, roughness1), (theta2, roughness2)))
                    else:
                        trial_list.append(((theta2, roughness2), (theta1, roughness1)))

    random.shuffle(trial_list)
    return trial_list


def load_and_crop_image(theta_str, roughness_str, eye, crop_side='left'):
    theta_filename = theta_str.replace('.', '_')
    roughness_filename = roughness_str.replace('.', '_')

    image_path = os.path.join(image_folder, f'theta_{theta_filename}_roughness_{roughness_filename}_{eye}_eye.png')

    #full img first for dimensaions
    temp_stim = visual.ImageStim(left_win, image=image_path)
    original_size = temp_stim.size

    #cropped img
    if crop_side == 'left':
        crop_size = [original_size[0], original_size[1]]
        pos_x = -window_width / 4  # position left half on left side
    else:  # crop_side == 'right'
        crop_size = [original_size[0], original_size[1]]
        pos_x = window_width / 4  # position right half on right side

    return image_path, crop_size, pos_x


def create_side_by_side_stimuli(left_condition, right_condition):
    theta1_str, roughness1_str = left_condition
    theta2_str, roughness2_str = right_condition

    #left window
    left_img1_path, crop_size, pos1_x = load_and_crop_image(theta1_str, roughness1_str, 'left', 'left')
    left_img2_path, _, pos2_x = load_and_crop_image(theta2_str, roughness2_str, 'left', 'right')

    left_stim1 = visual.ImageStim(left_win, image=left_img1_path, size=crop_size, pos=[pos1_x, 0])
    left_stim2 = visual.ImageStim(left_win, image=left_img2_path, size=crop_size, pos=[pos2_x, 0])

    #right window
    right_img1_path, crop_size, pos1_x = load_and_crop_image(theta1_str, roughness1_str, 'right', 'left')
    right_img2_path, _, pos2_x = load_and_crop_image(theta2_str, roughness2_str, 'right', 'right')

    right_stim1 = visual.ImageStim(right_win, image=right_img1_path, size=crop_size, pos=[pos1_x, 0])
    right_stim2 = visual.ImageStim(right_win, image=right_img2_path, size=crop_size, pos=[pos2_x, 0])

    return (left_stim1, left_stim2), (right_stim1, right_stim2)


# instructions on both windows
instructions_left = visual.TextStim(left_win,
                                    text='STEREOSCOPE EXPERIMENT\n              LEFT EYE\n\nLook at the two streaks side by side\nLEFT arrow: left streak more vertical\nRIGHT arrow: right streak more vertical\nESC: quit\n\nPress SPACE to start',
                                    pos=[0, 0], color='white', height=12, wrapWidth=280)

instructions_right = visual.TextStim(right_win,
                                     text='STEREOSCOPE EXPERIMENT\nRIGHT           EYE\n\nLook at the two streaks side by side\nLEFT arrow: left streak more vertical\nRIGHT arrow: right streak more vertical\nESC: quit\n\nPress SPACE to start',
                                     pos=[0, 0], color='white', height=12, wrapWidth=280)

# display instructions
instructions_left.draw()
instructions_right.draw()
left_win.flip()
right_win.flip()
event.waitKeys(keyList=['space'])

# create trial list
try:
    trial_list = create_trial_list()
    n_trials = len(trial_list)
    print(f"Found {len(get_image_pairs())} unique theta values")
    print(f"Total trials: {n_trials}")
except Exception as e:
    print(f"Error loading images: {e}")
    core.quit()

# csv setup
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
csv_filename = f'streakresponses/stereoscope_comparison_responses_{timestamp}.csv'

os.makedirs('streakresponses', exist_ok=True)

with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(
        ['trial', 'left_theta', 'left_roughness', 'right_theta', 'right_roughness', 'response', 'reaction_time'])

    for trial_num in range(1, n_trials + 1):
        # blank screen between trials
        if trial_num > 1:
            left_win.flip()
            right_win.flip()
            core.wait(inter_trial_interval)

        left_condition, right_condition = trial_list[trial_num - 1]
        left_theta, left_roughness = left_condition
        right_theta, right_roughness = right_condition

        try:
            # create side-by-side stimuli
            (left_stim1, left_stim2), (right_stim1, right_stim2) = create_side_by_side_stimuli(left_condition,
                                                                                               right_condition)

            # draw stimuli, borders, and fixation crosses
            left_stim1.draw()
            left_stim2.draw()
            border_left.draw()
            fixation_h_left.draw()
            fixation_v_left.draw()

            right_stim1.draw()
            right_stim2.draw()
            border_right.draw()
            fixation_h_right.draw()
            fixation_v_right.draw()

            left_win.flip()
            right_win.flip()

            # wait for response or timeout
            clock = core.Clock()
            keys = event.waitKeys(keyList=response_keys + ['escape'], timeStamped=clock, maxWait=stim_duration)

            if keys:
                key, rt = keys[0]
                ping_sound.play()  # keypress feedback
                if key == 'escape':
                    print("Experiment aborted by user.")
                    break
            else:
                # TIMEOUT
                key, rt = 'none', 'NA'
                change_sound.play()

            print(
                f"Trial {trial_num}/{n_trials} | Left: θ={left_theta} | Right: θ={right_theta} | Response: {key} | RT: {rt}")

            # write to csv
            writer.writerow([trial_num, left_theta, left_roughness, right_theta, right_roughness, key, rt])

            core.wait(0.5)

        except Exception as e:
            print(f"Error loading images for trial {trial_num}: {e}")
            continue

print("\nExperiment completed!")
results_text_left = visual.TextStim(left_win,
                                    text='Experiment completed!\nStereoscope comparison complete\nCheck stereoscope_comparison_responses.csv\nPress any key to exit',
                                    pos=[0, 0], color='white', height=16)
results_text_right = visual.TextStim(right_win,
                                     text='Experiment completed!\nStereoscope comparison complete\nCheck stereoscope_comparison_responses.csv\nPress any key to exit',
                                     pos=[0, 0], color='white', height=16)

results_text_left.draw()
results_text_right.draw()
left_win.flip()
right_win.flip()
event.waitKeys()

# close everything
left_win.close()
right_win.close()
core.quit()
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

#ref stick params
reference_theta = 2.0  # reference stick theta value in degrees
stick_length = 300
stick_width = 2
separation_distance = 0  # distance between left and right stimuli

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

# create blue border lines between left stick and right image
border_left = visual.Line(left_win, start=[0, -window_height / 2], end=[0, window_height / 2],
                          lineColor='blue', lineWidth=2, pos=[0, 0])
border_right = visual.Line(right_win, start=[0, -window_height / 2], end=[0, window_height / 2],
                           lineColor='blue', lineWidth=2, pos=[0, 0])


def create_stick_coords(center_x, center_y, angle_deg, length):
    angle_rad = np.radians(angle_deg)
    half_length = length / 2
    center_y=center_y-150
    start_x = center_x - half_length * np.sin(angle_rad)
    start_y = center_y - half_length * np.cos(angle_rad)
    end_x = center_x + half_length * np.sin(angle_rad)
    end_y = center_y + half_length * np.cos(angle_rad)

    return [start_x, start_y], [end_x, end_y]


def create_reference_stick(theta_deg, left_window, right_window):
    #pos
    left_center_x = -window_width / 4
    left_center_y = 0

    left_start, left_end = create_stick_coords(left_center_x, left_center_y, -theta_deg / 2, stick_length)
    left_stick = visual.Line(left_window,
                             start=left_start, end=left_end,
                             lineWidth=stick_width, lineColor='white')

    # right window
    right_start, right_end = create_stick_coords(left_center_x, left_center_y, theta_deg / 2, stick_length)
    right_stick = visual.Line(right_window,
                              start=right_start, end=right_end,
                              lineWidth=stick_width, lineColor='white')

    return left_stick, right_stick


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

    print(f"Using reference stick with theta = {reference_theta} degrees")

    trial_list = []

    #Left side always ref stick
    for comparison_condition in image_pairs:
        for _ in range(repetitions_per_comparison):
            #(Left side of each window)
            trial_list.append(comparison_condition)

    random.shuffle(trial_list)
    return trial_list


def load_and_crop_image(theta_str, roughness_str, eye, crop_side='right'):
    theta_filename = theta_str.replace('.', '_')
    roughness_filename = roughness_str.replace('.', '_')

    image_path = os.path.join(image_folder, f'theta_{theta_filename}_roughness_{roughness_filename}_{eye}_eye.png')

    #full img to get dimension
    temp_stim = visual.ImageStim(left_win, image=image_path)
    original_size = temp_stim.size

    #right eye on right window
    crop_size = [original_size[0] / 2, original_size[1]]
    pos_x = window_width / 4  # position right eye on right side

    return image_path, crop_size, pos_x


def create_stick_vs_image_stimuli(comparison_condition):
    theta_str, roughness_str = comparison_condition

    #create left stick
    left_stick, right_stick = create_reference_stick(reference_theta, left_win, right_win)

    # left window, left eye
    left_img_path, crop_size, pos_x = load_and_crop_image(theta_str, roughness_str, 'left', 'right')
    left_img_stim = visual.ImageStim(left_win, image=left_img_path, size=crop_size, pos=[pos_x, 0])

    #right window, right eye
    right_img_path, _, _ = load_and_crop_image(theta_str, roughness_str, 'right', 'right')
    right_img_stim = visual.ImageStim(right_win, image=right_img_path, size=crop_size, pos=[pos_x, 0])

    return (left_stick, left_img_stim), (right_stick, right_img_stim)


# instructions on both windows
instructions_left = visual.TextStim(left_win,
                                    text='STEREOSCOPE EXPERIMENT\n              LEFT EYE\n\nCompare the two streaks side by side\nLEFT streak is the REFERENCE STICK\nLEFT arrow: left streak more vertical\nRIGHT arrow: right streak more vertical\nESC: quit\n\nPress SPACE to start',
                                    pos=[0, 0], color='white', height=12, wrapWidth=280)

instructions_right = visual.TextStim(right_win,
                                     text='STEREOSCOPE EXPERIMENT\nRIGHT           EYE\n\nCompare the two streaks side by side\nLEFT streak is the REFERENCE STICK\nLEFT arrow: left streak more vertical\nRIGHT arrow: right streak more vertical\nESC: quit\n\nPress SPACE to start',
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
    print(f"Found {len(get_image_pairs())} unique theta/roughness combinations")
    print(f"Reference stick theta: {reference_theta} degrees")
    print(f"Total trials: {n_trials}")
except Exception as e:
    print(f"Error loading images: {e}")
    core.quit()

# csv setup
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
csv_filename = f'streakresponses/stereoscope_stick_vs_image_{timestamp}.csv'

os.makedirs('streakresponses', exist_ok=True)

with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(
        ['trial', 'reference_theta_stick', 'comparison_theta', 'comparison_roughness', 'response', 'reaction_time'])

    for trial_num in range(1, n_trials + 1):
        # blank screen between trials
        if trial_num > 1:
            left_win.flip()
            right_win.flip()
            core.wait(inter_trial_interval)

        comparison_condition = trial_list[trial_num - 1]
        comparison_theta, comparison_roughness = comparison_condition

        try:
            # create stick vs image stimuli
            (left_stick, left_img), (right_stick, right_img) = create_stick_vs_image_stimuli(comparison_condition)

            # draw stimuli, borders, and fixation crosses
            left_stick.draw()
            left_img.draw()
            border_left.draw()
            fixation_h_left.draw()
            fixation_v_left.draw()

            right_stick.draw()
            right_img.draw()
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
                f"Trial {trial_num}/{n_trials} | Reference: stick θ={reference_theta}° | Comparison: image θ={comparison_theta}° | Response: {key} | RT: {rt}")

            # write to csv
            writer.writerow([trial_num, reference_theta, comparison_theta, comparison_roughness, key, rt])

            core.wait(0.5)

        except Exception as e:
            print(f"Error loading images for trial {trial_num}: {e}")
            continue

print("\nExperiment completed!")
results_text_left = visual.TextStim(left_win,
                                    text='Experiment completed!\nStick vs Image comparison complete\nCheck stereoscope_stick_vs_image.csv\nPress any key to exit',
                                    pos=[0, 0], color='white', height=16)
results_text_right = visual.TextStim(right_win,
                                     text='Experiment completed!\nStick vs Image comparison complete\nCheck stereoscope_stick_vs_image.csv\nPress any key to exit',
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
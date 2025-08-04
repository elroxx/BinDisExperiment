from psychopy import visual, event, core, sound
import csv
import random
import os
import re
from datetime import datetime

# window dimensions
window_width = 740  # 300 originally
window_height = 920  # 300 originally

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
stim_duration = 30  # stimulus display duration
inter_trial_interval = 0.8  # black screen duration between trials
response_keys = ['left', 'right']
repetitions_per_theta = 2  # number of repetitions per theta value
image_folder = 'StreakImages'

# pings
ping_sound = sound.Sound(value=400, secs=0.05, hamming=True)  # feedback on keypress
change_sound = sound.Sound(value=800, secs=0.1, hamming=True)  # when timeout




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

            #need right eye as well
            right_eye_filename = f'theta_{theta_str}_roughness_{roughness_str}_right_eye.png'
            if right_eye_filename in image_files:
                theta_values.add((theta_str.replace('_', '.'), roughness_str.replace('_', '.')))

    return list(theta_values)


def create_trial_list():
    image_pairs = get_image_pairs()

    if not image_pairs:
        raise ValueError("No valid image pairs found in the StreakImages folder!")

    trial_list = []
    for theta_str, roughness_str in image_pairs:
        for _ in range(repetitions_per_theta):
            trial_list.append((theta_str, roughness_str))

    random.shuffle(trial_list)
    return trial_list


def load_image_pair(theta_str, roughness_str):
    theta_filename = theta_str.replace('.', '_')
    roughness_filename = roughness_str.replace('.', '_')

    left_eye_path = os.path.join(image_folder, f'theta_{theta_filename}_roughness_{roughness_filename}_left_eye.png')
    right_eye_path = os.path.join(image_folder, f'theta_{theta_filename}_roughness_{roughness_filename}_right_eye.png')

    #img stim
    left_image = visual.ImageStim(left_win, image=left_eye_path, pos=[0, 0])
    right_image = visual.ImageStim(right_win, image=right_eye_path, pos=[0, 0])

    return left_image, right_image


# instructions on both windows
instructions_left = visual.TextStim(left_win,
                                    text='STEREOSCOPE EXPERIMENT\n              LEFT EYE\n\nLook at the streak in the image\nLEFT arrow: streak is below the plane\nRIGHT arrow: streak is laying on the ground\nESC: quit\n\nPress SPACE to start',
                                    pos=[0, 0], color='white', height=12, wrapWidth=280)

instructions_right = visual.TextStim(right_win,
                                     text='STEREOSCOPE EXPERIMENT\nRIGHT           EYE\n\nLook at the streak in the image\nLEFT arrow: streak is below the plane\nRIGHT arrow: streak is laying on the ground\nESC: quit\n\nPress SPACE to start',
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
csv_filename = f'streakresponses/stereoscope_image_responses_{timestamp}.csv'


os.makedirs('streakresponsesresponses', exist_ok=True)

with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['trial', 'theta', 'roughness', 'response', 'reaction_time'])

    for trial_num in range(1, n_trials + 1):
        # blank screen between trials
        if trial_num > 1:
            left_win.flip()
            right_win.flip()
            core.wait(inter_trial_interval)

        theta_str, roughness_str = trial_list[trial_num - 1]

        try:
            # load image pair
            left_image, right_image = load_image_pair(theta_str, roughness_str)


            # display images
            left_image.draw()
            right_image.draw()

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
                f"Trial {trial_num}/{n_trials} | Theta: {theta_str} | Roughness: {roughness_str} | Response: {key} | RT: {rt}")

            # write to csv
            writer.writerow([trial_num, theta_str, roughness_str, key, rt])

            core.wait(0.5)

        except Exception as e:
            print(f"Error loading images for trial {trial_num}: {e}")
            continue

print("\nExperiment completed!")
results_text_left = visual.TextStim(left_win,
                                    text='Experiment completed!\nStereoscope rendering complete\nCheck stereoscope_image_responses.csv\nPress any key to exit',
                                    pos=[0, 0], color='white', height=16)
results_text_right = visual.TextStim(right_win,
                                     text='Experiment completed!\nStereoscope rendering complete\nCheck stereoscope_image_responses.csv\nPress any key to exit',
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
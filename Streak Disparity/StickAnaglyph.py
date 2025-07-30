from psychopy import visual, event, core
import numpy as np
import csv
import random

win = visual.Window(size=[1200, 600], color=[-1, -1, -1], units='pix', fullscr=False, blendMode='add')

# parameters
stick_length = 100
stick_width = 4
stim_duration = 8.0
response_keys = ['left', 'right']
theta_values = [2, 4, 6, 8] #12 cannot fuse at all. over 8 probably cannot fuse either so remove 10 and 12
n_trials = 15
separation_distance = 100


def create_stick_coords(center_x, center_y, angle_deg, length):
    angle_rad = np.radians(angle_deg)
    half_length = length / 2

    start_x = center_x - half_length * np.sin(angle_rad)
    start_y = center_y - half_length * np.cos(angle_rad)
    end_x = center_x + half_length * np.sin(angle_rad)
    end_y = center_y + half_length * np.cos(angle_rad)

    return [start_x, start_y], [end_x, end_y]


def get_line_bounding_box(start_x, start_y, end_x, end_y, line_width):
    margin = line_width / 2 + 1  # small margin
    min_x = int(min(start_x, end_x) - margin)
    max_x = int(max(start_x, end_x) + margin)
    min_y = int(min(start_y, end_y) - margin)
    max_y = int(max(start_y, end_y) + margin)
    return min_x, max_x, min_y, max_y


def get_all_line_pixels(left_theta, right_theta):
    left_center_x = -separation_distance / 2
    left_center_y = 0

    right_center_x = separation_distance / 2
    right_center_y = 0

    left_cyan_start, left_cyan_end = create_stick_coords(left_center_x, left_center_y, left_theta / 2, stick_length)
    left_red_start, left_red_end = create_stick_coords(left_center_x, left_center_y, -left_theta / 2, stick_length)
    right_cyan_start, right_cyan_end = create_stick_coords(right_center_x, right_center_y, right_theta / 2,
                                                           stick_length)
    right_red_start, right_red_end = create_stick_coords(right_center_x, right_center_y, -right_theta / 2, stick_length)

    lines = [
        (*left_cyan_start, *left_cyan_end),
        (*left_red_start, *left_red_end),
        (*right_cyan_start, *right_cyan_end),
        (*right_red_start, *right_red_end)
    ]

    pixel_coords = set()

    for start_x, start_y, end_x, end_y in lines:
        min_x, max_x, min_y, max_y = get_line_bounding_box(start_x, start_y, end_x, end_y, stick_width)

        # convert to pixel coord
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                # to array coord
                array_x = int(x + 1200 / 2)
                array_y = int(600 / 2 - y)

                # Check bounds
                if 0 <= array_x < 1200 and 0 <= array_y < 600:
                    pixel_coords.add((array_x, array_y))

    return pixel_coords


def is_pixel_on_line(pixel_x, pixel_y, start_x, start_y, end_x, end_y, line_width):
    #convert to line coord
    A = end_y - start_y
    B = start_x - end_x
    C = end_x * start_y - start_x * end_y

    # distance line to point
    if A == 0 and B == 0:  # Degenerate case
        return False

    distance = abs(A * pixel_x + B * pixel_y + C) / np.sqrt(A * A + B * B)

    # check if within line width
    if distance > line_width / 2:
        return False

    # Check if within line segment bounds
    min_x = min(start_x, end_x) - line_width / 2
    max_x = max(start_x, end_x) + line_width / 2
    min_y = min(start_y, end_y) - line_width / 2
    max_y = max(start_y, end_y) + line_width / 2

    return min_x <= pixel_x <= max_x and min_y <= pixel_y <= max_y


def compute_pixel_color(pixel_x, pixel_y, left_theta, right_theta):
    # left coordinates
    left_center_x = -separation_distance / 2
    left_center_y = 0

    # right coordinates
    right_center_x = separation_distance / 2
    right_center_y = 0

    # get line coord left
    left_cyan_start, left_cyan_end = create_stick_coords(left_center_x, left_center_y, left_theta / 2, stick_length)
    left_red_start, left_red_end = create_stick_coords(left_center_x, left_center_y, -left_theta / 2, stick_length)

    # get line coord right
    right_cyan_start, right_cyan_end = create_stick_coords(right_center_x, right_center_y, right_theta / 2,
                                                           stick_length)
    right_red_start, right_red_end = create_stick_coords(right_center_x, right_center_y, -right_theta / 2, stick_length)

    # if pixel on line
    on_left_cyan = is_pixel_on_line(pixel_x, pixel_y, *left_cyan_start, *left_cyan_end, stick_width)
    on_left_red = is_pixel_on_line(pixel_x, pixel_y, *left_red_start, *left_red_end, stick_width)
    on_right_cyan = is_pixel_on_line(pixel_x, pixel_y, *right_cyan_start, *right_cyan_end, stick_width)
    on_right_red = is_pixel_on_line(pixel_x, pixel_y, *right_red_start, *right_red_end, stick_width)

    on_any_cyan = on_left_cyan or on_right_cyan
    on_any_red = on_left_red or on_right_red

    if on_any_cyan and on_any_red:
        return 'white'
    elif on_any_cyan:
        return 'cyan'
    elif on_any_red:
        return 'red'
    else:
        return 'black'


def create_pixel_perfect_image(left_theta, right_theta, window_size=None):
    if window_size is None:
        width, height = 1200, 600
    else:
        width, height = window_size

    image = np.zeros((height, width, 3), dtype=np.uint8)

    line_pixels = get_all_line_pixels(left_theta, right_theta)

    for array_x, array_y in line_pixels:
        psychopy_x = array_x - width / 2
        psychopy_y = height / 2 - array_y

        color = compute_pixel_color(psychopy_x, psychopy_y, left_theta, right_theta)

        if color == 'red':
            image[array_y, array_x] = [255, 0, 0]
        elif color == 'cyan':
            image[array_y, array_x] = [0, 255, 255]
        elif color == 'white':
            image[array_y, array_x] = [255, 255, 255]
        # black are still black

    return image


def analyze_pixel_composition(left_theta, right_theta):
    width, height = 1200, 600
    counts = {'red': 0, 'cyan': 0, 'white': 0, 'black': 0}

    # Get only pixels that could contain lines
    line_pixels = get_all_line_pixels(left_theta, right_theta)

    for array_x, array_y in line_pixels:
        # Convert from array coordinates to PsychoPy coordinates
        psychopy_x = array_x - width / 2
        psychopy_y = height / 2 - array_y

        color = compute_pixel_color(psychopy_x, psychopy_y, left_theta, right_theta)
        counts[color] += 1

    # All other pixels are black
    total_line_pixels = len(line_pixels)
    total_pixels = width * height
    counts['black'] += total_pixels - total_line_pixels

    percentages = {color: (count / total_pixels) * 100 for color, count in counts.items()}

    return counts, percentages


# Create image stimulus for pixel-perfect rendering
image_stim = visual.ImageStim(win, size=[1200, 600], units='pix')

# Instructions
instructions = visual.TextStim(win,
                               text='Compare the two anaglyph images.\nPress LEFT arrow if left image has more disparity (bigger θ)\nPress RIGHT arrow if right image has more disparity\nPress ESCAPE to quit\nPress P to save pixel-perfect image\n\nNote: Use red-cyan anaglyph glasses for proper 3D effect\nPixel-perfect rendering: White areas show where red and cyan overlap\nPress SPACE to start',
                               pos=[0, 0], color='white', height=16, wrapWidth=800)

# Show instructions
instructions.draw()
win.flip()
event.waitKeys(keyList=['space'])

#csv
with open('anaglyph_responses.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(
        ['trial', 'left_theta', 'right_theta', 'correct_answer', 'response', 'correct', 'reaction_time', 'red_pixels',
         'cyan_pixels', 'white_pixels', 'black_pixels'])

    for trial_num in range(1, n_trials + 1):
        # get two different random values
        theta_pair = random.sample(theta_values, 2)
        left_theta = theta_pair[0]
        right_theta = theta_pair[1]

        # get correct answer
        correct_answer = 'left' if left_theta > right_theta else 'right'

        start_time = core.getTime()
        pixel_counts, pixel_percentages = analyze_pixel_composition(left_theta, right_theta)
        computation_time = core.getTime() - start_time

        pixel_image = create_pixel_perfect_image(left_theta, right_theta)

        pixel_image_normalized = (pixel_image.astype(np.float32) / 127.5) - 1.0

        # set img data
        image_stim.image = pixel_image_normalized

        image_stim.draw()

        trial_info = visual.TextStim(win,
                                     text=f'Trial {trial_num}/{n_trials} - Which has MORE disparity?',
                                     pos=[0, 250], color='yellow', height=18)
        trial_info.draw()

        # pixel comp
        #pixel_info = visual.TextStim(win,
                                     #text=f'L:{left_theta}° R:{right_theta}° | Red:{pixel_percentages["red"]:.1f}% Cyan:{pixel_percentages["cyan"]:.1f}% White:{pixel_percentages["white"]:.1f}% | Computed: {len(get_all_line_pixels(left_theta, right_theta)):,} pixels',
                                     #pos=[0, -250], color='white', height=12)
        #pixel_info.draw()

        win.flip()

        keys_pressed = event.getKeys()
        if 'p' in keys_pressed:
            print(f"Saving pixel-perfect image for trial {trial_num}...")
            np.save(f'trial_{trial_num}_left{left_theta}_right{right_theta}_pixels.npy', pixel_image)
            print(f"Saved: trial_{trial_num}_left{left_theta}_right{right_theta}_pixels.npy")
            print(f"  Image contains proper white pixels where red and cyan overlap")

        core.wait(stim_duration)

        win.flip()

        # get tresponse
        clock = core.Clock()
        keys = event.waitKeys(keyList=response_keys + ['escape'], timeStamped=clock)

        if keys:
            key, rt = keys[0]
            if key == 'escape':
                print("Experiment aborted by user.")
                break
        else:
            key, rt = 'none', 'NA'

        # response correct
        is_correct = (key == correct_answer)

        # feedback
        if key != 'none':
            if is_correct:
                feedback_text = f"Correct! Left: {left_theta}°, Right: {right_theta}°"
                feedback_color = 'green'
            else:
                feedback_text = f"Incorrect. Left: {left_theta}°, Right: {right_theta}°"
                feedback_color = 'red'
        else:
            feedback_text = "No response detected"
            feedback_color = 'white'

        feedback = visual.TextStim(win, text=feedback_text, pos=[0, 0],
                                   color=feedback_color, height=20)
        feedback.draw()
        win.flip()
        core.wait(1.5)

        # pixels analsysis
        computed_pixels = len(get_all_line_pixels(left_theta, right_theta))
        total_pixels = 1200 * 600
        efficiency_gain = total_pixels / computed_pixels if computed_pixels > 0 else float('inf')

        print(
            f"Trial {trial_num} | Left θ: {left_theta}° | Right θ: {right_theta}° | Correct: {correct_answer} | Response: {key} | Accuracy: {is_correct} | RT: {rt}")
        print(
            f"  Pixel composition: Red: {pixel_counts['red']} ({pixel_percentages['red']:.1f}%), Cyan: {pixel_counts['cyan']} ({pixel_percentages['cyan']:.1f}%), White: {pixel_counts['white']} ({pixel_percentages['white']:.1f}%), Black: {pixel_counts['black']} ({pixel_percentages['black']:.1f}%)")
        print(
            f"  Pixel-perfect rendering: {computed_pixels:,}/{total_pixels:,} pixels computed ({computed_pixels / total_pixels * 100:.2f}%) - {efficiency_gain:.1f}x speedup | Time: {computation_time:.3f}s")

        # csv
        writer.writerow([trial_num, left_theta, right_theta, correct_answer, key, is_correct, rt,
                         pixel_counts['red'], pixel_counts['cyan'], pixel_counts['white'], pixel_counts['black']])


        core.wait(0.5)

# results
print("\nExperiment completed!")
results_text = visual.TextStim(win,
                               text='Experiment completed!\nPixel-perfect anaglyph rendering with proper color blending\nCheck anaglyph_responses.csv for results\nPress any key to exit',
                               pos=[0, 0], color='white', height=20)
results_text.draw()
win.flip()
event.waitKeys()

win.close()
core.quit()

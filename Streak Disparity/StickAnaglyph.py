from psychopy import visual, event, core
import numpy as np
import csv
import random

win = visual.Window(size=[1200, 600], color=[0, 0, 0], units='pix', fullscr=False)

# parameters
stick_length = 100
stick_width = 4
stim_duration = 3.0
response_keys = ['left', 'right']
theta_values = [5, 10, 15, 20, 25, 30, 35, 40]  # Different disparity angles in degrees
n_trials = 15
separation_distance = 400  # Distance between left and right anaglyph images


# Function to create stick coordinates
def create_stick_coords(center_x, center_y, angle_deg, length):
    """Create start and end coordinates for a rotated stick"""
    angle_rad = np.radians(angle_deg)
    half_length = length / 2

    start_x = center_x - half_length * np.sin(angle_rad)
    start_y = center_y - half_length * np.cos(angle_rad)
    end_x = center_x + half_length * np.sin(angle_rad)
    end_y = center_y + half_length * np.cos(angle_rad)

    return [start_x, start_y], [end_x, end_y]


# Create stimulus objects for both anaglyph images
# Left anaglyph image sticks
left_white_stick = visual.Line(win, lineColor='white', lineWidth=stick_width)
left_cyan_stick = visual.Line(win, lineColor='cyan', lineWidth=stick_width)
left_red_stick = visual.Line(win, lineColor='red', lineWidth=stick_width)

# Right anaglyph image sticks
right_white_stick = visual.Line(win, lineColor='white', lineWidth=stick_width)
right_cyan_stick = visual.Line(win, lineColor='cyan', lineWidth=stick_width)
right_red_stick = visual.Line(win, lineColor='red', lineWidth=stick_width)

# Labels for theta values
#left_label = visual.TextStim(win, text='', pos=[-separation_distance / 2, -150],
                             #color='white', height=20)
#right_label = visual.TextStim(win, text='', pos=[separation_distance / 2, -150],
                              #color='white', height=20)

# Instructions
instructions = visual.TextStim(win,
                               text='Compare the two anaglyph images.\nPress LEFT arrow if left image has more disparity (bigger θ)\nPress RIGHT arrow if right image has more disparity\nPress ESCAPE to quit\n\nPress SPACE to start',
                               pos=[0, 0], color='white', height=16, wrapWidth=800)

# Show instructions
instructions.draw()
win.flip()
event.waitKeys(keyList=['space'])

# CSV file for data collection
with open('anaglyph_responses.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['trial', 'left_theta', 'right_theta', 'correct_answer', 'response', 'correct', 'reaction_time'])

    # Run trials
    for trial_num in range(1, n_trials + 1):
        # Select two different random theta values
        theta_pair = random.sample(theta_values, 2)
        left_theta = theta_pair[0]
        right_theta = theta_pair[1]

        # Determine correct answer (which side has bigger theta)
        correct_answer = 'left' if left_theta > right_theta else 'right'

        # Set up left anaglyph image (center at -separation_distance/2, 0)
        left_center_x = -separation_distance / 2
        left_center_y = 0

        # White reference stick (vertical)
        start, end = create_stick_coords(left_center_x, left_center_y, 0, stick_length)
        left_white_stick.start = start
        left_white_stick.end = end

        # Cyan stick (rotated by theta/2 counterclockwise)
        start, end = create_stick_coords(left_center_x, left_center_y, left_theta / 2, stick_length)
        left_cyan_stick.start = start
        left_cyan_stick.end = end

        # Red stick (rotated by theta/2 clockwise)
        start, end = create_stick_coords(left_center_x, left_center_y, -left_theta / 2, stick_length)
        left_red_stick.start = start
        left_red_stick.end = end

        # Set up right anaglyph image (center at +separation_distance/2, 0)
        right_center_x = separation_distance / 2
        right_center_y = 0

        # White reference stick (vertical)
        start, end = create_stick_coords(right_center_x, right_center_y, 0, stick_length)
        right_white_stick.start = start
        right_white_stick.end = end

        # Cyan stick (rotated by theta/2 counterclockwise)
        start, end = create_stick_coords(right_center_x, right_center_y, right_theta / 2, stick_length)
        right_cyan_stick.start = start
        right_cyan_stick.end = end

        # Red stick (rotated by theta/2 clockwise)
        start, end = create_stick_coords(right_center_x, right_center_y, -right_theta / 2, stick_length)
        right_red_stick.start = start
        right_red_stick.end = end

        # Update labels
        #left_label.text = f'θ = {left_theta}°'
        #right_label.text = f'θ = {right_theta}°'

        # Draw stimulus
        left_white_stick.draw()
        left_cyan_stick.draw()
        left_red_stick.draw()
        right_white_stick.draw()
        right_cyan_stick.draw()
        right_red_stick.draw()
        #left_label.draw()
        #right_label.draw()

        # Add trial info at top
        trial_info = visual.TextStim(win,
                                     text=f'Trial {trial_num}/{n_trials} - Which has MORE disparity?',
                                     pos=[0, 250], color='yellow', height=18)
        trial_info.draw()

        win.flip()

        core.wait(stim_duration)

        # Clear screen and get response
        win.flip()

        # Get response with timing
        clock = core.Clock()
        keys = event.waitKeys(keyList=response_keys + ['escape'], timeStamped=clock)

        # Handle response
        if keys:
            key, rt = keys[0]
            if key == 'escape':
                print("Experiment aborted by user.")
                break
        else:
            key, rt = 'none', 'NA'

        # Check if response is correct
        is_correct = (key == correct_answer)

        # Provide feedback
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

        # Print trial info
        print(
            f"Trial {trial_num} | Left θ: {left_theta}° | Right θ: {right_theta}° | Correct: {correct_answer} | Response: {key} | Accuracy: {is_correct} | RT: {rt}")

        # Write to CSV
        writer.writerow([trial_num, left_theta, right_theta, correct_answer, key, is_correct, rt])

        # Brief inter-trial interval
        core.wait(0.5)

# Show final results
print("\nExperiment completed!")
results_text = visual.TextStim(win,
                               text='Experiment completed!\nCheck anaglyph_responses.csv for results\nPress any key to exit',
                               pos=[0, 0], color='white', height=20)
results_text.draw()
win.flip()
event.waitKeys()

win.close()
core.quit()
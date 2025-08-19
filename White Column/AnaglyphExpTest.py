from psychopy import visual, core, event, data, gui
from pyglet.gl import *
import math
import random
import csv
import os
from datetime import datetime
import pandas as pd

good_distances_to_test = [3, 25]
good_disparities = [0.3]


class AnaglyphColumnExperiment:
    def __init__(self, win):
        self.win = win
        self.setup_opengl()

        self.camera_pos = [0, 3.0, 0]
        self.look_at_point = [0, 0, -15]
        self.viewing_vector = self.calculate_viewing_vector()

        self.reference_distance = 15.0
        self.reference_visual_angle_degrees = 1.5

        self.checkerboard_square_size = self.calculate_required_square_size()

        self.generate_checkerboard_floor()

        self.column_geometries = {}
        self.generate_all_column_geometries()

        self.trials = []
        self.current_trial = 0
        self.responses = []
        self.experiment_data = []

        self.eye_separation = 0.1
        self.screen_distance = 0.2 #useless
        self.convergence_distance = math.sqrt(234)

    def calculate_viewing_vector(self):
        vx = self.look_at_point[0] - self.camera_pos[0]
        vy = self.look_at_point[1] - self.camera_pos[1]
        vz = self.look_at_point[2] - self.camera_pos[2]

        length = math.sqrt(vx * vx + vy * vy + vz * vz)
        return [vx / length, vy / length, vz / length]

    def calculate_position_along_vector(self, distance):
        x = self.camera_pos[0] + distance * self.viewing_vector[0]
        y = self.camera_pos[1] + distance * self.viewing_vector[1]
        z = self.camera_pos[2] + distance * self.viewing_vector[2]
        return [x, y, z]

    def calculate_required_square_size(self):
        max_column_width = 0

        for distance in good_distances_to_test:
            size_factor = distance / self.reference_distance
            column_width = 0.8 * size_factor
            column_depth = 0.08 * size_factor

            max_offset = 0.04 * size_factor
            total_width = column_width + 2 * max_offset
            total_depth = column_depth + 2 * max_offset

            max_dimension = max(total_width, total_depth)
            max_column_width = max(max_column_width, max_dimension)

            print(f"Distance {distance}: width={total_width:.3f}, depth={total_depth:.3f}")

        required_size = max_column_width * 3.0
        nice_size = math.ceil(required_size * 2) / 2

        print(f"Maximum column dimension: {max_column_width:.3f}")
        print(f"Required square size (with centering): {nice_size:.3f}")

        return nice_size

    def generate_checkerboard_floor(self):
        floor_size = 60.0
        square_size = self.checkerboard_square_size

        num_squares = int(floor_size / square_size) + 4

        self.floor_white_vertices = []
        self.floor_white_normals = []

        column_positions = []
        for distance in good_distances_to_test:
            pos = self.calculate_position_along_vector(distance)
            column_positions.append((pos[0], pos[2]))
            print(f"Column at distance {distance}: x={pos[0]:.2f}, z={pos[2]:.2f}")

        reference_x = 0.0
        reference_z = column_positions[0][1]

        start_x = reference_x - (num_squares * square_size) / 2
        start_z = reference_z - (num_squares * square_size) / 2

        grid_offset_x = (reference_x - start_x) % square_size - square_size / 2
        grid_offset_z = (reference_z - start_z) % square_size - square_size / 2
        start_x += grid_offset_x
        start_z += grid_offset_z

        column_x_grid_index = round((0.0 - reference_x) / square_size)

        for i in range(num_squares):
            for j in range(num_squares):
                x1 = start_x + i * square_size
                x2 = x1 + square_size
                z1 = start_z + j * square_size
                z2 = z1 + square_size

                square_center_x = (x1 + x2) / 2
                square_center_z = (z1 + z2) / 2

                grid_i = round((square_center_x - reference_x) / square_size)
                grid_j = round((square_center_z - reference_z) / square_size)

                is_in_column_corridor = (grid_i == column_x_grid_index)

                if is_in_column_corridor:
                    print(f"Removing white square in column corridor at ({square_center_x:.1f}, {square_center_z:.1f})")
                    continue

                is_white = (grid_i + grid_j) % 2 == 1

                if is_white:
                    triangle1_vertices = [(x1, 0.0, z1), (x2, 0.0, z1), (x1, 0.0, z2)]
                    triangle1_normals = [(0, 1, 0)] * 3

                    triangle2_vertices = [(x2, 0.0, z1), (x2, 0.0, z2), (x1, 0.0, z2)]
                    triangle2_normals = [(0, 1, 0)] * 3

                    self.floor_white_vertices.extend(triangle1_vertices)
                    self.floor_white_vertices.extend(triangle2_vertices)
                    self.floor_white_normals.extend(triangle1_normals)
                    self.floor_white_normals.extend(triangle2_normals)
                else:
                    for dist, (col_x, col_z) in zip(good_distances_to_test, column_positions):
                        if (abs(square_center_x - col_x) < square_size / 4 and
                                abs(square_center_z - col_z) < square_size / 4):
                            print(f"  Column clearance: x=±{square_size / 2:.1f}, z=±{square_size / 2:.1f}")

        print(f"Total white squares generated: {len(self.floor_white_vertices) // 6}")

    def calculate_disparity_for_point(self, world_x, world_y, world_z, base_disparity_degrees, force_onplane=False):
        if force_onplane:
            plane_distance_x = world_x - self.camera_pos[0]
            plane_distance_y = 0 - self.camera_pos[1]
            plane_distance_z = world_z - self.camera_pos[2]
            plane_distance = math.sqrt(plane_distance_x * plane_distance_x +
                                       plane_distance_y * plane_distance_y +
                                       plane_distance_z * plane_distance_z)

            distance_factor = (self.convergence_distance - plane_distance) / self.convergence_distance
            total_disparity_degrees = base_disparity_degrees + distance_factor * 0.5
        else:
            dx = world_x - self.camera_pos[0]
            dy = world_y - self.camera_pos[1]
            dz = world_z - self.camera_pos[2]
            actual_distance = math.sqrt(dx * dx + dy * dy + dz * dz)

            distance_factor = (self.convergence_distance - actual_distance) / self.convergence_distance
            total_disparity_degrees = base_disparity_degrees + distance_factor * 0.5

        disparity_pixels = total_disparity_degrees * (self.win.size[0] / 60.0)
        return disparity_pixels

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glShadeModel(GL_FLAT)
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def calculate_size_for_distance(self, distance):
        size_factor = distance / self.reference_distance
        return size_factor

    def generate_all_column_geometries(self):
        distances = good_distances_to_test

        for distance in distances:
            self.column_geometries[distance] = self.generate_column_geometry_for_distance(distance)

    def generate_column_geometry_for_distance(self, distance_along_vector):
        column_data = {}
        column_data['vertices'] = []
        column_data['normals'] = []
        column_data['brick_data'] = []
        column_data['position'] = self.calculate_position_along_vector(distance_along_vector)

        size_factor = self.calculate_size_for_distance(distance_along_vector)

        base_total_height = 4.0
        base_brick_width = 0.8
        base_brick_depth = 0.08

        total_height = base_total_height * size_factor
        brick_width = base_brick_width * size_factor
        brick_depth = base_brick_depth * size_factor

        num_bricks = 80
        max_offset = 0.04 * size_factor
        brick_height = total_height / num_bricks
        missing_brick_probability = 0.1

        uniform_brightness = 0.8

        pos = column_data['position']
        print(f"Generating column for distance {distance_along_vector}: "
              f"position=({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}), "
              f"size_factor={size_factor:.3f}, height={total_height:.3f}")
        print(f"  Plane relationship: {'ABOVE' if pos[1] > 0 else 'BELOW'} ground plane")

        for brick_i in range(num_bricks):
            y_top = -brick_i * brick_height
            y_bottom = -(brick_i + 1) * brick_height

            if random.random() < missing_brick_probability:
                continue

            x_offset = random.uniform(-max_offset, max_offset)
            z_offset = random.uniform(-max_offset, max_offset)

            brightness = uniform_brightness + random.uniform(-0.1, 0.1)
            brightness = max(0.6, min(1.0, brightness))

            brick_x = x_offset
            brick_z = z_offset

            x1 = brick_x - brick_width / 2
            x2 = brick_x + brick_width / 2
            z1 = brick_z - brick_depth / 2
            z2 = brick_z + brick_depth / 2

            brick_vertices = []
            brick_normals = []
            self.add_brick_faces(x1, x2, y_top, y_bottom, z1, z2, brick_vertices, brick_normals)

            column_data['brick_data'].append({
                'vertices': brick_vertices,
                'normals': brick_normals,
                'brightness': brightness,
                'base_z': brick_z
            })

        return column_data

    def add_brick_faces(self, x1, x2, y_top, y_bottom, z1, z2, vertices, normals):
        vertices.extend([
            (x1, y_top, z1), (x2, y_top, z1), (x2, y_bottom, z1),
            (x1, y_top, z1), (x2, y_bottom, z1), (x1, y_bottom, z1)
        ])
        normals.extend([(0, 0, 1)] * 6)

        vertices.extend([
            (x2, y_top, z2), (x1, y_top, z2), (x1, y_bottom, z2),
            (x2, y_top, z2), (x1, y_bottom, z2), (x2, y_bottom, z2)
        ])
        normals.extend([(0, 0, -1)] * 6)

        vertices.extend([
            (x1, y_top, z2), (x1, y_top, z1), (x1, y_bottom, z1),
            (x1, y_top, z2), (x1, y_bottom, z1), (x1, y_bottom, z2)
        ])
        normals.extend([(-1, 0, 0)] * 6)

        vertices.extend([
            (x2, y_top, z1), (x2, y_top, z2), (x2, y_bottom, z2),
            (x2, y_top, z1), (x2, y_bottom, z2), (x2, y_bottom, z1)
        ])
        normals.extend([(1, 0, 0)] * 6)

        vertices.extend([
            (x1, y_top, z1), (x1, y_top, z2), (x2, y_top, z2),
            (x1, y_top, z1), (x2, y_top, z2), (x2, y_top, z1)
        ])
        normals.extend([(0, 1, 0)] * 6)

        vertices.extend([
            (x1, y_bottom, z2), (x1, y_bottom, z1), (x2, y_bottom, z1),
            (x1, y_bottom, z2), (x2, y_bottom, z1), (x2, y_bottom, z2)
        ])
        normals.extend([(0, -1, 0)] * 6)

    def load_experiment_conditions(self, csv_filename):
        try:
            df = pd.read_csv(csv_filename)
            self.trials = df.to_dict('records')
            random.shuffle(self.trials)
            print(f"Loaded {len(self.trials)} trials from {csv_filename}")
        except FileNotFoundError:
            print(f"CSV file {csv_filename} not found. Creating default conditions...")
            self.create_default_conditions()

    def create_default_conditions(self):
        disparities = good_disparities
        distances = good_distances_to_test
        onplane_conditions = [True, False]

        self.trials = []
        for disparity in disparities:
            for distance in distances:
                for onplane in onplane_conditions:
                    for repeat in range(2):
                        self.trials.append({
                            'disparity_degrees': disparity,
                            'distance_along_vector': distance,
                            'onplane': onplane,
                            'trial_id': len(self.trials) + 1,
                            'presentation_time': 3.0
                        })

        random.shuffle(self.trials)

        df = pd.DataFrame(self.trials)
        df.to_csv('experiment_conditions.csv', index=False)
        print("Created default experiment_conditions.csv with onplane conditions")

    def setup_anaglyph_camera(self, eye='left', disparity_offset_x=0):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        gluLookAt(
            self.camera_pos[0],
            self.camera_pos[1],
            self.camera_pos[2],
            self.look_at_point[0],
            self.look_at_point[1],
            self.look_at_point[2],
            0.0, 1.0, 0.0
        )

    def render_column_with_proper_disparity(self, distance_along_vector, base_disparity_degrees, eye='left',
                                            color_filter=(1.0, 1.0, 1.0), force_onplane=False):
        if distance_along_vector not in self.column_geometries:
            print(f"Warning: No geometry found for distance {distance_along_vector}")
            return

        column_data = self.column_geometries[distance_along_vector]
        column_position = column_data['position']

        for brick in column_data['brick_data']:
            brightness = brick['brightness']

            r, g, b = color_filter
            color_r = brightness * r
            color_g = brightness * g
            color_b = brightness * b

            glColor4f(color_r, color_g, color_b, 1.0)

            glBegin(GL_TRIANGLES)
            for i in range(len(brick['vertices'])):
                x, y, z = brick['vertices'][i]
                x_world = x + column_position[0]
                y_world = y + column_position[1]
                z_world = z + column_position[2]

                vertex_disparity_pixels = self.calculate_disparity_for_point(x_world, y_world, z_world,
                                                                             base_disparity_degrees, force_onplane)

                if eye == 'left':
                    disparity_x = -vertex_disparity_pixels / 2 * 0.01
                else:
                    disparity_x = vertex_disparity_pixels / 2 * 0.01

                glVertex3f(x_world + disparity_x, y_world, z_world)
            glEnd()

    def render_checkerboard_floor_with_disparity(self, base_disparity_degrees, eye='left',
                                                 color_filter=(1.0, 1.0, 1.0)):
        r, g, b = color_filter

        glColor4f(0.9 * r, 0.9 * g, 0.9 * b, 1.0)

        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_white_vertices)):
            x, y, z = self.floor_white_vertices[i]

            vertex_disparity_pixels = self.calculate_disparity_for_point(x, y, z, base_disparity_degrees, False)

            if eye == 'left':
                disparity_x = -vertex_disparity_pixels / 2 * 0.01
            else:
                disparity_x = vertex_disparity_pixels / 2 * 0.01

            glVertex3f(x + disparity_x, y, z)
        glEnd()

    def render_anaglyph_frame(self, trial_data):
        disparity = trial_data['disparity_degrees']
        distance_along_vector = trial_data['distance_along_vector']
        onplane = trial_data.get('onplane', False)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glColorMask(GL_TRUE, GL_FALSE, GL_FALSE, GL_TRUE)
        glClear(GL_DEPTH_BUFFER_BIT)

        self.setup_anaglyph_camera('left', 0)

        glDisable(GL_BLEND)
        self.render_column_with_proper_disparity(distance_along_vector, disparity, 'left',
                                                 color_filter=(1.0, 0.0, 0.0), force_onplane=onplane)

        glEnable(GL_BLEND)
        self.render_checkerboard_floor_with_disparity(disparity, 'left', color_filter=(1.0, 0.0, 0.0))

        glColorMask(GL_FALSE, GL_TRUE, GL_TRUE, GL_TRUE)
        glClear(GL_DEPTH_BUFFER_BIT)

        self.setup_anaglyph_camera('right', 0)

        glDisable(GL_BLEND)
        self.render_column_with_proper_disparity(distance_along_vector, disparity, 'right',
                                                 color_filter=(0.0, 1.0, 1.0), force_onplane=onplane)

        glEnable(GL_BLEND)
        self.render_checkerboard_floor_with_disparity(disparity, 'right', color_filter=(0.0, 1.0, 1.0))

        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def show_instructions(self):
        instruction_text = visual.TextStim(
            self.win,
            text="""ANAGLYPH DEPTH PERCEPTION EXPERIMENT
(Above/Below/On Checkerboard Plane)

Put on the red-cyan 3D glasses now.

You will see a white column positioned at different locations.
The ground is a checkerboard pattern with white and transparent squares.

IMPORTANT: The column is always CENTERED within a transparent square
and never touches the white squares. This ensures you judge depth 
purely from stereoscopic cues, not occlusion!

Your task is to judge whether the column appears:

ABOVE the checkerboard plane (press 'W')
BELOW the checkerboard plane (press 'S')
ON the checkerboard plane (press 'SPACE')

The column size adjusts for distance to maintain constant visual angle.
Take your time and be as accurate as possible.
The column will disappear after a few seconds.

Press SPACE to begin the experiment.
Press ESC to quit at any time.""",
            height=26,
            wrapWidth=800,
            color='white',
            pos=(0, 0)
        )

        instruction_text.draw()
        self.win.flip()
        event.waitKeys(keyList=['space', 'escape'])

    def show_trial_feedback(self, trial_num, total_trials):
        feedback_text = visual.TextStim(
            self.win,
            text=f"Trial {trial_num} of {total_trials}\n\nPress SPACE for next trial",
            height=40,
            color='white',
            pos=(0, 0)
        )

        feedback_text.draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])

    def collect_response(self, trial_data, start_time):
        response_text = visual.TextStim(
            self.win,
            text="Column appears:\n\n(W) Above the checkerboard plane\n(S) Below the checkerboard plane\n(SPACE) On the checkerboard plane",
            height=30,
            color='white',
            pos=(0, 0)
        )

        response_text.draw()
        self.win.flip()

        keys = event.waitKeys(keyList=['w', 's', 'space', 'escape'])
        response_time = core.getTime() - start_time

        if 'escape' in keys:
            return None

        response = keys[0].upper() if keys[0] != 'space' else 'SPACE'

        if trial_data.get('onplane', False):
            correct_answer = 'SPACE'
        else:
            column_position = self.column_geometries[trial_data['distance_along_vector']]['position']
            correct_answer = 'W' if column_position[1] > 0 else 'S'

        is_correct = response == correct_answer

        trial_record = {
            'trial_id': trial_data['trial_id'],
            'disparity_degrees': trial_data['disparity_degrees'],
            'distance_along_vector': trial_data['distance_along_vector'],
            'onplane': trial_data.get('onplane', False),
            'column_y_position': self.column_geometries[trial_data['distance_along_vector']]['position'][1],
            'response': response,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }

        self.experiment_data.append(trial_record)
        return response

    def save_results(self, participant_id):
        if not self.experiment_data:
            return

        filename = f"anaglyph_results_{participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame(self.experiment_data)
        df.to_csv(filename, index=False)

        correct_responses = sum(1 for trial in self.experiment_data if trial['is_correct'])
        total_responses = len(self.experiment_data)
        accuracy = correct_responses / total_responses if total_responses > 0 else 0

        onplane_trials = [trial for trial in self.experiment_data if trial['onplane']]
        offplane_trials = [trial for trial in self.experiment_data if not trial['onplane']]

        onplane_correct = sum(1 for trial in onplane_trials if trial['is_correct'])
        offplane_correct = sum(1 for trial in offplane_trials if trial['is_correct'])

        print(f"Results saved to {filename}")
        print(f"Overall Accuracy: {correct_responses}/{total_responses} ({accuracy:.1%})")
        if onplane_trials:
            print(
                f"On-plane Accuracy: {onplane_correct}/{len(onplane_trials)} ({onplane_correct / len(onplane_trials):.1%})")
        if offplane_trials:
            print(
                f"Off-plane Accuracy: {offplane_correct}/{len(offplane_trials)} ({offplane_correct / len(offplane_trials):.1%})")

    def run_experiment(self):
        dlg = gui.Dlg(title="Participant Information")
        dlg.addField('Participant ID:')
        dlg.addField('Age:')
        dlg.addField('Gender:')

        participant_info = dlg.show()
        if dlg.OK == False:
            return

        participant_id = participant_info[0]

        self.load_experiment_conditions('experiment_conditions.csv')
        self.show_instructions()

        for trial_num, trial_data in enumerate(self.trials, 1):
            if trial_num > 1:
                self.show_trial_feedback(trial_num, len(self.trials))

            start_time = core.getTime()
            stimulus_duration = trial_data.get('presentation_time', 3.0)

            while core.getTime() - start_time < stimulus_duration:
                self.render_anaglyph_frame(trial_data)
                self.win.flip()

                keys = event.getKeys(['escape'])
                if 'escape' in keys:
                    self.save_results(participant_id)
                    return

            response = self.collect_response(trial_data, start_time)
            if response is None:
                break

        self.save_results(participant_id)

        completion_text = visual.TextStim(
            self.win,
            text="Experiment complete!\n\nThank you for participating.\n\nPress any key to exit.",
            height=40,
            color='white',
            pos=(0, 0)
        )

        completion_text.draw()
        self.win.flip()
        event.waitKeys()


def run_anaglyph_experiment():
    win = None
    try:
        win = visual.Window(
            size=[1024, 768],
            units='pix',
            fullscr=False,
            allowGUI=True,
            winType='pyglet',
            color=[0, 0, 0],
            colorSpace='rgb',
            waitBlanking=True
        )
        win.recordFrameIntervals = False

        print("Initializing anaglyph experiment with checkerboard pattern and on-plane conditions...")
        experiment = AnaglyphColumnExperiment(win)
        experiment.run_experiment()

    except Exception as e:
        print(f"Error running experiment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if win is not None:
            win.close()
        core.quit()


if __name__ == "__main__":
    run_anaglyph_experiment()
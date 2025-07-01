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


class SimpleColumnRenderer:
    def __init__(self, win):
        self.win = win
        self.setup_opengl()

        # cam params
        self.camera_pos = [0, 3.0, 0]
        self.look_at_point = [0, 3.0, -15]  # down/forward
        self.viewing_vector = self.calculate_viewing_vector()

        # anaglyph params
        self.eye_separation = 0.065  # 6.5cm typical interpupillary distance
        self.current_eye = 'left'  # start with left eye
        self.frame_counter = 0
        self.eye_swap_rate = 1  # swap every N frames (1 = every frame for fastest)

        # eye positions
        self.left_eye_pos = self.calculate_eye_position('left')
        self.right_eye_pos = self.calculate_eye_position('right')

        # for scale calc
        self.reference_distance = 15.0  # along viewing vect
        self.reference_visual_angle_degrees = 1.5

        # checkboard size based on column
        self.checkerboard_square_size = self.calculate_required_square_size()

        # gen checkerboard
        self.generate_checkerboard_floor()

        # pre gen the columns
        self.column_geometries = {}
        self.generate_all_column_geometries()

        # generate filter planes for each eye
        self.generate_filter_planes()

        # exp parmas
        self.trials = []
        self.current_trial = 0
        self.responses = []
        self.experiment_data = []

    def calculate_eye_position(self, eye):
        """Calculate left or right eye position"""
        # get right vector (perpendicular to viewing vector)
        up_vector = [0, 1, 0]
        vx, vy, vz = self.viewing_vector

        # cross product of viewing vector and up vector gives right vector
        right_x = vy * up_vector[2] - vz * up_vector[1]
        right_y = vz * up_vector[0] - vx * up_vector[2]
        right_z = vx * up_vector[1] - vy * up_vector[0]

        # normalize right vector
        right_length = math.sqrt(right_x ** 2 + right_y ** 2 + right_z ** 2)
        right_x /= right_length
        right_y /= right_length
        right_z /= right_length

        # offset camera by half eye separation
        offset = self.eye_separation / 2.0
        if eye == 'left':
            offset = -offset

        eye_x = self.camera_pos[0] + offset * right_x
        eye_y = self.camera_pos[1] + offset * right_y
        eye_z = self.camera_pos[2] + offset * right_z

        return [eye_x, eye_y, eye_z]

    def generate_filter_planes(self):
        # position filter planes close enough to eye but far enough to cover full FOV
        filter_distance = 0.5  # distance from eye to filter plane

        # calculate filter size needed to cover full field of view
        # using 45 degree FOV (from gluPerspective call) and aspect ratio
        aspect_ratio = self.win.size[0] / self.win.size[1]
        fov_radians = math.radians(45.0)

        # calculate size needed to cover full vertical FOV at filter distance
        filter_height = 2.0 * filter_distance * math.tan(fov_radians / 2.0)
        filter_width = filter_height * aspect_ratio

        # add extra margin to ensure full coverage
        filter_height *= 1.5  # 50% extra coverage
        filter_width *= 1.5

        # left eye filter (red) - positioned in front of left eye
        left_filter_pos = [
            self.left_eye_pos[0] + filter_distance * self.viewing_vector[0],
            self.left_eye_pos[1] + filter_distance * self.viewing_vector[1],
            self.left_eye_pos[2] + filter_distance * self.viewing_vector[2]
        ]

        # right eye filter (cyan) - positioned in front of right eye
        right_filter_pos = [
            self.right_eye_pos[0] + filter_distance * self.viewing_vector[0],
            self.right_eye_pos[1] + filter_distance * self.viewing_vector[1],
            self.right_eye_pos[2] + filter_distance * self.viewing_vector[2]
        ]

        # create filter plane vertices (sized to cover full FOV)
        self.left_filter_vertices = self.create_filter_quad(left_filter_pos, filter_width, filter_height)
        self.right_filter_vertices = self.create_filter_quad(right_filter_pos, filter_width, filter_height)

    def create_filter_quad(self, center_pos, width, height):
        # get right and up vectors relative to viewing direction
        up_vector = [0, 1, 0]
        vx, vy, vz = self.viewing_vector

        # right vector (perpendicular to viewing vector)
        right_x = vy * up_vector[2] - vz * up_vector[1]
        right_y = vz * up_vector[0] - vx * up_vector[2]
        right_z = vx * up_vector[1] - vy * up_vector[0]

        # normalize right vector
        right_length = math.sqrt(right_x ** 2 + right_y ** 2 + right_z ** 2)
        right_x /= right_length
        right_y /= right_length
        right_z /= right_length

        # up vector perpendicular to both viewing and right vectors
        up_x = right_y * vz - right_z * vy
        up_y = right_z * vx - right_x * vz
        up_z = right_x * vy - right_y * vx

        half_width = width / 2.0
        half_height = height / 2.0
        cx, cy, cz = center_pos

        # create quad vertices using both right and up vectors for proper orientation
        vertices = [
            # triangle 1
            (cx - half_width * right_x - half_height * up_x,
             cy - half_width * right_y - half_height * up_y,
             cz - half_width * right_z - half_height * up_z),
            (cx + half_width * right_x - half_height * up_x,
             cy + half_width * right_y - half_height * up_y,
             cz + half_width * right_z - half_height * up_z),
            (cx - half_width * right_x + half_height * up_x,
             cy - half_width * right_y + half_height * up_y,
             cz - half_width * right_z + half_height * up_z),
            # triangle 2
            (cx + half_width * right_x - half_height * up_x,
             cy + half_width * right_y - half_height * up_y,
             cz + half_width * right_z - half_height * up_z),
            (cx + half_width * right_x + half_height * up_x,
             cy + half_width * right_y + half_height * up_y,
             cz + half_width * right_z + half_height * up_z),
            (cx - half_width * right_x + half_height * up_x,
             cy - half_width * right_y + half_height * up_y,
             cz - half_width * right_z + half_height * up_z)
        ]

        return vertices

    def render_filter_plane(self, vertices, color):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # disable depth testing for filter to ensure it renders on top
        glDisable(GL_DEPTH_TEST)

        # set filter color with transparency for anaglyph effect
        glColor4f(color[0], color[1], color[2], 0.4)  # semi-transparent for proper anaglyph

        glBegin(GL_TRIANGLES)
        for vertex in vertices:
            glVertex3f(vertex[0], vertex[1], vertex[2])
        glEnd()

        # re-enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

    def calculate_viewing_vector(self):
        #vx = self.look_at_point[0] - self.camera_pos[0]
        #vy = self.look_at_point[1] - self.camera_pos[1]
        #vz = self.look_at_point[2] - self.camera_pos[2]
        vx=0
        vy=-3
        vz=-15

        # Normalize vector
        length = math.sqrt(vx * vx + vy * vy + vz * vz)
        return [vx / length, vy / length, vz / length]

    def calculate_position_along_vector(self, distance):
        x = self.camera_pos[0] + distance * self.viewing_vector[0]
        y = self.camera_pos[1] + distance * self.viewing_vector[1]
        z = self.camera_pos[2] + distance * self.viewing_vector[2]
        return [x, y, z]

    def calculate_required_square_size(self):
        max_column_width = 0

        # max column width
        for distance in good_distances_to_test:
            size_factor = distance / self.reference_distance
            column_width = 0.8 * size_factor  # base_brick_width * size_factor
            column_depth = 0.08 * size_factor  # base_brick_depth * size_factor

            # check for max offset as well
            max_offset = 0.04 * size_factor
            total_width = column_width + 2 * max_offset
            total_depth = column_depth + 2 * max_offset

            max_dimension = max(total_width, total_depth)
            max_column_width = max(max_column_width, max_dimension)

        # MUST HAVE COLUMN CENTERED in square
        required_size = max_column_width * 3.0  # 200% safety margin for full centering
        nice_size = math.ceil(required_size * 2) / 2  # round to 0.5

        return nice_size

    def generate_checkerboard_floor(self):
        floor_size = 60.0  # large floor
        square_size = self.checkerboard_square_size

        # get # of squares
        num_squares = int(floor_size / square_size) + 4  # extra coverage

        self.floor_white_vertices = []
        self.floor_white_normals = []

        # verif column positions for debug
        column_positions = []
        for distance in good_distances_to_test:
            pos = self.calculate_position_along_vector(distance)
            column_positions.append((pos[0], pos[2]))  # x, z coordinates

        # start ref point
        reference_x = 0.0
        reference_z = column_positions[0][1]

        # align grid with center of colmn
        start_x = reference_x - (num_squares * square_size) / 2
        start_z = reference_z - (num_squares * square_size) / 2

        # adjust pos
        grid_offset_x = (reference_x - start_x) % square_size - square_size / 2
        grid_offset_z = (reference_z - start_z) % square_size - square_size / 2
        start_x += grid_offset_x
        start_z += grid_offset_z

        # see which contains the column
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

                # remove all white square
                is_in_column_corridor = (grid_i == column_x_grid_index)

                if is_in_column_corridor:
                    continue  # Skip the square so its transparent

                # normal checkerboard
                is_white = (grid_i + grid_j) % 2 == 1

                # white square vrtx list
                if is_white:
                    # 2 triangles/square
                    triangle1_vertices = [(x1, 0.0, z1), (x2, 0.0, z1), (x1, 0.0, z2)]
                    triangle1_normals = [(0, 1, 0)] * 3

                    triangle2_vertices = [(x2, 0.0, z1), (x2, 0.0, z2), (x1, 0.0, z2)]
                    triangle2_normals = [(0, 1, 0)] * 3

                    self.floor_white_vertices.extend(triangle1_vertices)
                    self.floor_white_vertices.extend(triangle2_vertices)
                    self.floor_white_normals.extend(triangle1_normals)
                    self.floor_white_normals.extend(triangle2_normals)

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)  # no lighting
        glDisable(GL_LIGHT0)
        glShadeModel(GL_FLAT)  # flat shading
        glClearColor(0.0, 0.0, 0.0, 1.0)  # black background

    def calculate_size_for_distance(self, distance):
        # size factor/distance so always about same size
        size_factor = distance / self.reference_distance
        return size_factor

    def generate_all_column_geometries(self):
        # pre gen geoemetries
        distances = good_distances_to_test

        for distance in distances:
            self.column_geometries[distance] = self.generate_column_geometry_for_distance(distance)

    def generate_column_geometry_for_distance(self, distance_along_vector):
        column_data = {}
        column_data['vertices'] = []
        column_data['normals'] = []
        column_data['brick_data'] = []
        column_data['position'] = self.calculate_position_along_vector(distance_along_vector)

        # scaling factor on distance
        size_factor = self.calculate_size_for_distance(distance_along_vector)

        # base distance
        base_total_height = 4.0
        base_brick_width = 0.8
        base_brick_depth = 0.08

        # Scale
        total_height = base_total_height * size_factor
        brick_width = base_brick_width * size_factor
        brick_depth = base_brick_depth * size_factor

        num_bricks = 80
        max_offset = 0.04 * size_factor  # scale offset as well
        brick_height = total_height / num_bricks
        missing_brick_probability = 0.1

        pos = column_data['position']

        for brick_i in range(num_bricks):
            y_top = -brick_i * brick_height
            y_bottom = -(brick_i + 1) * brick_height

            if random.random() < missing_brick_probability:
                continue

            x_offset = random.uniform(-max_offset, max_offset)
            z_offset = random.uniform(-max_offset, max_offset)

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
                'normals': brick_normals
            })

        return column_data

    def add_brick_faces(self, x1, x2, y_top, y_bottom, z1, z2, vertices, normals):
        # Front face
        vertices.extend([
            (x1, y_top, z1), (x2, y_top, z1), (x2, y_bottom, z1),
            (x1, y_top, z1), (x2, y_bottom, z1), (x1, y_bottom, z1)
        ])
        normals.extend([(0, 0, 1)] * 6)

        # Back face
        vertices.extend([
            (x2, y_top, z2), (x1, y_top, z2), (x1, y_bottom, z2),
            (x2, y_top, z2), (x1, y_bottom, z2), (x2, y_bottom, z2)
        ])
        normals.extend([(0, 0, -1)] * 6)

        # Left face
        vertices.extend([
            (x1, y_top, z2), (x1, y_top, z1), (x1, y_bottom, z1),
            (x1, y_top, z2), (x1, y_bottom, z1), (x1, y_bottom, z2)
        ])
        normals.extend([(-1, 0, 0)] * 6)

        # Right face
        vertices.extend([
            (x2, y_top, z1), (x2, y_top, z2), (x2, y_bottom, z2),
            (x2, y_top, z1), (x2, y_bottom, z2), (x2, y_bottom, z1)
        ])
        normals.extend([(1, 0, 0)] * 6)

        # Top face
        vertices.extend([
            (x1, y_top, z1), (x1, y_top, z2), (x2, y_top, z2),
            (x1, y_top, z1), (x2, y_top, z2), (x2, y_top, z1)
        ])
        normals.extend([(0, 1, 0)] * 6)

        # Bottom face
        vertices.extend([
            (x1, y_bottom, z2), (x1, y_bottom, z1), (x2, y_bottom, z1),
            (x1, y_bottom, z2), (x2, y_bottom, z1), (x2, y_bottom, z2)
        ])
        normals.extend([(0, -1, 0)] * 6)

    def setup_camera(self, eye_position):
        # cam setup for specific eye position
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # cam from eye position with downward angle
        gluLookAt(
            eye_position[0], eye_position[1], eye_position[2],  # Eye position
            self.look_at_point[0]+eye_position[0], self.look_at_point[1], self.look_at_point[2],  # Look at point
            0.0, 1.0, 0.0  # Up vector
        )

    def render_column(self, distance_along_vector):
        if distance_along_vector not in self.column_geometries:
            return

        column_data = self.column_geometries[distance_along_vector]
        column_position = column_data['position']

        # white color
        glColor4f(1.0, 1.0, 1.0, 1.0)

        for brick in column_data['brick_data']:
            glBegin(GL_TRIANGLES)
            for i in range(len(brick['vertices'])):
                x, y, z = brick['vertices'][i]
                # position along vector
                x_world = x + column_position[0]
                y_world = y + column_position[1]
                z_world = z + column_position[2]

                glVertex3f(x_world, y_world, z_world)
            glEnd()

    def render_checkerboard_floor(self):
        # white color for floor
        glColor4f(0.9, 0.9, 0.9, 1.0)

        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_white_vertices)):
            x, y, z = self.floor_white_vertices[i]
            glVertex3f(x, y, z)
        glEnd()

    def render_frame(self):
        # determine which eye to render and swap if needed
        self.frame_counter += 1
        if self.frame_counter % self.eye_swap_rate == 0:
            self.current_eye = 'right' if self.current_eye == 'left' else 'left'

        # get current eye position
        current_eye_pos = self.left_eye_pos if self.current_eye == 'left' else self.right_eye_pos

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        self.setup_camera(current_eye_pos)

        # render checkerboard floor
        self.render_checkerboard_floor()

        # render all columns
        for distance in good_distances_to_test:
            self.render_column(distance)

        # render the appropriate color filter for current eye
        if self.current_eye == 'left':
            # red filter for left eye
            self.render_filter_plane(self.left_filter_vertices, (1.0, 0.0, 0.0))
        else:
            # cyan filter for right eye
            self.render_filter_plane(self.right_filter_vertices, (0.0, 1.0, 1.0))

    def load_experiment_conditions(self, csv_filename):
        try:
            df = pd.read_csv(csv_filename)
            self.trials = df.to_dict('records')
            random.shuffle(self.trials)  # randomize  order
            print(f"Loaded {len(self.trials)} trials from {csv_filename}")
        except FileNotFoundError:
            print(f"CSV file {csv_filename} not found. Creating default conditions...")
            self.create_default_conditions()

    def create_default_conditions(self):
        disparities = good_disparities  # degrees
        distances = good_distances_to_test  # Distances along viewing vector
        onplane_conditions = [True, False]  # Add onplane condition

        self.trials = []
        for disparity in disparities:
            for distance in distances:
                for onplane in onplane_conditions:
                    for repeat in range(2):  # 2 repetitions per condition
                        self.trials.append({
                            'disparity_degrees': disparity,
                            'distance_along_vector': distance,
                            'onplane': onplane,
                            'trial_id': len(self.trials) + 1,
                            'presentation_time': 3.0
                        })

        random.shuffle(self.trials)

        # save to csv
        df = pd.DataFrame(self.trials)
        df.to_csv('experiment_conditions.csv', index=False)
        print("Created default experiment_conditions.csv with onplane conditions")

    def show_instructions(self):
        # Instructions
        instruction_text = visual.TextStim(
            self.win,
            text="""ANAGLYPH 3D DEPTH PERCEPTION EXPERIMENT
(Above/Below/On Checkerboard Plane)

*** WEAR RED-CYAN 3D GLASSES FOR PROPER EFFECT ***

You will see a white column positioned at different locations in 3D.
The ground is a checkerboard pattern with white and transparent squares.

IMPORTANT: The column is always CENTERED within a transparent square
and never touches the white squares. This ensures you judge depth 
purely from visual cues, not occlusion!

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
        # get response
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

        # get correct answer based on trial condition
        if trial_data.get('onplane', False):
            correct_answer = 'SPACE'  # Column should appear on the plane
        else:
            # Original logic for above/below
            column_position = self.column_geometries[trial_data['distance_along_vector']]['position']
            correct_answer = 'W' if column_position[1] > 0 else 'S'

        is_correct = response == correct_answer

        # record data
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
        # Save csv
        if not self.experiment_data:
            return

        filename = f"anaglyph_results_{participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame(self.experiment_data)
        df.to_csv(filename, index=False)

        # get accuracy
        correct_responses = sum(1 for trial in self.experiment_data if trial['is_correct'])
        total_responses = len(self.experiment_data)
        accuracy = correct_responses / total_responses if total_responses > 0 else 0

        # Calculate accuracy by condition
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

    def render_trial_frame(self, trial_data):
        distance_along_vector = trial_data['distance_along_vector']

        # determine which eye to render and swap if needed
        self.frame_counter += 1
        if self.frame_counter % self.eye_swap_rate == 0:
            self.current_eye = 'right' if self.current_eye == 'left' else 'left'

        # get current eye position
        current_eye_pos = self.left_eye_pos if self.current_eye == 'left' else self.right_eye_pos

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        self.setup_camera(current_eye_pos)

        # render checkerboard floor
        self.render_checkerboard_floor()

        # render specific column for this trial
        self.render_column(distance_along_vector)

        # render the appropriate color filter for current eye
        if self.current_eye == 'left':
            # red filter for left eye
            self.render_filter_plane(self.left_filter_vertices, (1.0, 0.0, 0.0))
        else:
            # cyan filter for right eye
            self.render_filter_plane(self.right_filter_vertices, (0.0, 1.0, 1.0))

    def run_experiment(self):
        # full exp
        # get id
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

            # show image
            start_time = core.getTime()
            stimulus_duration = trial_data.get('presentation_time', 3.0)

            while core.getTime() - start_time < stimulus_duration:
                self.render_trial_frame(trial_data)
                self.win.flip()

                # Check for escape
                keys = event.getKeys(['escape'])
                if 'escape' in keys:
                    self.save_results(participant_id)
                    return

            # Collect
            response = self.collect_response(trial_data, start_time)
            if response is None:  # Escape pressed
                break

        # save
        self.save_results(participant_id)

        # end msg
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

    def run_demo(self):
        print("Rendering anaglyph 3D structures...")
        print("*** WEAR RED-CYAN 3D GLASSES FOR PROPER EFFECT ***")
        print("Press ESC to quit, SPACE to continue")

        while True:
            self.render_frame()
            self.win.flip()

            # Check for key presses
            keys = event.getKeys(['escape', 'space'])
            if 'escape' in keys:
                break


def run_depth_perception_study():
    # demo or full experiment
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

        print("Initializing anaglyph 3D depth perception study...")
        renderer = SimpleColumnRenderer(win)

        # choose mode
        mode_dlg = gui.Dlg(title="Select Mode")
        mode_dlg.addField('Mode:', choices=['Demo', 'Experiment'])
        mode_info = mode_dlg.show()

        if mode_dlg.OK == False:
            return

        if mode_info[0] == 'Experiment':
            renderer.run_experiment()
        else:
            renderer.run_demo()

    except Exception as e:
        print(f"Error running study: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if win is not None:
            win.close()
        core.quit()


if __name__ == "__main__":
    run_depth_perception_study()
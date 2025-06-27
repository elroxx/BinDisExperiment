from psychopy import visual, core, event, data, gui
from pyglet.gl import *
import math
import random
import csv
import os
from datetime import datetime
import pandas as pd

# WITH THIS SCALING!
# DONT PLACE ANYTHING BETWEEN 6.485 and 15.297 (sqrt234) ALONG VECTOR. distance along vector at 15 is below the plane, and at 6 its above the plane.
good_distances_to_test = [3, 25]
#good_disparities = [-0.6, -0.3, -0.1, 0.0, 0.1, 0.3, 0.6]
good_disparities = [0.3]


class AnaglyphColumnExperiment:
    def __init__(self, win):
        self.win = win
        self.setup_opengl()
        self.generate_floor_geometry()

        # cam params
        self.camera_pos = [0, 3.0, 0]
        self.look_at_point = [0, 0, -15]  # down/forward
        self.viewing_vector = self.calculate_viewing_vector()

        # Reference distance for scaling calculations
        self.reference_distance = 15.0  # Reference distance along viewing vector
        self.reference_visual_angle_degrees = 1.5

        # pre gen the columns
        self.column_geometries = {}
        self.generate_all_column_geometries()

        # exp parmas
        self.trials = []
        self.current_trial = 0
        self.responses = []
        self.experiment_data = []

        # Anaglyph params
        self.eye_separation = 0.1 #0.065  # human ipd meters
        self.screen_distance = 0.2  # distance to screen meters
        self.convergence_distance = 15.0  # Distance where disparity = 0 so verging on the plane

    def calculate_viewing_vector(self):
        vx = self.look_at_point[0] - self.camera_pos[0]
        vy = self.look_at_point[1] - self.camera_pos[1]
        vz = self.look_at_point[2] - self.camera_pos[2]

        # Normalize vector
        length = math.sqrt(vx * vx + vy * vy + vz * vz)
        return [vx / length, vy / length, vz / length]

    def calculate_position_along_vector(self, distance):
        x = self.camera_pos[0] + distance * self.viewing_vector[0]
        y = self.camera_pos[1] + distance * self.viewing_vector[1]
        z = self.camera_pos[2] + distance * self.viewing_vector[2]
        return [x, y, z]

    def calculate_disparity_for_point(self, world_x, world_y, world_z, base_disparity_degrees):
        """Calculate proper disparity for a 3D point based on its distance from camera"""
        # Calculate actual distance from camera to this point
        dx = world_x - self.camera_pos[0]
        dy = world_y - self.camera_pos[1]
        dz = world_z - self.camera_pos[2]
        actual_distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        # Calculate disparity based on actual distance relative to convergence distance
        # Closer objects have positive disparity, farther objects have negative disparity
        distance_factor = (self.convergence_distance - actual_distance) / self.convergence_distance

        # Apply base disparity plus distance-based disparity
        total_disparity_degrees = base_disparity_degrees + distance_factor * 0.5  # 0.5 degrees max distance effect

        # Convert to pixel disparity
        disparity_pixels = total_disparity_degrees * (self.win.size[0] / 60.0)
        return disparity_pixels

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)  # no lighting
        glDisable(GL_LIGHT0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glShadeModel(GL_FLAT)  # flat shading
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def calculate_size_for_distance(self, distance):
        # size factor/distance so always about same size
        size_factor = distance / self.reference_distance
        return size_factor

    def generate_floor_geometry(self):
        floor_size = 40.0
        divisions = 50
        step = floor_size / divisions

        self.floor_vertices = []
        self.floor_normals = []

        for i in range(divisions):
            for j in range(divisions):
                x1 = -floor_size / 2 + i * step
                x2 = x1 + step
                z1 = -floor_size / 2 + j * step
                z2 = z1 + step

                triangle1_vertices = [(x1, 0.0, z1), (x2, 0.0, z1), (x1, 0.0, z2)]
                triangle1_normals = [(0, 1, 0)] * 3

                triangle2_vertices = [(x2, 0.0, z1), (x2, 0.0, z2), (x1, 0.0, z2)]
                triangle2_normals = [(0, 1, 0)] * 3

                self.floor_vertices.extend(triangle1_vertices)
                self.floor_vertices.extend(triangle2_vertices)
                self.floor_normals.extend(triangle1_normals)
                self.floor_normals.extend(triangle2_normals)

    def generate_all_column_geometries(self):
        # pre gen geoemetries
        distances = good_distances_to_test  # Along viewing vector

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
        base_total_height = 4.0  # Much shorter column
        base_brick_width = 0.8
        base_brick_depth = 0.08

        # Scale
        total_height = base_total_height * size_factor
        brick_width = base_brick_width * size_factor
        brick_depth = base_brick_depth * size_factor

        num_bricks = 80  # less bricks
        max_offset = 0.04 * size_factor  # scale offset as well
        brick_height = total_height / num_bricks
        missing_brick_probability = 0.1

        # uniform brightness
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

            # small random variation like my prev column
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
        disparities = good_disparities  # degress
        distances = good_distances_to_test  # Distances along viewing vector

        self.trials = []
        for disparity in disparities:
            for distance in distances:
                for repeat in range(2):  # 2 repetitions per condition
                    self.trials.append({
                        'disparity_degrees': disparity,
                        'distance_along_vector': distance,
                        'trial_id': len(self.trials) + 1,
                        'presentation_time': 3.0
                    })

        random.shuffle(self.trials)

        # save to csv
        df = pd.DataFrame(self.trials)
        df.to_csv('experiment_conditions.csv', index=False)
        print("Created default experiment_conditions.csv")

    def setup_anaglyph_camera(self, eye='left', disparity_offset_x=0):
        # cam
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # eye offset for stereo anag
        if eye == 'left':
            eye_offset = -self.eye_separation / 2
        else:
            eye_offset = self.eye_separation / 2

        # cam above and slight downward angle
        gluLookAt(
            self.camera_pos[0] + eye_offset + disparity_offset_x,
            self.camera_pos[1],
            self.camera_pos[2],  # Eye position
            self.look_at_point[0] + disparity_offset_x,
            self.look_at_point[1],
            self.look_at_point[2],  # Look at point
            0.0, 1.0, 0.0  # Up vector
        )

    def render_column_with_proper_disparity(self, distance_along_vector, base_disparity_degrees, eye='left',
                                            color_filter=(1.0, 1.0, 1.0)):
        if distance_along_vector not in self.column_geometries:
            print(f"Warning: No geometry found for distance {distance_along_vector}")
            return

        column_data = self.column_geometries[distance_along_vector]
        column_position = column_data['position']

        for brick in column_data['brick_data']:
            brightness = brick['brightness']

            # no lighting
            r, g, b = color_filter
            color_r = brightness * r
            color_g = brightness * g
            color_b = brightness * b

            # color directly
            glColor4f(color_r, color_g, color_b, 1.0)

            glBegin(GL_TRIANGLES)
            for i in range(len(brick['vertices'])):
                x, y, z = brick['vertices'][i]
                # position computed along vector
                x_world = x + column_position[0]
                y_world = y + column_position[1]
                z_world = z + column_position[2]

                # Calculate proper disparity for this specific vertex
                vertex_disparity_pixels = self.calculate_disparity_for_point(x_world, y_world, z_world,
                                                                             base_disparity_degrees)

                # Apply eye-specific disparity offset
                if eye == 'left':
                    disparity_x = -vertex_disparity_pixels / 2 * 0.01  # Convert to world units
                else:
                    disparity_x = vertex_disparity_pixels / 2 * 0.01

                glVertex3f(x_world + disparity_x, y_world, z_world)
            glEnd()

    def render_floor(self, color_filter=(1.0, 1.0, 1.0)):
        r, g, b = color_filter

        # darker floor than column
        glColor4f(0.3 * r, 0.3 * g, 0.3 * b, 0.3)

        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_vertices)):
            x, y, z = self.floor_vertices[i]
            glVertex3f(x, y, z)
        glEnd()

    def render_anaglyph_frame(self, trial_data):
        disparity = trial_data['disparity_degrees']
        distance_along_vector = trial_data['distance_along_vector']

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        # render left eye
        glColorMask(GL_TRUE, GL_FALSE, GL_FALSE, GL_TRUE)  # Only red channel
        glClear(GL_DEPTH_BUFFER_BIT)

        self.setup_anaglyph_camera('left', 0)

        glDisable(GL_BLEND)
        self.render_column_with_proper_disparity(distance_along_vector, disparity, 'left', color_filter=(1.0, 0.0, 0.0))

        glEnable(GL_BLEND)
        self.render_floor(color_filter=(1.0, 0.0, 0.0))

        # render cyan
        glColorMask(GL_FALSE, GL_TRUE, GL_TRUE, GL_TRUE)  # Green and blue channels
        glClear(GL_DEPTH_BUFFER_BIT)

        self.setup_anaglyph_camera('right', 0)

        glDisable(GL_BLEND)
        self.render_column_with_proper_disparity(distance_along_vector, disparity, 'right',
                                                 color_filter=(0.0, 1.0, 1.0))

        glEnable(GL_BLEND)
        self.render_floor(color_filter=(0.0, 1.0, 1.0))

        # reset color mask
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def show_instructions(self):
        # Instructions
        instruction_text = visual.TextStim(
            self.win,
            text="""ANAGLYPH DEPTH PERCEPTION EXPERIMENT
(Above/Below Ground Plane - Enhanced Disparity)

Put on the red-cyan 3D glasses now.

You will see a white column positioned at different locations.
The camera is looking down at a slight angle.
Each part of the column now has proper stereoscopic disparity!

Your task is to judge whether the column appears:

ABOVE the ground plane/floor (press 'A')
BELOW the ground plane/floor (press 'B')

The column size adjusts for distance to maintain constant visual angle.
Take your time and be as accurate as possible.
The column will disappear after a few seconds.

Press SPACE to begin the experiment.
Press ESC to quit at any time.""",
            height=30,
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
            text="Column appears:\n\n(A) Above the ground plane\n(B) Below the ground plane",
            height=30,
            color='white',
            pos=(0, 0)
        )

        response_text.draw()
        self.win.flip()

        keys = event.waitKeys(keyList=['a', 'b', 'escape'])
        response_time = core.getTime() - start_time

        if 'escape' in keys:
            return None

        response = keys[0].upper()

        # get correct answer
        column_position = self.column_geometries[trial_data['distance_along_vector']]['position']
        correct_answer = 'A' if column_position[1] > 0 else 'B'
        is_correct = response == correct_answer

        # record data
        trial_record = {
            'trial_id': trial_data['trial_id'],
            'disparity_degrees': trial_data['disparity_degrees'],
            'distance_along_vector': trial_data['distance_along_vector'],
            'column_y_position': column_position[1],
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

        print(f"Results saved to {filename}")
        print(f"Accuracy: {correct_responses}/{total_responses} ({accuracy:.1%})")

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
                self.render_anaglyph_frame(trial_data)
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


def run_anaglyph_experiment():
    # Run anaglyph experiment
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

        print("Initializing anaglyph experiment with proper per-vertex disparity...")
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
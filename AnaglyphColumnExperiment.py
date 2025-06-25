from psychopy import visual, core, event, data, gui
from pyglet.gl import *
import math
import random
import csv
import os
from datetime import datetime
import pandas as pd


class AnaglyphColumnExperiment:
    def __init__(self, win):
        self.win = win
        self.setup_opengl()
        self.setup_lighting()
        self.generate_floor_geometry()
        self.generate_column_geometry()

        # Experiment parameters
        self.trials = []
        self.current_trial = 0
        self.responses = []
        self.experiment_data = []

        # Anaglyph param
        self.eye_separation = 0.065  # Average human IPD in meters
        self.screen_distance = 0.6  # Distance to screen in meters

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def setup_lighting(self):
        # Main light
        light0_pos = (GLfloat * 4)(0.0, 8.0, -5.0, 1.0)
        light0_ambient = (GLfloat * 4)(0.3, 0.3, 0.3, 1.0)
        light0_diffuse = (GLfloat * 4)(0.8, 0.8, 0.8, 1.0)
        light0_specular = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)

        glLightfv(GL_LIGHT0, GL_POSITION, light0_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light0_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light0_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light0_specular)

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

    def generate_column_geometry(self):
        self.column_vertices = []
        self.column_normals = []
        self.brick_data = []

        total_height = 15.0
        num_bricks = 300
        max_offset = 0.08
        brick_width = 1.0
        brick_depth = 0.08
        brick_height = total_height / num_bricks
        missing_brick_probability = 0.15

        for brick_i in range(num_bricks):
            y_top = -brick_i * brick_height
            y_bottom = -(brick_i + 1) * brick_height

            if random.random() < missing_brick_probability:
                continue

            x_offset = random.uniform(-max_offset, max_offset)
            z_offset = random.uniform(-max_offset, max_offset)

            # Position-based brightness for better depth cues
            position_factor = brick_i / (num_bricks - 1)
            base_brightness = 1.0 - (position_factor * 0.3)
            brightness = base_brightness + random.uniform(-0.1, 0.1)
            brightness = max(0.4, min(1.0, brightness))

            brick_x = x_offset
            brick_z = z_offset  # modified each trial

            x1 = brick_x - brick_width / 2
            x2 = brick_x + brick_width / 2
            z1 = brick_z - brick_depth / 2
            z2 = brick_z + brick_depth / 2

            brick_vertices = []
            brick_normals = []
            self.add_brick_faces(x1, x2, y_top, y_bottom, z1, z2, brick_vertices, brick_normals)

            self.brick_data.append({
                'vertices': brick_vertices,
                'normals': brick_normals,
                'brightness': brightness,
                'base_z': brick_z
            })

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
            random.shuffle(self.trials)  # Randomize trial order
            print(f"Loaded {len(self.trials)} trials from {csv_filename}")
        except FileNotFoundError:
            print(f"CSV file {csv_filename} not found. Creating default conditions...")
            self.create_default_conditions()

    def create_default_conditions(self):

        disparities = [-0.8, -0.4, -0.2, -0.1, 0.0, 0.1, 0.2, 0.4, 0.8]  # In degrees
        distances = [-15, -20, -25]  # Column distances

        self.trials = []
        for disparity in disparities:
            for distance in distances:
                for repeat in range(3):  # 3 repetitions per condition
                    self.trials.append({
                        'disparity_degrees': disparity,
                        'column_distance': distance,
                        'trial_id': len(self.trials) + 1,
                        'presentation_time': 2.0
                    })

        random.shuffle(self.trials)

        # default to csv
        df = pd.DataFrame(self.trials)
        df.to_csv('experiment_conditions.csv', index=False)
        print("Created default experiment_conditions.csv")

    def setup_anaglyph_camera(self, eye='left', disparity_pixels=0):
        #setup cam
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Calculate eye offset for stereoscopic effect
        if eye == 'left':
            eye_offset = -self.eye_separation / 2
        else:
            eye_offset = self.eye_separation / 2

        # horizontal offset
        disparity_offset = disparity_pixels * 0.01  #world units

        gluLookAt(eye_offset + disparity_offset, 1.5, 0.0,  # eye
                  disparity_offset, 1.0, -10.0,  # Look at point
                  0.0, 1.0, 0.0)  # Up vector

    def render_column(self, column_distance, color_filter=(1.0, 1.0, 1.0)):
        for brick in self.brick_data:
            brightness = brick['brightness']

            # color filter for analgyoh
            r, g, b = color_filter
            color_r = brightness * r
            color_g = brightness * g
            color_b = brightness * b

            mat_ambient = (GLfloat * 4)(0.3 * color_r, 0.3 * color_g, 0.3 * color_b, 1.0)
            mat_diffuse = (GLfloat * 4)(color_r, color_g, color_b, 1.0)
            mat_specular = (GLfloat * 4)(color_r, color_g, color_b, 1.0)
            mat_shininess = (GLfloat * 1)(32.0)

            glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)

            glColor4f(color_r, color_g, color_b, 1.0)

            glBegin(GL_TRIANGLES)
            for i in range(len(brick['vertices'])):
                nx, ny, nz = brick['normals'][i]
                x, y, z = brick['vertices'][i]
                # Adjust Z position based on column distance
                z_adjusted = z + column_distance
                glNormal3f(nx, ny, nz)
                glVertex3f(x, y, z_adjusted)
            glEnd()

    def render_floor(self, color_filter=(1.0, 1.0, 1.0)):
        r, g, b = color_filter
        mat_ambient = (GLfloat * 4)(0.1 * r, 0.1 * g, 0.1 * b, 0.3)
        mat_diffuse = (GLfloat * 4)(0.2 * r, 0.2 * g, 0.2 * b, 0.3)

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)

        glColor4f(0.3 * r, 0.3 * g, 0.3 * b, 0.3)

        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_vertices)):
            nx, ny, nz = self.floor_normals[i]
            x, y, z = self.floor_vertices[i]
            glNormal3f(nx, ny, nz)
            glVertex3f(x, y, z)
        glEnd()

    def render_anaglyph_frame(self, trial_data):
        disparity = trial_data['disparity_degrees']
        column_distance = trial_data['column_distance']

        disparity_pixels = disparity * (self.win.size[0] / 60.0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)

        self.setup_lighting()

        # Render left eye (red channel)
        glColorMask(GL_TRUE, GL_FALSE, GL_FALSE, GL_TRUE)  # Only red channel
        glClear(GL_DEPTH_BUFFER_BIT)

        self.setup_anaglyph_camera('left', -disparity_pixels / 2)

        glDisable(GL_BLEND)
        self.render_column(column_distance, color_filter=(1.0, 0.0, 0.0))

        glEnable(GL_BLEND)
        self.render_floor(color_filter=(1.0, 0.0, 0.0))

        # Render right eye (cyan channel)
        glColorMask(GL_FALSE, GL_TRUE, GL_TRUE, GL_TRUE)  # Green and blue channels
        glClear(GL_DEPTH_BUFFER_BIT)

        self.setup_anaglyph_camera('right', disparity_pixels / 2)

        glDisable(GL_BLEND)
        self.render_column(column_distance, color_filter=(0.0, 1.0, 1.0))

        glEnable(GL_BLEND)
        self.render_floor(color_filter=(0.0, 1.0, 1.0))

        # Reset color mask
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    def show_instructions(self):
    #instructions
        instruction_text = visual.TextStim(
            self.win,
            text="""ANAGLYPH DEPTH PERCEPTION EXPERIMENT

Put on the red-cyan 3D glasses now.

You will see a white column that appears at different depths.
Your task is to judge whether the column appears:

CLOSER than the floor (press 'C')
FARTHER than the floor (press 'F') 
AT THE SAME DEPTH as the floor (press 'S')

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
        #get reponse
        response_text = visual.TextStim(
            self.win,
            text="Column appears:\n\n(C) Closer than floor\n(F) Farther than floor\n(S) Same depth as floor",
            height=30,
            color='white',
            pos=(0, 0)
        )

        response_text.draw()
        self.win.flip()

        keys = event.waitKeys(keyList=['c', 'f', 's', 'escape'])
        response_time = core.getTime() - start_time

        if 'escape' in keys:
            return None

        response = keys[0].upper()

        # record data
        trial_record = {
            'trial_id': trial_data['trial_id'],
            'disparity_degrees': trial_data['disparity_degrees'],
            'column_distance': trial_data['column_distance'],
            'response': response,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }

        self.experiment_data.append(trial_record)
        return response

    def save_results(self, participant_id):
        #save csv
        if not self.experiment_data:
            return

        filename = f"anaglyph_results_{participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame(self.experiment_data)
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")

    def run_experiment(self):
        #run full experiemnt
        # Get participant ID
        dlg = gui.Dlg(title="Participant Information")
        dlg.addField('Participant ID:')
        dlg.addField('Age:')
        dlg.addField('Gender:')
        dlg.addField('Vision Correction:', choices=['None', 'Glasses', 'Contacts'])

        participant_info = dlg.show()
        if dlg.OK == False:
            return

        participant_id = participant_info[0]

        self.load_experiment_conditions('experiment_conditions.csv')
        self.show_instructions()

        for trial_num, trial_data in enumerate(self.trials, 1):
            if trial_num > 1:
                self.show_trial_feedback(trial_num, len(self.trials))

            # Present stimulus
            start_time = core.getTime()
            stimulus_duration = trial_data.get('presentation_time', 7.0)

            while core.getTime() - start_time < stimulus_duration:
                self.render_anaglyph_frame(trial_data)
                self.win.flip()

                # Check for escape
                keys = event.getKeys(['escape'])
                if 'escape' in keys:
                    self.save_results(participant_id)
                    return

            # Collect response
            response = self.collect_response(trial_data, start_time)
            if response is None:  # Escape pressed
                break

        # Save results
        self.save_results(participant_id)

        # Show completion message
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
    #aanglyph experiemnt
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

        print("Initializing anaglyph experiment...")
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
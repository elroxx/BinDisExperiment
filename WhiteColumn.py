from psychopy import visual, core, event
from pyglet.gl import *
import math
import random


class WhiteColumnScene:
    def __init__(self, win):
        self.win = win
        print("Setting up OpenGL...")
        self.setup_opengl()
        print("Setting up lighting...")
        self.setup_lighting()
        print("Setting up camera...")
        self.setup_camera()
        print("Generating floor geometry...")
        self.generate_floor_geometry()
        print("Generating column geometry...")
        self.generate_column_geometry()
        print("Scene initialization complete")
        self.angle_x = 0  # Rotation X
        self.angle_z = 0  # Rotation Z

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)  # light for the bottom which might be useless for this????. I probably should skip all the lights but
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 1.0)  # Black background

    def setup_lighting(self):
        # light above
        light0_pos = (GLfloat * 4)(0.0, 8.0, -5.0, 1.0)
        light0_ambient = (GLfloat * 4)(0.2, 0.2, 0.2, 1.0)
        light0_diffuse = (GLfloat * 4)(0.8, 0.8, 0.8, 1.0)
        light0_specular = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)

        glLightfv(GL_LIGHT0, GL_POSITION, light0_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light0_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light0_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light0_specular)

        # at bottom of location (ALSO NEED TO CHANGE THE -20 IF I CHANGE THE DISTANCE)
        light1_pos = (GLfloat * 4)(0.0, -12.0, -20.0, 1.0)  # Bottom of distant column
        light1_ambient = (GLfloat * 4)(0.3, 0.3, 0.3, 1.0)
        light1_diffuse = (GLfloat * 4)(1.2, 1.2, 1.2, 1.0)
        light1_specular = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)

        glLightfv(GL_LIGHT1, GL_POSITION, light1_pos)
        glLightfv(GL_LIGHT1, GL_AMBIENT, light1_ambient)
        glLightfv(GL_LIGHT1, GL_DIFFUSE, light1_diffuse)
        glLightfv(GL_LIGHT1, GL_SPECULAR, light1_specular)

    def setup_camera(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 1.5, 0.0,  # Eye position
                  0.0, 1.0, -10.0,  # Look at point
                  0.0, 1.0, 0.0)  # Up vector

    def generate_floor_geometry(self):
        # transparent floor (kinda useless with how I understand it? if its fully transparent its compeltely different)
        floor_size = 40.0
        divisions = 100
        step = floor_size / divisions

        self.floor_vertices = []
        self.floor_normals = []

        def jittered_normal():
            nx = random.gauss(0.0, 0.05)
            ny = 1.0
            nz = 0.0
            length = (nx ** 2 + ny ** 2) ** 0.5
            return (nx / length, ny / length, 0.0)

        for i in range(divisions):
            for j in range(divisions):
                x1 = -floor_size / 2 + i * step
                x2 = x1 + step
                z1 = -floor_size / 2 + j * step
                z2 = z1 + step

                # Triangle 1
                triangle1_vertices = [(x1, 0.0, z1), (x2, 0.0, z1), (x1, 0.0, z2)]
                triangle1_normals = [jittered_normal() for _ in range(3)]

                # Triangle 2
                triangle2_vertices = [(x2, 0.0, z1), (x2, 0.0, z2), (x1, 0.0, z2)]
                triangle2_normals = [jittered_normal() for _ in range(3)]

                self.floor_vertices.extend(triangle1_vertices)
                self.floor_vertices.extend(triangle2_vertices)
                self.floor_normals.extend(triangle1_normals)
                self.floor_normals.extend(triangle2_normals)

    def generate_column_geometry(self):
        #tower
        self.column_vertices = []
        self.column_normals = []
        self.brick_data = []  # brick for rendering

        # HYPER PARAEMETERS
        total_height = 15.0
        num_bricks = 500
        max_offset = 0.3  # random offset from center
        brick_width = 1.4  # (X dimension)
        brick_depth = 0.6  # (Z dimension)
        column_z_position = -20.0  # Distance from camera

        # color var
        min_brightness = 0.1  # darkest (0.0 = black, 1.0 = white)
        max_brightness = 1.0  # brightest
        brightness_variation = 1.0  #(0.0 = no variation, 1.0 = full range)

        # missing bricks + split row
        missing_brick_probability = 0.15
        split_row_probability = 0.25
        split_gap = 0.3  # gap between

        # brick height
        brick_height = total_height / num_bricks

        # gen per layer
        for brick_i in range(num_bricks):
            # get vertical pos
            y_top = -brick_i * brick_height
            y_bottom = -(brick_i + 1) * brick_height

            # if missing
            if random.random() < missing_brick_probability:
                continue  # skip

            # fi split
            if random.random() < split_row_probability:
                # gen 2 side by sides
                for split_i in range(2):
                    # left + right of center
                    base_x_offset = (-split_gap / 2 - brick_width / 4) if split_i == 0 else (
                                split_gap / 2 + brick_width / 4)

                    # individiual offset
                    x_offset = base_x_offset + random.uniform(-max_offset / 2, max_offset / 2)
                    z_offset = random.uniform(-max_offset, max_offset)

                    # random brightness
                    brightness = random.uniform(
                        max_brightness - brightness_variation,
                        max_brightness
                    )
                    brightness = max(min_brightness, brightness)

                    # smaller splits
                    split_brick_width = brick_width * 0.7
                    brick_x = x_offset
                    brick_z = column_z_position + z_offset
                    x1 = brick_x - split_brick_width / 2
                    x2 = brick_x + split_brick_width / 2
                    z1 = brick_z - brick_depth / 2
                    z2 = brick_z + brick_depth / 2

                    brick_vertices = []
                    brick_normals = []
                    self.add_brick_face_to_lists(x1, x2, y_top, y_bottom, z1, z2, brick_vertices, brick_normals)

                    self.brick_data.append({
                        'vertices': brick_vertices,
                        'normals': brick_normals,
                        'brightness': brightness
                    })
            else:
                #normal
                x_offset = random.uniform(-max_offset, max_offset)
                z_offset = random.uniform(-max_offset, max_offset)

                brightness = random.uniform(
                    max_brightness - brightness_variation,
                    max_brightness
                )
                brightness = max(min_brightness, brightness)

                brick_x = x_offset
                brick_z = column_z_position + z_offset

                x1 = brick_x - brick_width / 2
                x2 = brick_x + brick_width / 2
                z1 = brick_z - brick_depth / 2
                z2 = brick_z + brick_depth / 2

                brick_vertices = []
                brick_normals = []
                self.add_brick_face_to_lists(x1, x2, y_top, y_bottom, z1, z2, brick_vertices, brick_normals)

                self.brick_data.append({
                    'vertices': brick_vertices,
                    'normals': brick_normals,
                    'brightness': brightness
                })

    def add_brick_face_to_lists(self, x1, x2, y_top, y_bottom, z1, z2, vertices, normals):
        # Front
        vertices.extend([
            (x1, y_top, z1), (x2, y_top, z1), (x2, y_bottom, z1),
            (x1, y_top, z1), (x2, y_bottom, z1), (x1, y_bottom, z1)
        ])
        normals.extend([(0, 0, 1)] * 6)

        # Back
        vertices.extend([
            (x2, y_top, z2), (x1, y_top, z2), (x1, y_bottom, z2),
            (x2, y_top, z2), (x1, y_bottom, z2), (x2, y_bottom, z2)
        ])
        normals.extend([(0, 0, -1)] * 6)

        # Left
        vertices.extend([
            (x1, y_top, z2), (x1, y_top, z1), (x1, y_bottom, z1),
            (x1, y_top, z2), (x1, y_bottom, z1), (x1, y_bottom, z2)
        ])
        normals.extend([(-1, 0, 0)] * 6)

        # Right
        vertices.extend([
            (x2, y_top, z1), (x2, y_top, z2), (x2, y_bottom, z2),
            (x2, y_top, z1), (x2, y_bottom, z2), (x2, y_bottom, z1)
        ])
        normals.extend([(1, 0, 0)] * 6)

        # Top
        vertices.extend([
            (x1, y_top, z1), (x1, y_top, z2), (x2, y_top, z2),
            (x1, y_top, z1), (x2, y_top, z2), (x2, y_top, z1)
        ])
        normals.extend([(0, 1, 0)] * 6)

        # Bottom
        vertices.extend([
            (x1, y_bottom, z2), (x1, y_bottom, z1), (x2, y_bottom, z1),
            (x1, y_bottom, z2), (x2, y_bottom, z1), (x2, y_bottom, z2)
        ])
        normals.extend([(0, -1, 0)] * 6)

    def render_transparent_floor(self):
        mat_ambient = (GLfloat * 4)(0.1, 0.1, 0.1, 0.3)
        mat_diffuse = (GLfloat * 4)(0.2, 0.2, 0.2, 0.3)
        mat_specular = (GLfloat * 4)(0.5, 0.5, 0.5, 0.3)
        mat_shininess = (GLfloat * 1)(32.0)

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)

        glColor4f(0.5, 0.5, 0.5, 0.3)

        # as trinagles again
        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_vertices)):
            nx, ny, nz = self.floor_normals[i]
            x, y, z = self.floor_vertices[i]
            glNormal3f(nx, ny, nz)
            glVertex3f(x, y, z)
        glEnd()

    def render_white_column(self):
        for brick in self.brick_data:
            brightness = brick['brightness']

            # material based on brightness
            mat_ambient = (GLfloat * 4)(0.8 * brightness, 0.8 * brightness, 0.8 * brightness, 1.0)
            mat_diffuse = (GLfloat * 4)(brightness, brightness, brightness, 1.0)
            mat_specular = (GLfloat * 4)(brightness, brightness, brightness, 1.0)
            mat_shininess = (GLfloat * 1)(64.0 + 64.0 * brightness)  # brighter bricks == more shiny. prob will change without

            glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)

            glColor4f(brightness, brightness, brightness, 1.0)

            # render
            glBegin(GL_TRIANGLES)
            for i in range(len(brick['vertices'])):
                nx, ny, nz = brick['normals'][i]
                x, y, z = brick['vertices'][i]
                glNormal3f(nx, ny, nz)
                glVertex3f(x, y, z)
            glEnd()

    def render_frame(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # ope ngl
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_LIGHT1)
            glEnable(GL_COLOR_MATERIAL)
            glEnable(GL_BLEND)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glShadeModel(GL_SMOOTH)

            # Set up projection
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            aspect_ratio = self.win.size[0] / self.win.size[1]
            gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

            # Set up modelview (original camera positioning)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(0.0, 1.5, 0.0, 0.0, 1.0, -10.0, 0.0, 1.0, 0.0)

            self.setup_lighting()

            glPushMatrix()

            # rotation
            glRotatef(self.angle_x, 1.0, 0.0, 0.0)
            glRotatef(self.angle_z, 0.0, 0.0, 1.0)

            # opaque (should be at least)
            glDisable(GL_BLEND)
            self.render_white_column()

            # transparaent floor
            glEnable(GL_BLEND)
            self.render_transparent_floor()

            glPopMatrix()

        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            raise


def run_column_scene():
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
            waitBlanking=False
        )
        win.recordFrameIntervals = False
        win.autoDraw = False
        win.flip()

        print("Window created successfully")
        print("Initializing OpenGL scene...")

        scene = WhiteColumnScene(win)

        print("Press SPACE to start the scene...")
        print("Use arrow keys to rotate, ESC or Q to quit")
        event.waitKeys(keyList=['space'])

        clock = core.Clock()
        frame_count = 0

        while True:
            keys = event.getKeys()
            if 'escape' in keys or 'q' in keys:
                print("Exiting")
                break
            if 'left' in keys:
                scene.angle_z -= 2
                print(f"Rotation Z: {scene.angle_z}")
            if 'right' in keys:
                scene.angle_z += 2
                print(f"Rotation Z: {scene.angle_z}")
            if 'up' in keys:
                scene.angle_x -= 2
                print(f"Rotation X: {scene.angle_x}")
            if 'down' in keys:
                scene.angle_x += 2
                print(f"Rotation X: {scene.angle_x}")

            try:
                scene.render_frame()
                win.flip()

                frame_count += 1
                if frame_count % 60 == 0:
                    print(f"Rendered {frame_count} frames...")

            except Exception as render_error:
                print(f"Rendering error: {render_error}")
                import traceback
                traceback.print_exc()
                break

            core.wait(0.016)  # ~60 fps

    except Exception as e:
        print(f"Error creating window or scene: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if win is not None:
            win.close()
        core.quit()


if __name__ == "__main__":
    run_column_scene()
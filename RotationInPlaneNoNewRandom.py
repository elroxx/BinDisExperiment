from psychopy import visual, core, event
from pyglet.gl import *
import random


class SpecularStreakScene:
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
        print("Scene initialization complete")
        self.angle_x = 0  # Rotation  X
        self.angle_z = 0  # Rotation  Z

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # gradual light falloff
        glShadeModel(GL_SMOOTH)

        # black background
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def setup_lighting(self):
        # center far like sun
        light_pos = (GLfloat * 4)(0.0, 8.0, -40.0, 1.0)  # point light

        # Light properties (white light for B&W scene)
        light_ambient = (GLfloat * 4)(0.01, 0.01, 0.01, 1.0)
        light_diffuse = (GLfloat * 4)(0.8, 0.8, 0.8, 1.0)
        light_specular = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)

        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

    def setup_camera(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # perspective
        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # slightly above ground looking toward horizon
        gluLookAt(0.0, 1.5, 0.0,  # Eye position
                  0.0, 1.0, -10.0,  # Look at point
                  0.0, 1.0, 0.0)  # Up vector

    def generate_floor_geometry(self):
        # Tessellation parameters
        floor_size = 40.0
        divisions = 100
        step = floor_size / divisions

        # Store vertices and normals
        self.floor_vertices = []
        self.floor_normals = []

        def jittered_normal():
            nx = random.uniform(-0.7, 0.7)
            ny = 1.0
            nz = random.uniform(-0.05, 0.05)  # little variation in x but not in z
            # normalize
            length = (nx ** 2 + ny ** 2 + nz ** 2) ** 0.5
            return (nx / length, ny / length, nz / length)

        for i in range(divisions):
            for j in range(divisions):
                x1 = -floor_size / 2 + i * step
                x2 = x1 + step
                z1 = -floor_size / 2 + j * step
                z2 = z1 + step

                # Triangle 1 vertices and normals
                triangle1_vertices = [(x1, 0.0, z1), (x2, 0.0, z1), (x1, 0.0, z2)]
                triangle1_normals = [jittered_normal() for _ in range(3)]

                # Triangle 2 vertices and normals
                triangle2_vertices = [(x2, 0.0, z1), (x2, 0.0, z2), (x1, 0.0, z2)]
                triangle2_normals = [jittered_normal() for _ in range(3)]

                # Store all of em
                self.floor_vertices.extend(triangle1_vertices)
                self.floor_vertices.extend(triangle2_vertices)
                self.floor_normals.extend(triangle1_normals)
                self.floor_normals.extend(triangle2_normals)

    """def generate_floor_geometry(self):
        # Tessellation parameters
        floor_size = 40.0
        divisions = 100
        step = floor_size / divisions

        # Store vertices and normals
        self.floor_vertices = []
        self.floor_normals = []

        def jittered_normal():
            nx = random.uniform(-0.7, 0.7)
            ny = 1.0
            nz = random.uniform(-0.07, 0.07)  # small streak bias
            length = (nx ** 2 + ny ** 2 + nz ** 2) ** 0.5
            return (nx / length, ny / length, nz / length)

        for i in range(divisions):
            for j in range(divisions):
                x1 = -floor_size / 2 + i * step
                x2 = x1 + step
                z1 = -floor_size / 2 + j * step
                z2 = z1 + step

                # Random elevation values for each vertex (small perturbation)
                y1 = random.uniform(-0.01, 0.01)
                y2 = random.uniform(-0.01, 0.01)
                y3 = random.uniform(-0.01, 0.01)
                y4 = random.uniform(-0.01, 0.01)
                y5 = random.uniform(-0.01, 0.01)
                y6 = random.uniform(-0.01, 0.01)

                # Triangle 1
                triangle1_vertices = [(x1, y1, z1), (x2, y2, z1), (x1, y3, z2)]
                triangle1_normals = [jittered_normal() for _ in range(3)]

                # Triangle 2
                triangle2_vertices = [(x2, y4, z1), (x2, y5, z2), (x1, y6, z2)]
                triangle2_normals = [jittered_normal() for _ in range(3)]

                # Append
                self.floor_vertices.extend(triangle1_vertices)
                self.floor_vertices.extend(triangle2_vertices)
                self.floor_normals.extend(triangle1_normals)
                self.floor_normals.extend(triangle2_normals)
                """

    def render_glossy_floor(self):
        #pre gen geometry this time
        # MATERIAL PROPERTY FOR LIGHT REFLECTION
        mat_ambient = (GLfloat * 4)(0.01, 0.01, 0.01, 1.0)  # Fixed alpha
        mat_diffuse = (GLfloat * 4)(0.02, 0.02, 0.02, 1.0)
        mat_specular = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)
        mat_shininess = (GLfloat * 1)(128.0)

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)

        glColor3f(1.0, 1.0, 1.0)  # Reset color

        # pre gen fgeo this time
        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_vertices)):
            nx, ny, nz = self.floor_normals[i]
            x, y, z = self.floor_vertices[i]
            glNormal3f(nx, ny, nz)
            glVertex3f(x, y, z)
        glEnd()

    def render_frame(self):
        try:
            # Clear buffers
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glShadeModel(GL_SMOOTH)


            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            aspect_ratio = self.win.size[0] / self.win.size[1]
            gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(0.0, 1.5, 0.0, 0.0, 1.0, -10.0, 0.0, 1.0, 0.0)

            # lighting (after modelview matrix)
            self.setup_lighting()

            glPushMatrix()

            # rotation
            glRotatef(self.angle_x, 1.0, 0.0, 0.0)  # Rotate  X
            glRotatef(self.angle_z, 0.0, 0.0, 1.0)  # Rotate  Z

            self.render_glossy_floor()

            glPopMatrix()

        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            raise


def run_specular_scene():
    # main scene
    win = None
    try:
        # window
        win = visual.Window(
            size=[1024, 768],
            units='pix',
            fullscr=False,
            allowGUI=True,
            winType='pyglet',
            color=[0, 0, 0],
            colorSpace='rgb',
            waitBlanking=False  # improves responsiveness
        )
        win.recordFrameIntervals = False
        win.autoDraw = False

        # Initial flip
        win.flip()

        print("Window created successfully")
        print("Initializing OpenGL scene...")

        scene = SpecularStreakScene(win)

        # user input to start
        print("Press SPACE to start the scene...")
        event.waitKeys(keyList=['space'])

        clock = core.Clock()
        frame_count = 0

        while True:
            keys = event.getKeys()
            if 'escape' in keys or 'q' in keys:
                print("exiting")
                break
            if 'left' in keys:
                scene.angle_z -= 1
                print(f"Rotation Z: {scene.angle_z}")
            if 'right' in keys:
                scene.angle_z += 1
                print(f"Rotation Z: {scene.angle_z}")
            if 'up' in keys:
                scene.angle_x -= 1
                print(f"Rotation X: {scene.angle_x}")
            if 'down' in keys:
                scene.angle_x += 1
                print(f"Rotation X: {scene.angle_x}")

            try:
                # render
                scene.render_frame()

                # buffer
                win.flip()

                frame_count += 1
                if frame_count % 60 == 0:  # printing to see if its still rendering
                    print(f"Rendered {frame_count} frames...")

            except Exception as render_error:
                print(f"Rendering error: {render_error}")
                import traceback
                traceback.print_exc()
                break

            # mini delay
            core.wait(0.016)  # about 60 fps

    except Exception as e:
        print(f"Error creating window or scene: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if win is not None:
            win.close()
        core.quit()


if __name__ == "__main__":
    run_specular_scene()
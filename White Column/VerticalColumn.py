from psychopy import visual, core, event
from pyglet.gl import *
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
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_BLEND)  # Enable blending for transparency
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Gradual light falloff
        glShadeModel(GL_SMOOTH)

        # Black background
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def setup_lighting(self):
        # Center light source
        light_pos = (GLfloat * 4)(0.0, 8.0, -5.0, 1.0)  # Point light above the scene

        # Light properties
        light_ambient = (GLfloat * 4)(0.2, 0.2, 0.2, 1.0)
        light_diffuse = (GLfloat * 4)(0.8, 0.8, 0.8, 1.0)
        light_specular = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)

        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

    def setup_camera(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Perspective
        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Slightly above ground looking toward horizon
        gluLookAt(0.0, 1.5, 0.0,  # Eye position
                  0.0, 1.0, -10.0,  # Look at point
                  0.0, 1.0, 0.0)  # Up vector

    def generate_floor_geometry(self):
        # Tessellation parameters
        floor_size = 40.0
        divisions = 250
        step = floor_size / divisions

        # Store vertices and normals
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

                # Triangle 1 vertices and normals
                triangle1_vertices = [(x1, 0.0, z1), (x2, 0.0, z1), (x1, 0.0, z2)]
                triangle1_normals = [jittered_normal() for _ in range(3)]

                # Triangle 2 vertices and normals
                triangle2_vertices = [(x2, 0.0, z1), (x2, 0.0, z2), (x1, 0.0, z2)]
                triangle2_normals = [jittered_normal() for _ in range(3)]

                # Store all of them
                self.floor_vertices.extend(triangle1_vertices)
                self.floor_vertices.extend(triangle2_vertices)
                self.floor_normals.extend(triangle1_normals)
                self.floor_normals.extend(triangle2_normals)

    def generate_column_geometry(self):
        # Create a vertical column geometry that extends downward from the plane
        self.column_vertices = []
        self.column_normals = []

        # Column parameters
        column_width = 2.0
        column_height = 15.0  # downwards
        column_depth = 0.8
        segments = 50  # number of segment with randomness

        # vertical strips for my light column
        for i in range(segments):
            x_offset = random.gauss(0.0, 0.3)  # vertical variation but i also think i need to stretch more z_pos
            z_pos = -5.0 + (i / segments) * column_depth

            # quads extending downards
            x1 = -column_width / 2 + x_offset
            x2 = column_width / 2 + x_offset
            y1 = 0.0
            y2 = -column_height
            z1 = z_pos
            z2 = z_pos + (column_depth / segments)

            # Front face
            self.column_vertices.extend([
                (x1, y1, z1), (x2, y1, z1), (x2, y2, z1),
                (x1, y1, z1), (x2, y2, z1), (x1, y2, z1)
            ])
            self.column_normals.extend([(0, 0, 1)] * 6)

            # Back face
            self.column_vertices.extend([
                (x2, y1, z2), (x1, y1, z2), (x1, y2, z2),
                (x2, y1, z2), (x1, y2, z2), (x2, y2, z2)
            ])
            self.column_normals.extend([(0, 0, -1)] * 6)

            # Left face
            self.column_vertices.extend([
                (x1, y1, z2), (x1, y1, z1), (x1, y2, z1),
                (x1, y1, z2), (x1, y2, z1), (x1, y2, z2)
            ])
            self.column_normals.extend([(-1, 0, 0)] * 6)

            # Right face
            self.column_vertices.extend([
                (x2, y1, z1), (x2, y1, z2), (x2, y2, z2),
                (x2, y1, z1), (x2, y2, z2), (x2, y2, z1)
            ])
            self.column_normals.extend([(1, 0, 0)] * 6)

    def render_transparent_floor(self):
        # properties for transparent floor (material wise)
        mat_ambient = (GLfloat * 4)(0.1, 0.1, 0.1, 0.3)  # Low alpha for transparency
        mat_diffuse = (GLfloat * 4)(0.2, 0.2, 0.2, 0.3)
        mat_specular = (GLfloat * 4)(0.5, 0.5, 0.5, 0.3)
        mat_shininess = (GLfloat * 1)(32.0)

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)

        glColor4f(0.5, 0.5, 0.5, 0.3)  # Semi-transparent gray. Should put white tho? or fully transparent?

        # Render floor geometry
        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_vertices)):
            nx, ny, nz = self.floor_normals[i]
            x, y, z = self.floor_vertices[i]
            glNormal3f(nx, ny, nz)
            glVertex3f(x, y, z)
        glEnd()

    def render_white_column(self):
        # properties for bright white column (matierla wise)
        mat_ambient = (GLfloat * 4)(0.8, 0.8, 0.8, 1.0)
        mat_diffuse = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)
        mat_specular = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)
        mat_shininess = (GLfloat * 1)(64.0)

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)

        glColor4f(1.0, 1.0, 1.0, 1.0)  # Bright white

        # Render column geometry
        glBegin(GL_TRIANGLES)
        for i in range(len(self.column_vertices)):
            nx, ny, nz = self.column_normals[i]
            x, y, z = self.column_vertices[i]
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
            glEnable(GL_BLEND)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glShadeModel(GL_SMOOTH)

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            aspect_ratio = self.win.size[0] / self.win.size[1]
            gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(0.0, 1.5, 0.0, 0.0, 1.0, -10.0, 0.0, 1.0, 0.0)

            # Lighting (after modelview matrix)
            self.setup_lighting()

            glPushMatrix()

            # Rotation
            glRotatef(self.angle_x, 1.0, 0.0, 0.0)  # Rotate X
            glRotatef(self.angle_z, 0.0, 0.0, 1.0)  # Rotate Z

            # render column
            glDisable(GL_BLEND)
            self.render_white_column()

            # render floor
            glEnable(GL_BLEND)
            self.render_transparent_floor()

            glPopMatrix()

        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            raise


def run_column_scene():
    # Main scene
    win = None
    try:
        # Window
        win = visual.Window(
            size=[1024, 768],
            units='pix',
            fullscr=False,
            allowGUI=True,
            winType='pyglet',
            color=[0, 0, 0],
            colorSpace='rgb',
            waitBlanking=False  # for responsiveness
        )
        win.recordFrameIntervals = False
        win.autoDraw = False

        # Initial flip
        win.flip()

        print("Window created successfully")
        print("Initializing OpenGL scene...")

        scene = WhiteColumnScene(win)

        # User input to start
        print("Press SPACE to start the scene...")
        event.waitKeys(keyList=['space'])

        clock = core.Clock()
        frame_count = 0

        while True:
            keys = event.getKeys()
            if 'escape' in keys or 'q' in keys:
                print("Exiting")
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
                # Render
                scene.render_frame()

                # Buffer
                win.flip()

                frame_count += 1
                if frame_count % 60 == 0:  # Printing to see if it's still rendering
                    print(f"Rendered {frame_count} frames...")

            except Exception as render_error:
                print(f"Rendering error: {render_error}")
                import traceback
                traceback.print_exc()
                break

            # Mini delay
            core.wait(0.016)  # About 60 fps

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
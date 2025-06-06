from psychopy import visual, core, event
from pyglet.gl import *
import random

#HAVE TO FIX THE GROUND TEXTURE FOR THE MICROFACETS STUFF IN THE REFLECTION
class SpecularStreakScene:
    def __init__(self, win):
        self.win = win
        print("Setting up OpenGL...")
        self.setup_opengl()
        print("Setting up lighting...")
        self.setup_lighting()
        print("Setting up camera...")
        self.setup_camera()
        print("Scene initialization complete")

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # gradual light falloff
        glShadeModel(GL_SMOOTH)

        # black backgorund
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def setup_lighting(self):
        # center far like sun
        light_pos = (GLfloat * 4)(0.0, 8.0, -40.0, 1.0)  # point light (width=1 so there is technically a width)


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

    def create_glossy_floor(self):
        # Enable lighting and depth test
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)

        # MATERIAL PROPERTY FOR LIGHT REFLECTION
        mat_ambient = (GLfloat * 4)(0.01, 0.01, 0.01, 0.01)  # Darker ambient
        mat_diffuse = (GLfloat * 4)(0.02, 0.02, 0.02, 1.0)  # Darker diffuse
        mat_specular = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)  # Bright specular
        mat_shininess = (GLfloat * 1)(128.0)  # Higher shininess for sharp highlights

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)

        glColor3f(1.0, 1.0, 1.0)  # Reset color

        # Tessellation parameters
        floor_size = 40.0
        divisions = 120
        step = floor_size / divisions

        def jittered_normal():
            nx = random.uniform(-0.3, 0.3)
            ny = 1.0
            nz = random.uniform(-0.05, 0.05)  # Less variation in Z
            # Normalize the perturbed normal
            length = (nx ** 2 + ny ** 2 + nz ** 2) ** 0.5
            return (nx / length, ny / length, nz / length)

        glBegin(GL_TRIANGLES)

        for i in range(divisions):
            for j in range(divisions):
                x1 = -floor_size / 2 + i * step
                x2 = x1 + step
                z1 = -floor_size / 2 + j * step
                z2 = z1 + step

                # Triangle 1
                for (x, z) in [(x1, z1), (x2, z1), (x1, z2)]:
                    nx, ny, nz = jittered_normal()
                    glNormal3f(nx, ny, nz)
                    glVertex3f(x, 0.0, z)

                # Triangle 2
                for (x, z) in [(x2, z1), (x2, z2), (x1, z2)]:
                    nx, ny, nz = jittered_normal()
                    glNormal3f(nx, ny, nz)
                    glVertex3f(x, 0.0, z)

        glEnd()

    def render_frame(self):
        #render 1 frame but its always 1 frame anyway coz no movement
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Reset the modelview matrix
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            # setup camera again for consistency
            gluLookAt(0.0, 1.5, 0.0,  # Eye position
                      0.0, 1.0, -10.0,  # Look at point
                      0.0, 1.0, 0.0)  # Up vector

            # setup lighting each frame again
            self.setup_lighting()

            glPushMatrix()

            # glossy floor
            self.create_glossy_floor()

            glPopMatrix()

        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            raise


def run_specular_scene():
    #main scene
    win = None
    try:
        # window
        win = visual.Window(
            size=[1024, 768],
            units='pix',
            fullscr=False,
            allowGUI=True,
            winType='pyglet',
            color=[0, 0, 0],  # Black background
            colorSpace='rgb',
        )

        print("Window created successfully")
        print("Initializing OpenGL scene...")

        # scene
        scene = SpecularStreakScene(win)

        print("Specular Streaks Scene initialized")
        print("Press ESC or Q to exit, SPACE to continue")

        # user input to start coz weird bug ?
        print("Press SPACE to start the scene...")
        event.waitKeys(keyList=['space'])

        clock = core.Clock()
        frame_count = 0

        while True:
            # to exit
            keys = event.getKeys()
            if 'escape' in keys or 'q' in keys:
                print("Exiting...")
                break

            try:
                # Render the scene
                scene.render_frame()
                #win.flip()

                frame_count += 1
                if frame_count % 60 == 0:  #printing to see if its stillrendering
                    print(f"Rendered {frame_count} frames...")

            except Exception as render_error:
                print(f"Rendering error: {render_error}")
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
from psychopy import visual, core, event
from pyglet.gl import *
import random
import numpy as np
import math


class SpecularStreakScene:
    def __init__(self, win):
        self.win = win
        print("Setting up OpenGL...")
        self.setup_opengl()
        print("Setting up custom lighting...")
        self.setup_custom_lighting()

        # Initialize angles first
        self.angle_x = 0  # Rotation X
        self.angle_z = 0  # Rotation Z

        # Store original positions for transformation
        self.original_light_pos = np.array([0.0, 1.0, -100.0])
        self.original_camera_pos = np.array([0.0, 1.5, 0.0])

        print("Generating floor geometry...")
        self.generate_floor_geometry()
        print("Scene initialization complete")

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        # DISABLED LIGHTNING TO DO A CUSTOM MODEL
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)

        # Enable vertex colors
        glEnable(GL_COLOR_MATERIAL)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def setup_custom_lighting(self):
        # LIGHT SOURCE
        self.light_pos = np.array([0.0, 1.0, -100.0])

        # camera pos
        self.camera_pos = np.array([0.0, 1.5, 0.0])

        # properties for material
        self.material = {
            'ambient': np.array([0.05, 0.05, 0.05]),
            'diffuse': np.array([0, 0, 0]),  # low diffuse === wet surface ???
            'specular': np.array([1.0, 1.0, 1.0]),  # Very high specular
            'shininess': 128.0,  # Same shinyness asbefore
            'roughness': 0.05  # only for ward
        }

        # properties for light
        self.light = {
            'ambient': np.array([0.02, 0.02, 0.02]),
            'diffuse': np.array([0, 0, 0]),
            'specular': np.array([1.0, 1.0, 1.0])
        }

        # Lighting model selection
        self.use_ward = False

    def get_rotation_matrix_x(self, angle_deg):
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return np.array([
            [1, 0, 0],
            [0, cos_a, -sin_a],
            [0, sin_a, cos_a]
        ])

    def get_rotation_matrix_z(self, angle_deg):
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ])

    def get_inverse_rotation_matrix(self):
        #inverse rotation for current angles
        rot_z = self.get_rotation_matrix_z(-self.angle_z)
        rot_x = self.get_rotation_matrix_x(-self.angle_x)
        return np.dot(rot_z, rot_x)

    def update_lighting_positions(self):
        # Get inverse rotation matrix to transform light and camera positions
        inv_rotation = self.get_inverse_rotation_matrix()

        # Transform light position (apply inverse rotation)
        self.light_pos = np.dot(inv_rotation, self.original_light_pos)

        # Transform camera position (apply inverse rotation)
        self.camera_pos = np.dot(inv_rotation, self.original_camera_pos)

    def normalize(self, v):
        # normalize vector + avoiding div by 0
        norm = np.linalg.norm(v)
        if norm < 1e-8:  # if very small vector
            return np.array([0.0, 1.0, 0.0])  # it defaults to up vector
        return v / norm

    def blinn_phong_lighting(self, vertex_pos, normal, view_pos, light_pos):
        # Convert to numpy arrays
        pos = np.array(vertex_pos)
        n = np.array(normal)

        # vectors
        light_dir = self.normalize(light_pos - pos)
        view_dir = self.normalize(view_pos - pos)
        half_vector = self.normalize(light_dir + view_dir)  # half angle vec

        # light components
        ambient = self.material['ambient'] * self.light['ambient']
        n_dot_l = max(0.0, np.dot(n, light_dir))
        diffuse = self.material['diffuse'] * self.light['diffuse'] * n_dot_l
        n_dot_h = max(0.0, np.dot(n, half_vector))  # specular blinn phong
        spec_power = n_dot_h ** self.material['shininess']
        specular = self.material['specular'] * self.light['specular'] * spec_power

        # combine colors
        color = ambient + diffuse + specular

        # clip to base interval 0, 1
        return np.clip(color, 0.0, 1.0)

    def ward_lighting(self, vertex_pos, normal, view_pos, light_pos):
        # WARD BUT JUST FOR DEBUG PURPOSES
        pos = np.array(vertex_pos)
        n = np.array(normal)

        light_dir = self.normalize(light_pos - pos)
        view_dir = self.normalize(view_pos - pos)
        half_vector = self.normalize(light_dir + view_dir)

        # Ambient
        ambient = self.material['ambient'] * self.light['ambient']

        # Diffuse (Lambertian)
        n_dot_l = max(0.0, np.dot(n, light_dir))
        diffuse = self.material['diffuse'] * self.light['diffuse'] * n_dot_l

        # Ward specular component with safety checks
        n_dot_v = max(0.001, np.dot(n, view_dir))  # Avoid division by zero
        n_dot_h = max(0.0, np.dot(n, half_vector))

        # Safety check: if light or view direction is too perpendicular, skip specular
        if n_dot_l < 0.001 or n_dot_v < 0.001:
            specular = np.array([0.0, 0.0, 0.0])
        else:
            # Angle between normal and half vector
            cos_delta = n_dot_h

            # Safety check for cos_delta
            if cos_delta < 0.001:
                specular = np.array([0.0, 0.0, 0.0])
            else:
                tan_delta_sq = (1.0 - cos_delta * cos_delta) / (cos_delta * cos_delta)

                # Ward BRDF specular term
                alpha = max(0.001, self.material['roughness'])  # Ensure alpha > 0

                # Safety check for extreme values
                if tan_delta_sq / (alpha * alpha) > 20:  # Prevent exp overflow
                    ward_spec = 0.0
                else:
                    ward_spec = math.exp(-tan_delta_sq / (alpha * alpha))

                    # Denominator with safety check
                    denominator = 4.0 * math.pi * alpha * alpha * math.sqrt(n_dot_l * n_dot_v)
                    if denominator > 0.0001:
                        ward_spec /= denominator
                    else:
                        ward_spec = 0.0

                specular = self.material['specular'] * self.light['specular'] * ward_spec

        color = ambient + diffuse + specular
        return np.clip(color, 0.0, 1.0)

    def generate_floor_geometry(self):
        # Update lighting positions based on current rotation
        self.update_lighting_positions()

        # floor params
        floor_size_z = 40.0
        floor_size_x = 40.0
        divisions_x = 100
        divisions_z = 100
        step_x = floor_size_x / divisions_x
        step_z = floor_size_z / divisions_z

        self.floor_vertices = []
        self.floor_normals = []
        self.floor_colors = []

        def jittered_normal():
            nx = random.gauss(0.0, 0.1)
            ny = 1.0
            nz = random.gauss(0.0, 0.02)  # I can play with variation
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            return (nx / length, ny / length, nz / length)

        # plane
        for i in range(divisions_x):
            for j in range(divisions_z):
                x1 = -floor_size_x / 2 + i * step_x
                x2 = x1 + step_x
                z1 = -floor_size_z / 2 + j * step_z
                z2 = z1 + step_z

                # Triangle 1
                v1 = (x1, 0.0, z1)
                v2 = (x2, 0.0, z1)
                v3 = (x1, 0.0, z2)

                # Triangle 2
                v4 = (x2, 0.0, z1)
                v5 = (x2, 0.0, z2)
                v6 = (x1, 0.0, z2)

                # normals time
                n1 = jittered_normal()
                n2 = jittered_normal()
                n3 = jittered_normal()
                n4 = jittered_normal()
                n5 = jittered_normal()
                n6 = jittered_normal()

                # compute lightning for EACH VERTEX
                try:
                    if self.use_ward:
                        c1 = self.ward_lighting(v1, n1, self.camera_pos, self.light_pos)
                        c2 = self.ward_lighting(v2, n2, self.camera_pos, self.light_pos)
                        c3 = self.ward_lighting(v3, n3, self.camera_pos, self.light_pos)
                        c4 = self.ward_lighting(v4, n4, self.camera_pos, self.light_pos)
                        c5 = self.ward_lighting(v5, n5, self.camera_pos, self.light_pos)
                        c6 = self.ward_lighting(v6, n6, self.camera_pos, self.light_pos)
                    else:
                        c1 = self.blinn_phong_lighting(v1, n1, self.camera_pos, self.light_pos)
                        c2 = self.blinn_phong_lighting(v2, n2, self.camera_pos, self.light_pos)
                        c3 = self.blinn_phong_lighting(v3, n3, self.camera_pos, self.light_pos)
                        c4 = self.blinn_phong_lighting(v4, n4, self.camera_pos, self.light_pos)
                        c5 = self.blinn_phong_lighting(v5, n5, self.camera_pos, self.light_pos)
                        c6 = self.blinn_phong_lighting(v6, n6, self.camera_pos, self.light_pos)
                except Exception as e:
                    print(f"Lighting calculation error at ({i}, {j}): {e}")
                    # if bug its gray
                    c1 = c2 = c3 = c4 = c5 = c6 = np.array([0.1, 0.1, 0.1])

                # store triangle so that I can change the angle later on without recomputing everything like before
                self.floor_vertices.extend([v1, v2, v3, v4, v5, v6])
                self.floor_normals.extend([n1, n2, n3, n4, n5, n6])
                self.floor_colors.extend([c1, c2, c3, c4, c5, c6])

    def setup_camera(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # camera pos same as before
        gluLookAt(0.0, 1.5, 0.0,  # Eye position
                  0.0, 1.0, -10.0,  # Look at point
                  0.0, 1.0, 0.0)  # Up vector

    def render_glossy_floor(self):
        # Render using vertex colors computed with our custom lighting
        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_vertices)):
            # Set color for this vertex
            color = self.floor_colors[i]
            glColor3f(color[0], color[1], color[2])

            # Set normal (still useful for potential future effects)
            normal = self.floor_normals[i]
            glNormal3f(normal[0], normal[1], normal[2])

            # Set vertex position
            vertex = self.floor_vertices[i]
            glVertex3f(vertex[0], vertex[1], vertex[2])
        glEnd()

    def update_lighting_params(self, light_height=None, roughness=None, shininess=None):
        if light_height is not None:
            self.original_light_pos[1] = light_height
        if roughness is not None:
            self.material['roughness'] = roughness
        if shininess is not None:
            self.material['shininess'] = shininess

        #  geo if changing model
        model_name = "Ward BRDF" if self.use_ward else "Blinn-Phong"
        print(
            f"Updating lighting ({model_name}): height={self.original_light_pos[1]:.1f}, Z={self.original_light_pos[2]:.1f}, roughness={self.material['roughness']:.3f}, shininess={self.material['shininess']:.1f}")
        self.generate_floor_geometry()

    def update_angles(self, delta_x=0, delta_z=0):
        """Update rotation angles and regenerate geometry if needed"""
        old_angle_x = self.angle_x
        old_angle_z = self.angle_z

        self.angle_x += delta_x
        self.angle_z += delta_z

        # Only regenerate if angles actually changed
        if self.angle_x != old_angle_x or self.angle_z != old_angle_z:
            print(f"Rotation updated - X: {self.angle_x}, Z: {self.angle_z}")
            self.generate_floor_geometry()

    def render_frame(self):
        try:
            # hashtag buffers
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)
            glShadeModel(GL_SMOOTH)

            self.setup_camera()

            glPushMatrix()

            # rotations
            glRotatef(self.angle_x, 1.0, 0.0, 0.0)
            glRotatef(self.angle_z, 0.0, 1.0, 0.0)

            self.render_glossy_floor()

            glPopMatrix()

        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            raise


def run_specular_scene():
    win = None
    try:
        # Create window
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
        print("Initializing custom specular streak scene...")

        scene = SpecularStreakScene(win)

        print("Controls:")
        print("SPACE - Start scene")
        print("Arrow keys - Rotate view (automatically recomputes lighting)")
        print("1/2 - Adjust light height")
        print("3/4 - Adjust surface roughness")
        print("5/6 - Adjust shininess")
        print("7/8 - Adjust light Z position")
        print("W - Toggle Ward/Blinn-Phong lighting")
        print("R - Regenerate geometry")
        print("ESC/Q - Exit")

        event.waitKeys(keyList=['space'])

        clock = core.Clock()
        frame_count = 0

        while True:
            keys = event.getKeys()
            if 'escape' in keys or 'q' in keys:
                print("Exiting...")
                break

            # View controls - now properly updates lighting
            if 'left' in keys:
                scene.update_angles(delta_z=-10)
            if 'right' in keys:
                scene.update_angles(delta_z=10)
            if 'up' in keys:
                scene.update_angles(delta_x=-1)
            if 'down' in keys:
                scene.update_angles(delta_x=1)

            # Lighting parameter controls
            if '1' in keys:
                scene.update_lighting_params(light_height=scene.original_light_pos[1] + 2)
            if '2' in keys:
                scene.update_lighting_params(light_height=scene.original_light_pos[1] - 2)
            if '3' in keys:
                new_roughness = min(0.2, scene.material['roughness'] + 0.01)
                scene.update_lighting_params(roughness=new_roughness)
            if '4' in keys:
                new_roughness = max(0.01, scene.material['roughness'] - 0.01)
                scene.update_lighting_params(roughness=new_roughness)
            if '5' in keys:
                new_shininess = min(500, scene.material['shininess'] + 20)
                scene.update_lighting_params(shininess=new_shininess)
            if '6' in keys:
                new_shininess = max(10, scene.material['shininess'] - 20)
                scene.update_lighting_params(shininess=new_shininess)
            if '7' in keys:
                scene.original_light_pos[2] -= 5
                print(f"Light Z position: {scene.original_light_pos[2]}")
                scene.generate_floor_geometry()
            if '8' in keys:
                scene.original_light_pos[2] += 5
                print(f"Light Z position: {scene.original_light_pos[2]}")
                scene.generate_floor_geometry()
            if 'w' in keys:
                scene.use_ward = not scene.use_ward
                model_name = "Ward BRDF" if scene.use_ward else "Blinn-Phong"
                print(f"Switched to {model_name}")
                scene.generate_floor_geometry()
            if 'r' in keys:
                print("Regenerating geometry...")
                scene.generate_floor_geometry()

            try:
                # Render frame
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

            # Frame rate limiting
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
    run_specular_scene()

    # THE BLINN-PHONG ONE IS WORKING I THINK
from psychopy import visual, core, event
from pyglet.gl import *
import random
import numpy as np
import math

# Test with numba
try:
    from numba import jit, prange

    NUMBA_AVAILABLE = True
    print("Numba available - using accelerated lighting calculations")
except ImportError:
    print("Numba not available - using pure NumPy (slower but still optimized)")
    NUMBA_AVAILABLE = False


    # Needed decorator
    def jit(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


    def prange(n):
        return range(n)

# numba test
if NUMBA_AVAILABLE:
    @jit(nopython=True, parallel=True)
    def compute_blinn_phong_numba(vertices, normals, light_pos, camera_pos,
                                  material_ambient, material_diffuse, material_specular,
                                  light_ambient, light_diffuse, light_specular, shininess):
        num_vertices = vertices.shape[0]
        colors = np.zeros((num_vertices, 3), dtype=np.float32)

        for i in prange(num_vertices):
            # vector compute
            light_dir = light_pos - vertices[i]
            light_dist = np.sqrt(np.sum(light_dir * light_dir))
            if light_dist > 1e-8:
                light_dir = light_dir / light_dist

            view_dir = camera_pos - vertices[i]
            view_dist = np.sqrt(np.sum(view_dir * view_dir))
            if view_dist > 1e-8:
                view_dir = view_dir / view_dist

            half_vector = light_dir + view_dir
            half_dist = np.sqrt(np.sum(half_vector * half_vector))
            if half_dist > 1e-8:
                half_vector = half_vector / half_dist

            # light components
            ambient = material_ambient * light_ambient

            n_dot_l = max(0.0, np.sum(normals[i] * light_dir))
            diffuse = material_diffuse * light_diffuse * n_dot_l

            n_dot_h = max(0.0, np.sum(normals[i] * half_vector))
            spec_power = n_dot_h ** shininess
            specular = material_specular * light_specular * spec_power

            # clamp
            color = ambient + diffuse + specular
            colors[i] = np.clip(color, 0.0, 1.0)

        return colors


class OptimizedSpecularStreakScene:
    def __init__(self, win):
        self.win = win
        print("Setting up OpenGL...")
        self.setup_opengl()
        print("Setting up custom lighting...")
        self.setup_custom_lighting()

        # Initialize angles
        self.angle_x = 0
        self.angle_z = 0

        # Store original positions for transformation
        self.original_light_pos = np.array([0.0, 1.0, -100.0], dtype=np.float32)
        self.original_camera_pos = np.array([0.0, 1.5, 0.0], dtype=np.float32)

        # Cache for expensive calculations
        self._rotation_cache = {}
        self._geometry_cache = None

        # Rendering method selection
        self.use_vertex_arrays = True
        self.rendering_method = "vertex_arrays"  # or "immediate_mode"

        print("Generating floor geometry...")
        self.generate_floor_geometry()
        print("Scene initialization complete")

    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def setup_custom_lighting(self):
        self.light_pos = np.array([0.0, 1.0, -100.0], dtype=np.float32)
        self.camera_pos = np.array([0.0, 1.5, 0.0], dtype=np.float32)

        # properties
        self.material = {
            'ambient': np.array([0.05, 0.05, 0.05], dtype=np.float32),
            'diffuse': np.array([0.0, 0.0, 0.0], dtype=np.float32),
            'specular': np.array([1.0, 1.0, 1.0], dtype=np.float32),
            'shininess': 128.0,
            'roughness': 0.05
        }

        self.light = {
            'ambient': np.array([0.02, 0.02, 0.02], dtype=np.float32),
            'diffuse': np.array([0.0, 0.0, 0.0], dtype=np.float32),
            'specular': np.array([1.0, 1.0, 1.0], dtype=np.float32)
        }

        self.use_ward = False

    def get_rotation_matrix_x(self, angle_deg):
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return np.array([
            [1, 0, 0],
            [0, cos_a, -sin_a],
            [0, sin_a, cos_a]
        ], dtype=np.float32)

    def get_rotation_matrix_z(self, angle_deg):
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ], dtype=np.float32)

    def get_inverse_rotation_matrix(self):
        # cache key to not compute everysingle time
        cache_key = (round(self.angle_x, 2), round(self.angle_z, 2))

        if cache_key not in self._rotation_cache:
            # inverse rot
            rot_z = self.get_rotation_matrix_z(-self.angle_z)
            rot_x = self.get_rotation_matrix_x(-self.angle_x)
            # same order
            self._rotation_cache[cache_key] = np.dot(rot_z, rot_x)

        return self._rotation_cache[cache_key]

    def update_lighting_positions(self):
        inv_rotation = self.get_inverse_rotation_matrix()

        # apply inverse rot
        self.light_pos = np.dot(inv_rotation, self.original_light_pos)

        # on cam
        self.camera_pos = np.dot(inv_rotation, self.original_camera_pos)

    def generate_floor_geometry_static(self):
        #ONLY CALL STATIC GEO ONCE
        if self._geometry_cache is not None:
            return self._geometry_cache

        floor_size_z = 20.0
        floor_size_x = 10.0
        divisions_x = 25
        divisions_z = 100

        # Pregeo
        num_triangles = divisions_x * divisions_z * 2
        num_vertices = num_triangles * 3

        vertices = np.zeros((num_vertices, 3), dtype=np.float32)
        normals = np.zeros((num_vertices, 3), dtype=np.float32)

        step_x = floor_size_x / divisions_x
        step_z = floor_size_z / divisions_z

        # pre gen
        np.random.seed(42)
        normal_variations = np.random.normal(0, [0.1, 0.0, 0.1], (num_vertices, 3))
        normal_variations[:, 1] = 1.0  # need y as 1

        # normalize all at once
        norms = np.linalg.norm(normal_variations, axis=1, keepdims=True)
        normals = normal_variations / norms

        idx = 0
        for i in range(divisions_x):
            for j in range(divisions_z):
                x1 = -floor_size_x / 2 + i * step_x
                x2 = x1 + step_x
                z1 = -floor_size_z + j * step_z
                z2 = z1 + step_z

                # Triangle 1 vertices
                vertices[idx:idx + 3] = [
                    [x1, 0.0, z1],
                    [x2, 0.0, z1],
                    [x1, 0.0, z2]
                ]

                # Triangle 2 vertices
                vertices[idx + 3:idx + 6] = [
                    [x2, 0.0, z1],
                    [x2, 0.0, z2],
                    [x1, 0.0, z2]
                ]

                idx += 6

        self._geometry_cache = (vertices, normals)
        return vertices, normals

    def compute_lighting_vectorized(self, vertices, normals):
        if self.use_ward:
            print("Using Ward BRDF lighting...")
            return self.compute_ward_lighting_fallback(vertices, normals)
        else:
            print("Using Blinn-Phong lighting...")

            if NUMBA_AVAILABLE:
                try:
                    colors = compute_blinn_phong_numba(
                        vertices, normals, self.light_pos, self.camera_pos,
                        self.material['ambient'], self.material['diffuse'], self.material['specular'],
                        self.light['ambient'], self.light['diffuse'], self.light['specular'],
                        self.material['shininess']
                    )
                    print(f"Numba: Computed {len(colors)} colors, range: {np.min(colors):.3f} to {np.max(colors):.3f}")
                    return colors
                except Exception as e:
                    print(f"Numba calculation failed: {e}, falling back to NumPy")

            # pure numpy
            return self.compute_blinn_phong_numpy(vertices, normals)

    def compute_blinn_phong_numpy(self, vertices, normals):
        #numpy only
        print("Using pure NumPy Blinn-Phong implementation...")

        # vecto in numpy
        light_dirs = self.light_pos[np.newaxis, :] - vertices  # (N, 3)
        light_dists = np.linalg.norm(light_dirs, axis=1, keepdims=True)  # (N, 1)
        light_dirs = light_dirs / np.maximum(light_dists, 1e-8)  # Normalize

        view_dirs = self.camera_pos[np.newaxis, :] - vertices  # (N, 3)
        view_dists = np.linalg.norm(view_dirs, axis=1, keepdims=True)  # (N, 1)
        view_dirs = view_dirs / np.maximum(view_dists, 1e-8)  # Normalize

        half_vectors = light_dirs + view_dirs  # (N, 3)
        half_dists = np.linalg.norm(half_vectors, axis=1, keepdims=True)  # (N, 1)
        half_vectors = half_vectors / np.maximum(half_dists, 1e-8)  # Normalize

        # light compo
        ambient = self.material['ambient'] * self.light['ambient']  # (3,)
        ambient = np.tile(ambient, (len(vertices), 1))  # (N, 3)

        n_dot_l = np.maximum(0.0, np.sum(normals * light_dirs, axis=1, keepdims=True))  # (N, 1)
        diffuse = self.material['diffuse'] * self.light['diffuse'] * n_dot_l  # (N, 3)

        n_dot_h = np.maximum(0.0, np.sum(normals * half_vectors, axis=1, keepdims=True))  # (N, 1)
        spec_power = np.power(n_dot_h, self.material['shininess'])  # (N, 1)
        specular = self.material['specular'] * self.light['specular'] * spec_power  # (N, 3)

        # camp
        colors = ambient + diffuse + specular
        colors = np.clip(colors, 0.0, 1.0)

        print(f"NumPy: Computed {len(colors)} colors, range: {np.min(colors):.3f} to {np.max(colors):.3f}")
        return colors.astype(np.float32)

    def compute_ward_lighting_fallback(self, vertices, normals):
        #still base ward
        colors = np.zeros((len(vertices), 3), dtype=np.float32)

        for i, (vertex, normal) in enumerate(zip(vertices, normals)):
            try:
                color = self.ward_lighting_single(vertex, normal, self.camera_pos, self.light_pos)
                colors[i] = color
            except:
                colors[i] = np.array([0.1, 0.1, 0.1])

        return colors

    def ward_lighting_single(self, vertex_pos, normal, view_pos, light_pos):
        #ward
        pos = np.array(vertex_pos, dtype=np.float32)
        n = np.array(normal, dtype=np.float32)

        light_dir = light_pos - pos
        light_dir = light_dir / max(1e-8, np.linalg.norm(light_dir))

        view_dir = view_pos - pos
        view_dir = view_dir / max(1e-8, np.linalg.norm(view_dir))

        half_vector = light_dir + view_dir
        half_vector = half_vector / max(1e-8, np.linalg.norm(half_vector))

        # Ambient
        ambient = self.material['ambient'] * self.light['ambient']

        # Diffuse
        n_dot_l = max(0.0, np.dot(n, light_dir))
        diffuse = self.material['diffuse'] * self.light['diffuse'] * n_dot_l

        # Ward specular with safety checks
        n_dot_v = max(0.001, np.dot(n, view_dir))
        n_dot_h = max(0.0, np.dot(n, half_vector))

        if n_dot_l < 0.001 or n_dot_v < 0.001 or n_dot_h < 0.001:
            specular = np.array([0.0, 0.0, 0.0])
        else:
            cos_delta = n_dot_h
            tan_delta_sq = (1.0 - cos_delta * cos_delta) / (cos_delta * cos_delta)
            alpha = max(0.001, self.material['roughness'])

            if tan_delta_sq / (alpha * alpha) > 20:
                ward_spec = 0.0
            else:
                ward_spec = math.exp(-tan_delta_sq / (alpha * alpha))
                denominator = 4.0 * math.pi * alpha * alpha * math.sqrt(n_dot_l * n_dot_v)
                if denominator > 0.0001:
                    ward_spec /= denominator
                else:
                    ward_spec = 0.0

            specular = self.material['specular'] * self.light['specular'] * ward_spec

        color = ambient + diffuse + specular
        return np.clip(color, 0.0, 1.0)

    def generate_floor_geometry(self):
        self.update_lighting_positions()

        # gen static geo
        vertices, normals = self.generate_floor_geometry_static()

        # light all vert
        colors = self.compute_lighting_vectorized(vertices, normals)

        # STORE
        self.floor_vertices = np.ascontiguousarray(vertices, dtype=np.float32)
        self.floor_normals = np.ascontiguousarray(normals, dtype=np.float32)
        self.floor_colors = np.ascontiguousarray(colors, dtype=np.float32)

        print(f"Generated geometry: {len(self.floor_vertices)} vertices")
        print(f"Light pos: {self.light_pos}, Camera pos: {self.camera_pos}")
        print(f"Color range: min={np.min(self.floor_colors):.3f}, max={np.max(self.floor_colors):.3f}")

    def setup_camera(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspect_ratio = self.win.size[0] / self.win.size[1]
        gluPerspective(45.0, aspect_ratio, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 1.5, 0.0, 0.0, 1.0, -10.0, 0.0, 1.0, 0.0)

    def render_glossy_floor(self):
        #optimized witbh fallback
        if self.rendering_method == "vertex_arrays" and self.use_vertex_arrays:
            try:
                self.render_vertex_arrays()
            except Exception as e:
                print(f"Vertex array rendering failed: {e}")
                print("Switching to immediate mode...")
                self.rendering_method = "immediate_mode"
                self.use_vertex_arrays = False
                self.render_immediate_mode()
        else:
            self.render_immediate_mode()

    def render_vertex_arrays(self):
        #vertex array
        vertices_gl = np.ascontiguousarray(self.floor_vertices, dtype=np.float32)
        normals_gl = np.ascontiguousarray(self.floor_normals, dtype=np.float32)
        colors_gl = np.ascontiguousarray(self.floor_colors, dtype=np.float32)

        # sometimes the shape were weird so debug
        if len(vertices_gl.shape) != 2 or vertices_gl.shape[1] != 3:
            raise ValueError(f"Invalid vertex array shape: {vertices_gl.shape}")
        if len(normals_gl.shape) != 2 or normals_gl.shape[1] != 3:
            raise ValueError(f"Invalid normal array shape: {normals_gl.shape}")
        if len(colors_gl.shape) != 2 or colors_gl.shape[1] != 3:
            raise ValueError(f"Invalid color array shape: {colors_gl.shape}")

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        # ctypes
        glVertexPointer(3, GL_FLOAT, 0, vertices_gl.ctypes.data)
        glNormalPointer(GL_FLOAT, 0, normals_gl.ctypes.data)
        glColorPointer(3, GL_FLOAT, 0, colors_gl.ctypes.data)

        glDrawArrays(GL_TRIANGLES, 0, len(self.floor_vertices))

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

    def render_immediate_mode(self):
        #FALLBACK NORMAL
        glBegin(GL_TRIANGLES)
        for i in range(len(self.floor_vertices)):
            color = self.floor_colors[i]
            glColor3f(float(color[0]), float(color[1]), float(color[2]))

            normal = self.floor_normals[i]
            glNormal3f(float(normal[0]), float(normal[1]), float(normal[2]))

            vertex = self.floor_vertices[i]
            glVertex3f(float(vertex[0]), float(vertex[1]), float(vertex[2]))
        glEnd()

    def update_lighting_params(self, light_height=None, roughness=None, shininess=None):
        if light_height is not None:
            self.original_light_pos[1] = light_height
        if roughness is not None:
            self.material['roughness'] = roughness
        if shininess is not None:
            self.material['shininess'] = shininess

        model_name = "Ward BRDF" if self.use_ward else "Blinn-Phong"
        print(f"Updating lighting ({model_name}): height={self.original_light_pos[1]:.1f}, "
              f"Z={self.original_light_pos[2]:.1f}, roughness={self.material['roughness']:.3f}, "
              f"shininess={self.material['shininess']:.1f}")

        self.generate_floor_geometry()

    def update_angles(self, delta_x=0, delta_z=0):
        old_angle_x = self.angle_x
        old_angle_z = self.angle_z

        self.angle_x += delta_x
        self.angle_z += delta_z

        if self.angle_x != old_angle_x or self.angle_z != old_angle_z:
            print(f"Rotation updated - X: {self.angle_x}, Z: {self.angle_z}")

            cache_key = (round(self.angle_x, 2), round(self.angle_z, 2))
            if cache_key in self._rotation_cache:
                del self._rotation_cache[cache_key]

            # update light pos
            self.update_lighting_positions()
            print(f"Light position after rotation: {self.light_pos}")
            print(f"Camera position after rotation: {self.camera_pos}")

            # regen only lightning
            vertices, normals = self.generate_floor_geometry_static()
            colors = self.compute_lighting_vectorized(vertices, normals)

            # Store
            self.floor_vertices = np.ascontiguousarray(vertices, dtype=np.float32)
            self.floor_normals = np.ascontiguousarray(normals, dtype=np.float32)
            self.floor_colors = np.ascontiguousarray(colors, dtype=np.float32)

    def render_frame(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)
            glShadeModel(GL_SMOOTH)

            self.setup_camera()

            glPushMatrix()
            glRotatef(self.angle_x, 1.0, 0.0, 0.0)
            glRotatef(self.angle_z, 0.0, 1.0, 0.0)

            self.render_glossy_floor()

            glPopMatrix()

        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            raise


def run_optimized_specular_scene():
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
        print("Initializing optimized specular streak scene...")

        scene = OptimizedSpecularStreakScene(win)

        print("Controls:")
        print("SPACE - Start scene")
        print("Arrow keys - Rotate view")
        print("1/2 - Adjust light height")
        print("3/4 - Adjust surface roughness")
        print("5/6 - Adjust shininess")
        print("7/8 - Adjust light Z position")
        print("W - Toggle Ward/Blinn-Phong lighting")
        print("V - Toggle vertex arrays/immediate mode rendering")
        print("R - Regenerate geometry")
        print("ESC/Q - Exit")

        event.waitKeys(keyList=['space'])

        clock = core.Clock()
        frame_count = 0
        fps_counter = 0
        fps_timer = clock.getTime()

        while True:
            keys = event.getKeys()
            if 'escape' in keys or 'q' in keys:
                print("Exiting...")
                break

            if keys:
                # controls
                if 'left' in keys:
                    scene.update_angles(delta_z=-10)
                if 'right' in keys:
                    scene.update_angles(delta_z=10)
                if 'up' in keys:
                    scene.update_angles(delta_x=-1)
                if 'down' in keys:
                    scene.update_angles(delta_x=1)

                # Lighting controls
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
                if 'v' in keys:
                    scene.use_vertex_arrays = not scene.use_vertex_arrays
                    scene.rendering_method = "vertex_arrays" if scene.use_vertex_arrays else "immediate_mode"
                    render_method = "Vertex Arrays" if scene.use_vertex_arrays else "Immediate Mode"
                    print(f"Switched to {render_method} rendering")
                if 'r' in keys:
                    print("Regenerating geometry...")
                    scene._geometry_cache = None  # Clear cache
                    scene.generate_floor_geometry()

            try:
                scene.render_frame()
                win.flip()

                frame_count += 1
                fps_counter += 1

                # FPS reporting every 2 seconds
                current_time = clock.getTime()
                if current_time - fps_timer >= 2.0:
                    fps = fps_counter / (current_time - fps_timer)
                    print(f"FPS: {fps:.1f} ({frame_count} total frames)")
                    fps_counter = 0
                    fps_timer = current_time

            except Exception as render_error:
                print(f"Rendering error: {render_error}")
                import traceback
                traceback.print_exc()
                break

            # rate limiting
            core.wait(0.001)  # slight wait

    except Exception as e:
        print(f"Error creating window or scene: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if win is not None:
            win.close()
        core.quit()


if __name__ == "__main__":
    run_optimized_specular_scene()
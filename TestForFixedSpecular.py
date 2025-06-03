import numpy as np
import psychopy.visual as visual
import psychopy.core as core
import psychopy.event as event
from psychopy import monitors
import pyglet
from pyglet.gl import *
import math


class SpecularStreakSimulation:
    def __init__(self):
        # Set up monitor and window
        self.win = visual.Window(
            size=[1200, 800],
            units='pix',
            allowGUI=False,
            fullscr=False,
            winType='pyglet'
        )

        # Scene parameters
        self.ground_size = 50.0
        self.ground_resolution = 100

        # Light sources (position: [x, y, z], color: [r, g, b], intensity)
        self.lights = [
            {'pos': [-15.0, 8.0, 25.0], 'color': [1.0, 0.9, 0.7], 'intensity': 100.0},
            {'pos': [0.0, 12.0, 35.0], 'color': [1.0, 1.0, 1.0], 'intensity': 150.0},
            {'pos': [20.0, 6.0, 45.0], 'color': [0.9, 0.8, 1.0], 'intensity': 80.0},
        ]

        # Camera parameters
        self.camera_pos = np.array([0.0, 3.0, 0.0])  # Viewer at ground level + 3m height
        self.camera_target = np.array([0.0, 0.0, 30.0])

        # Material parameters (Blinn-Phong model)
        self.material = {
            'ambient': 0.1,
            'diffuse': 0.3,
            'specular': 0.8,
            'shininess': 1000.0,  # High shininess for wet surface
            'roughness': 0.05  # Low roughness for smooth wet surface
        }

        # Animation parameters
        self.time = 0.0
        self.light_animation = True

        self.setup_opengl()
        self.create_ground_mesh()

    def setup_opengl(self):
        """Initialize OpenGL settings for 3D rendering"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_LIGHT2)

        # Enable blending for better visual effects
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Set clear color (dark night sky)
        glClearColor(0.05, 0.05, 0.1, 1.0)

        # Setup perspective projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, 1200 / 800, 0.1, 1000.0)

    def create_ground_mesh(self):
        """Create a mesh for the ground plane"""
        self.ground_vertices = []
        self.ground_normals = []
        self.ground_indices = []

        # Create grid of vertices
        for i in range(self.ground_resolution + 1):
            for j in range(self.ground_resolution + 1):
                x = (i / self.ground_resolution - 0.5) * self.ground_size
                z = (j / self.ground_resolution - 0.5) * self.ground_size
                y = 0.0

                # Add small random perturbations for surface roughness
                noise_scale = 0.02
                y += noise_scale * (np.random.random() - 0.5)

                self.ground_vertices.extend([x, y, z])
                self.ground_normals.extend([0.0, 1.0, 0.0])  # Up normal

        # Create triangle indices
        for i in range(self.ground_resolution):
            for j in range(self.ground_resolution):
                # Two triangles per quad
                v0 = i * (self.ground_resolution + 1) + j
                v1 = v0 + 1
                v2 = v0 + (self.ground_resolution + 1)
                v3 = v2 + 1

                self.ground_indices.extend([v0, v1, v2, v1, v3, v2])

    def calculate_blinn_phong(self, position, normal, light_pos, light_color, view_pos):
        """
        Calculate Blinn-Phong shading according to Eq. 1 from the paper:
        I = ka + kd*max(0, n·l) + ks*(n·h)^s
        """
        # Normalize vectors
        light_dir = np.array(light_pos) - np.array(position)
        light_distance = np.linalg.norm(light_dir)
        light_dir = light_dir / light_distance

        view_dir = np.array(view_pos) - np.array(position)
        view_dir = view_dir / np.linalg.norm(view_dir)

        normal = np.array(normal)
        normal = normal / np.linalg.norm(normal)

        # Half-angle vector (Eq. 2 from paper: h = (v + l) / ||v + l||)
        half_vector = light_dir + view_dir
        half_vector = half_vector / np.linalg.norm(half_vector)

        # Blinn-Phong terms
        ambient = self.material['ambient']

        diffuse = self.material['diffuse'] * max(0.0, np.dot(normal, light_dir))

        specular_factor = max(0.0, np.dot(normal, half_vector))
        specular = self.material['specular'] * (specular_factor ** self.material['shininess'])

        # Distance attenuation
        attenuation = 1.0 / (1.0 + 0.01 * light_distance + 0.001 * light_distance * light_distance)

        # Combine components
        intensity = ambient + (diffuse + specular) * attenuation

        return [intensity * c for c in light_color]

    def render_ground(self):
        """Render the ground plane with specular streaks"""
        glBegin(GL_TRIANGLES)

        vertices = np.array(self.ground_vertices).reshape(-1, 3)
        normals = np.array(self.ground_normals).reshape(-1, 3)

        for i in range(0, len(self.ground_indices), 3):
            # Get triangle vertices
            v0_idx, v1_idx, v2_idx = self.ground_indices[i:i + 3]

            v0 = vertices[v0_idx]
            v1 = vertices[v1_idx]
            v2 = vertices[v2_idx]

            n0 = normals[v0_idx]
            n1 = normals[v1_idx]
            n2 = normals[v2_idx]

            # Calculate lighting for each vertex
            for vertex, normal in [(v0, n0), (v1, n1), (v2, n2)]:
                total_color = [0.0, 0.0, 0.0]

                # Accumulate lighting from all light sources
                for light in self.lights:
                    light_pos = light['pos'].copy()

                    # Animate lights if enabled
                    if self.light_animation:
                        light_pos[0] += 5.0 * math.sin(self.time * 0.5)
                        light_pos[2] += 2.0 * math.cos(self.time * 0.3)

                    color_contribution = self.calculate_blinn_phong(
                        vertex, normal, light_pos, light['color'], self.camera_pos
                    )

                    # Scale by light intensity
                    intensity_factor = light['intensity'] / 100.0
                    color_contribution = [c * intensity_factor for c in color_contribution]

                    # Add to total color
                    total_color = [total_color[i] + color_contribution[i] for i in range(3)]

                # Clamp colors to [0, 1] range
                total_color = [min(1.0, max(0.0, c)) for c in total_color]

                glColor3f(*total_color)
                glNormal3f(*normal)
                glVertex3f(*vertex)

        glEnd()

    def render_light_sources(self):
        """Render visible light sources as bright spheres"""
        for light in self.lights:
            light_pos = light['pos'].copy()

            # Animate lights if enabled
            if self.light_animation:
                light_pos[0] += 5.0 * math.sin(self.time * 0.5)
                light_pos[2] += 2.0 * math.cos(self.time * 0.3)

            glPushMatrix()
            glTranslatef(*light_pos)

            # Disable lighting for light sources themselves
            glDisable(GL_LIGHTING)
            glColor3f(*light['color'])

            # Draw sphere (simplified as octahedron for performance)
            glBegin(GL_TRIANGLES)
            # Simple octahedron vertices
            vertices = [
                [0, 1, 0], [1, 0, 0], [0, 0, 1],
                [0, 1, 0], [0, 0, 1], [-1, 0, 0],
                [0, 1, 0], [-1, 0, 0], [0, 0, -1],
                [0, 1, 0], [0, 0, -1], [1, 0, 0],
                [0, -1, 0], [0, 0, 1], [1, 0, 0],
                [0, -1, 0], [-1, 0, 0], [0, 0, 1],
                [0, -1, 0], [0, 0, -1], [-1, 0, 0],
                [0, -1, 0], [1, 0, 0], [0, 0, -1]
            ]

            for vertex in vertices:
                scaled_vertex = [v * 0.5 for v in vertex]  # Scale down
                glVertex3f(*scaled_vertex)

            glEnd()
            glEnable(GL_LIGHTING)
            glPopMatrix()

    def setup_camera(self):
        """Set up camera view matrix"""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Animate camera slightly for better viewing
        camera_offset_x = 2.0 * math.sin(self.time * 0.1)
        camera_pos = self.camera_pos + [camera_offset_x, 0, 0]

        gluLookAt(
            camera_pos[0], camera_pos[1], camera_pos[2],  # Camera position
            self.camera_target[0], self.camera_target[1], self.camera_target[2],  # Look at
            0.0, 1.0, 0.0  # Up vector
        )

    def render_frame(self):
        """Render a single frame"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.setup_camera()

        # Render ground with specular streaks
        self.render_ground()

        # Render light sources
        self.render_light_sources()

        # Update time
        self.time += 0.016  # Approximately 60 FPS

    def run(self):
        """Main simulation loop"""
        print("Specular Streak Simulation")
        print("Based on 'Specular Streaks in Stereo' by Langer & Bourque")
        print("\nControls:")
        print("- ESC: Exit")
        print("- SPACE: Toggle light animation")
        print("- R: Reset camera")
        print("\nObserve the vertically elongated highlights (specular streaks)")
        print("These represent virtual light columns beneath the surface!")

        clock = core.Clock()

        while True:
            # Handle events
            keys = event.getKeys()
            if 'escape' in keys:
                break
            elif 'space' in keys:
                self.light_animation = not self.light_animation
                print(f"Light animation: {'ON' if self.light_animation else 'OFF'}")
            elif 'r' in keys:
                self.time = 0.0
                print("Camera reset")

            # Render frame
            self.render_frame()

            # Flip buffers
            self.win.flip()

            # Control frame rate
            clock.tick(60)

        self.win.close()
        core.quit()


def main():
    """Run the specular streak simulation"""
    try:
        sim = SpecularStreakSimulation()
        sim.run()
    except Exception as e:
        print(f"Error running simulation: {e}")
        core.quit()


if __name__ == "__main__":
    main()
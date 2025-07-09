import moderngl
import numpy as np
import pygame
import math
import random
from pyrr import matrix44

good_distances_to_test = [3, 25]
good_disparities = [0.3]


class ModernGLColumnRenderer:
    def __init__(self, width=1024, height=768):
        # Initialize Pygame and OpenGL context
        pygame.init()
        pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)

        # Create ModernGL context
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.clear_color = (0.0, 0.0, 0.0, 1.0)

        self.width = width
        self.height = height

        # Camera parameters (same as original)
        self.camera_pos = np.array([0.0, 3.0, 0.0])
        self.look_at_point = np.array([0.0, 3.0, -15.0])
        self.viewing_vector = self.calculate_viewing_vector()

        # Scale calculation parameters
        self.reference_distance = 15.0
        self.reference_visual_angle_degrees = 1.5

        # Calculate checkerboard square size
        self.checkerboard_square_size = self.calculate_required_square_size()

        # Create shaders
        self.create_shaders()

        # Generate geometry
        self.generate_checkerboard_floor()
        self.generate_all_column_geometries()

        # Create vertex array objects
        self.create_vaos()

    def calculate_viewing_vector(self):
        # Use the hardcoded values from original
        vx, vy, vz = 0, -3, -15
        length = math.sqrt(vx * vx + vy * vy + vz * vz)
        return np.array([vx / length, vy / length, vz / length])

    def calculate_position_along_vector(self, distance):
        pos = self.camera_pos + distance * self.viewing_vector
        return pos

    def calculate_required_square_size(self):
        max_column_width = 0

        for distance in good_distances_to_test:
            size_factor = distance / self.reference_distance
            column_width = 0.8 * size_factor
            column_depth = 0.08 * size_factor
            max_offset = 0.04 * size_factor
            total_width = column_width + 2 * max_offset
            total_depth = column_depth + 2 * max_offset
            max_dimension = max(total_width, total_depth)
            max_column_width = max(max_column_width, max_dimension)

        required_size = max_column_width * 3.0
        nice_size = math.ceil(required_size * 2) / 2
        return nice_size

    def create_shaders(self):
        vertex_shader = '''
        #version 330

        in vec3 position;
        in vec3 normal;

        uniform mat4 mvp;

        out vec3 frag_normal;
        out vec3 frag_pos;

        void main() {
            gl_Position = mvp * vec4(position, 1.0);
            frag_normal = normal;
            frag_pos = position;
        }
        '''

        fragment_shader = '''
        #version 330

        in vec3 frag_normal;
        in vec3 frag_pos;

        uniform vec3 color;

        out vec4 fragColor;

        void main() {
            fragColor = vec4(color, 1.0);
        }
        '''

        self.program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

    def generate_checkerboard_floor(self):
        floor_size = 60.0
        square_size = self.checkerboard_square_size
        num_squares = int(floor_size / square_size) + 4

        vertices = []
        normals = []

        # Get column positions for reference
        column_positions = []
        for distance in good_distances_to_test:
            pos = self.calculate_position_along_vector(distance)
            column_positions.append((pos[0], pos[2]))

        # Grid alignment (same logic as original)
        reference_x = 0.0
        reference_z = column_positions[0][1]

        start_x = reference_x - (num_squares * square_size) / 2
        start_z = reference_z - (num_squares * square_size) / 2

        grid_offset_x = (reference_x - start_x) % square_size - square_size / 2
        grid_offset_z = (reference_z - start_z) % square_size - square_size / 2
        start_x += grid_offset_x
        start_z += grid_offset_z

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

                # Skip squares in column corridor
                is_in_column_corridor = (grid_i == column_x_grid_index)
                if is_in_column_corridor:
                    continue

                # Checkerboard pattern - only white squares
                is_white = (grid_i + grid_j) % 2 == 1
                if is_white:
                    # Two triangles per square
                    # Triangle 1
                    vertices.extend([
                        [x1, 0.0, z1], [x2, 0.0, z1], [x1, 0.0, z2]
                    ])
                    # Triangle 2
                    vertices.extend([
                        [x2, 0.0, z1], [x2, 0.0, z2], [x1, 0.0, z2]
                    ])
                    # Normals (up direction)
                    normals.extend([[0, 1, 0]] * 6)

        self.floor_vertices = np.array(vertices, dtype=np.float32)
        self.floor_normals = np.array(normals, dtype=np.float32)

    def calculate_size_for_distance(self, distance):
        return distance / self.reference_distance

    def generate_all_column_geometries(self):
        self.column_geometries = {}
        for distance in good_distances_to_test:
            self.column_geometries[distance] = self.generate_column_geometry_for_distance(distance)

    def generate_column_geometry_for_distance(self, distance_along_vector):
        vertices = []
        normals = []

        position = self.calculate_position_along_vector(distance_along_vector)
        size_factor = self.calculate_size_for_distance(distance_along_vector)

        # Base parameters
        base_total_height = 4.0
        base_brick_width = 0.8
        base_brick_depth = 0.08

        # Scaled parameters
        total_height = base_total_height * size_factor
        brick_width = base_brick_width * size_factor
        brick_depth = base_brick_depth * size_factor

        num_bricks = 80
        max_offset = 0.04 * size_factor
        brick_height = total_height / num_bricks
        missing_brick_probability = 0.1

        # Set random seed for reproducible results
        random.seed(42)

        for brick_i in range(num_bricks):
            y_top = -brick_i * brick_height
            y_bottom = -(brick_i + 1) * brick_height

            if random.random() < missing_brick_probability:
                continue

            x_offset = random.uniform(-max_offset, max_offset)
            z_offset = random.uniform(-max_offset, max_offset)

            brick_x = x_offset + position[0]
            brick_y_top = y_top + position[1]
            brick_y_bottom = y_bottom + position[1]
            brick_z = z_offset + position[2]

            x1 = brick_x - brick_width / 2
            x2 = brick_x + brick_width / 2
            z1 = brick_z - brick_depth / 2
            z2 = brick_z + brick_depth / 2

            # Add all 6 faces of the brick
            self.add_brick_faces(x1, x2, brick_y_top, brick_y_bottom, z1, z2, vertices, normals)

        return {
            'vertices': np.array(vertices, dtype=np.float32),
            'normals': np.array(normals, dtype=np.float32),
            'position': position
        }

    def add_brick_faces(self, x1, x2, y_top, y_bottom, z1, z2, vertices, normals):
        # Front face
        vertices.extend([
            [x1, y_top, z1], [x2, y_top, z1], [x2, y_bottom, z1],
            [x1, y_top, z1], [x2, y_bottom, z1], [x1, y_bottom, z1]
        ])
        normals.extend([[0, 0, 1]] * 6)

        # Back face
        vertices.extend([
            [x2, y_top, z2], [x1, y_top, z2], [x1, y_bottom, z2],
            [x2, y_top, z2], [x1, y_bottom, z2], [x2, y_bottom, z2]
        ])
        normals.extend([[0, 0, -1]] * 6)

        # Left face
        vertices.extend([
            [x1, y_top, z2], [x1, y_top, z1], [x1, y_bottom, z1],
            [x1, y_top, z2], [x1, y_bottom, z1], [x1, y_bottom, z2]
        ])
        normals.extend([[-1, 0, 0]] * 6)

        # Right face
        vertices.extend([
            [x2, y_top, z1], [x2, y_top, z2], [x2, y_bottom, z2],
            [x2, y_top, z1], [x2, y_bottom, z2], [x2, y_bottom, z1]
        ])
        normals.extend([[1, 0, 0]] * 6)

        # Top face
        vertices.extend([
            [x1, y_top, z1], [x1, y_top, z2], [x2, y_top, z2],
            [x1, y_top, z1], [x2, y_top, z2], [x2, y_top, z1]
        ])
        normals.extend([[0, 1, 0]] * 6)

        # Bottom face
        vertices.extend([
            [x1, y_bottom, z2], [x1, y_bottom, z1], [x2, y_bottom, z1],
            [x1, y_bottom, z2], [x2, y_bottom, z1], [x2, y_bottom, z2]
        ])
        normals.extend([[0, -1, 0]] * 6)

    def create_vaos(self):
        # Create VAO for floor
        if len(self.floor_vertices) > 0:
            floor_vbo = self.ctx.buffer(self.floor_vertices.tobytes())
            floor_normal_vbo = self.ctx.buffer(self.floor_normals.tobytes())
            self.floor_vao = self.ctx.vertex_array(self.program, [
                (floor_vbo, '3f', 'position'),
                (floor_normal_vbo, '3f', 'normal')
            ])
        else:
            self.floor_vao = None

        # Create VAOs for columns
        self.column_vaos = {}
        for distance, geometry in self.column_geometries.items():
            if len(geometry['vertices']) > 0:
                vbo = self.ctx.buffer(geometry['vertices'].tobytes())
                normal_vbo = self.ctx.buffer(geometry['normals'].tobytes())
                vao = self.ctx.vertex_array(self.program, [
                    (vbo, '3f', 'position'),
                    (normal_vbo, '3f', 'normal')
                ])
                self.column_vaos[distance] = vao

    def setup_camera_matrices(self):
        # Projection matrix
        aspect_ratio = self.width / self.height
        projection = matrix44.create_perspective_projection_matrix(
            math.radians(45.0), aspect_ratio, 0.1, 100.0
        )

        # View matrix (lookAt)
        up = np.array([0.0, 1.0, 0.0])
        view = matrix44.create_look_at(self.camera_pos, self.look_at_point, up)

        # Model matrix (identity)
        model = matrix44.create_identity()

        # MVP matrix
        mvp = projection @ view @ model

        return model, view, projection, mvp

    def render_frame(self):
        self.ctx.clear()

        model, view, projection, mvp = self.setup_camera_matrices()

        # Set MVP uniform
        self.program['mvp'].write(mvp.astype(np.float32).tobytes())

        # Render floor (light gray/white)
        if self.floor_vao:
            self.program['color'].value = (0.9, 0.9, 0.9)
            self.floor_vao.render()

        # Render columns (white)
        self.program['color'].value = (1.0, 1.0, 1.0)
        for distance in good_distances_to_test:
            if distance in self.column_vaos:
                self.column_vaos[distance].render()

    def run_demo(self):
        print("ModernGL Column Scene Demo")
        print("Press ESC to quit")

        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.render_frame()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


def run_moderngl_demo():
    """Run the ModernGL demo showing the exact same scene as the original PsychoPy code."""
    try:
        renderer = ModernGLColumnRenderer()
        renderer.run_demo()
    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_moderngl_demo()
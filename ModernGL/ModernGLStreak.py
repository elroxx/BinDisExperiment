import moderngl
import moderngl_window as mglw
from pyrr import Matrix44, Vector3
import numpy as np
import math


class SpecularStreakScene(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Specular Streak Demo"
    window_size = (1280, 720)
    resource_dir = '.'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.camera_pos = np.array([0.0, 5.0, 0.0], dtype='f4')

        # flat plane
        plane_size = 200
        vertices = np.array([
            -plane_size, 0.0, -plane_size,
             plane_size, 0.0, -plane_size,
            -plane_size, 0.0,  plane_size,
             plane_size, 0.0,  plane_size,
        ], dtype='f4')

        normals = np.array([
            0.0, 1.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 1.0, 0.0,
        ], dtype='f4')

        indices = np.array([0, 1, 2, 1, 2, 3], dtype='i4')

        vbo = self.ctx.buffer(vertices.tobytes())
        nbo = self.ctx.buffer(normals.tobytes())
        ibo = self.ctx.buffer(indices.tobytes())

        self.program = self.load_program(
            vertex_shader='plane.vert',
            fragment_shader='plane.frag'
        )

        self.vao = self.ctx.vertex_array(
            self.program,
            [(vbo, '3f', 'in_position'), (nbo, '3f', 'in_normal')],
            index_buffer=ibo
        )

        self.ctx.disable(moderngl.CULL_FACE)

    def on_render(self, time: float, frame_time: float):
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.clear(0.1, 0.1, 0.1)

        max_angle = math.radians(45)
        angle = max_angle * math.sin(time * 0.5) #rotation max angle

        model = Matrix44.from_z_rotation(angle) #LIGHTING IS INDEED RECOMPUTED EVERY SINGLE FRAME FOR EVERY SINGLE VECTOR

        projection = Matrix44.perspective_projection(45.0, self.wnd.aspect_ratio, 0.1, 1000.0)
        view = Matrix44.look_at(
            eye=Vector3(self.camera_pos),
            target=Vector3([0.0, 0.0, -15.0]),
            up=Vector3([0.0, 1.0, 0.0])
        )

        self.program['u_proj'].write(projection.astype('f4').tobytes())
        self.program['u_view'].write(view.astype('f4').tobytes())
        self.program['u_model'].write(model.astype('f4').tobytes())
        self.program['u_camera_pos'].value = tuple(self.camera_pos)
        self.program['u_light_pos'].value = (0.0, 30.0, -100.0)
        self.program['u_specular_power'].value = 400.0

        self.vao.render()


if __name__ == '__main__':
    mglw.run_window_config(SpecularStreakScene)

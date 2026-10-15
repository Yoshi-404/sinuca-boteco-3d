import math
import random
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from constants import (
    BALL_RADIUS,
    TABLE_WIDTH,
    TABLE_LENGTH,
    FRICTION,
)
from graphics import draw_cube


class Particle:
    """Partícula tridimensional representando giz e poeira da tacada."""
    def __init__(self, x, z, vel_x, vel_z):
        self.pos = pygame.math.Vector3(x, BALL_RADIUS, z)
        self.vel = pygame.math.Vector3(vel_x, random.uniform(0.1, 0.3), vel_z)
        self.life = 1.0
        self.color = (0.2, 0.6, 1.0)

    def update(self):
        self.pos += self.vel
        self.life -= 0.02

    def render(self):
        glColor4f(self.color[0], self.color[1], self.color[2], self.life)
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, self.pos.z)
        draw_cube(0.1)
        glPopMatrix()


class Ball:
    """Bola de sinuca com física de rolamento com rotação quaterniônica via matriz OpenGL."""
    def __init__(self, x, y, z, texture_id, radius=BALL_RADIUS, is_cue=False, is_black=False):
        self.pos = pygame.math.Vector2(x, z)
        self.vel = pygame.math.Vector2(0, 0)
        self.height = y
        self.texture_id = texture_id
        self.radius = radius
        self.is_cue = is_cue
        self.is_black = is_black
        self.spin = pygame.math.Vector2(0, 0)
        self.rot_matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

    def update(self):
        speed = self.vel.length()
        if speed > 0.001:
            axis_x, axis_z = -self.vel.y, self.vel.x
            angle = (speed / self.radius) * (180.0 / math.pi)
            glPushMatrix()
            glLoadIdentity()
            glRotatef(angle, axis_x, 0.0, axis_z)
            glMultMatrixf(self.rot_matrix)
            self.rot_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
            glPopMatrix()

        self.pos += self.vel
        self.vel *= FRICTION

        if self.vel.length() < 0.005:
            self.vel = pygame.math.Vector2(0, 0)
            self.spin *= 0.8

        # Colisões com as tabelas da mesa (com amortecimento e efeito lateral)
        if self.pos.x - self.radius < -TABLE_WIDTH / 2:
            self.pos.x = -TABLE_WIDTH / 2 + self.radius
            self.vel.x *= -0.8
            self.vel.y -= self.spin.x * 0.3
        if self.pos.x + self.radius > TABLE_WIDTH / 2:
            self.pos.x = TABLE_WIDTH / 2 - self.radius
            self.vel.x *= -0.8
            self.vel.y += self.spin.x * 0.3
        if self.pos.y - self.radius < -TABLE_LENGTH / 2:
            self.pos.y = -TABLE_LENGTH / 2 + self.radius
            self.vel.y *= -0.8
            self.vel.x -= self.spin.x * 0.3
        if self.pos.y + self.radius > TABLE_LENGTH / 2:
            self.pos.y = TABLE_LENGTH / 2 - self.radius
            self.vel.y *= -0.8
            self.vel.x += self.spin.x * 0.3

    def render(self, quadric):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glColor3fv((1.0, 1.0, 1.0))

        glPushMatrix()
        glTranslatef(self.pos.x, self.height, self.pos.y)
        glMultMatrixf(self.rot_matrix)
        glRotatef(90, 1, 0, 0)
        gluSphere(quadric, self.radius, 40, 40)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)


def create_triangle_rack(start_z, tex_list):
    """Gera a formação em triângulo clássica das 15 bolas de sinuca."""
    rack_balls = []
    tex_idx = 1
    for row in range(5):
        for col in range(row + 1):
            x_pos = (col * BALL_RADIUS * 2) - (row * BALL_RADIUS)
            z_pos = start_z + (row * BALL_RADIUS * math.sqrt(3))

            if row == 2 and col == 1:
                # Bola 8 no centro da terceira linha
                rack_balls.append(Ball(x_pos, BALL_RADIUS, z_pos, tex_list[8], is_black=True))
            else:
                rack_balls.append(Ball(x_pos, BALL_RADIUS, z_pos, tex_list[tex_idx]))
                tex_idx += 1
                if tex_idx > 7:
                    tex_idx = 1
    return rack_balls

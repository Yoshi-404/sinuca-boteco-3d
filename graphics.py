import math
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from constants import (
    WIDTH,
    HEIGHT,
    HUD_CX,
    HUD_CY,
    HUD_R,
    HUD_COLOR,
    YELLOW,
    RED,
    BALL_RADIUS,
)


def draw_cube(size):
    """Renderiza um cubo alinhado aos eixos com coordenadas de textura e normais."""
    s = size / 2.0
    glBegin(GL_QUADS)
    # Face frontal
    glNormal3f(0.0, 0.0, 1.0)
    glTexCoord2f(0, 0); glVertex3f(-s, -s, s)
    glTexCoord2f(1, 0); glVertex3f(s, -s, s)
    glTexCoord2f(1, 1); glVertex3f(s, s, s)
    glTexCoord2f(0, 1); glVertex3f(-s, s, s)
    # Face traseira
    glNormal3f(0.0, 0.0, -1.0)
    glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
    glTexCoord2f(0, 1); glVertex3f(-s, s, -s)
    glTexCoord2f(1, 1); glVertex3f(s, s, -s)
    glTexCoord2f(1, 0); glVertex3f(s, -s, -s)
    # Face superior
    glNormal3f(0.0, 1.0, 0.0)
    glTexCoord2f(0, 1); glVertex3f(-s, s, -s)
    glTexCoord2f(0, 0); glVertex3f(-s, s, s)
    glTexCoord2f(1, 0); glVertex3f(s, s, s)
    glTexCoord2f(1, 1); glVertex3f(s, s, -s)
    # Face inferior
    glNormal3f(0.0, -1.0, 0.0)
    glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
    glTexCoord2f(1, 0); glVertex3f(s, -s, -s)
    glTexCoord2f(1, 1); glVertex3f(s, -s, s)
    glTexCoord2f(0, 1); glVertex3f(-s, -s, s)
    # Face direita
    glNormal3f(1.0, 0.0, 0.0)
    glTexCoord2f(0, 0); glVertex3f(s, -s, -s)
    glTexCoord2f(0, 1); glVertex3f(s, s, -s)
    glTexCoord2f(1, 1); glVertex3f(s, s, s)
    glTexCoord2f(1, 0); glVertex3f(s, -s, s)
    # Face esquerda
    glNormal3f(-1.0, 0.0, 0.0)
    glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
    glTexCoord2f(1, 0); glVertex3f(-s, -s, s)
    glTexCoord2f(1, 1); glVertex3f(-s, s, s)
    glTexCoord2f(0, 1); glVertex3f(-s, s, -s)
    glEnd()


def draw_disk(inner, outer, slices):
    """Renderiza um disco plano ou anel circular sem dependência de GLUT."""
    if inner == 0:
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        for i in range(slices + 1):
            angle = 2 * math.pi * i / slices
            glVertex3f(outer * math.cos(angle), outer * math.sin(angle), 0)
        glEnd()
    else:
        glBegin(GL_QUAD_STRIP)
        glNormal3f(0.0, 0.0, 1.0)
        for i in range(slices + 1):
            angle = 2 * math.pi * i / slices
            c = math.cos(angle)
            s = math.sin(angle)
            glVertex3f(inner * c, inner * s, 0)
            glVertex3f(outer * c, outer * s, 0)
        glEnd()


def draw_textured_box(bx, by, bz, bw, bh, bd):
    """Posiciona e dimensiona um bloco retangular texturizado."""
    glPushMatrix()
    glTranslatef(bx, by, bz)
    glScalef(bw, bh, bd)
    draw_cube(1.0)
    glPopMatrix()


def draw_text(x, y, text, font_size=18, color=HUD_COLOR):
    """Renderiza texto bidimensional convertendo superfície Pygame em textura OpenGL."""
    color_255 = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
    pygame.font.init()
    font = pygame.font.SysFont("helvetica", font_size, bold=True)
    surf = font.render(text, True, color_255)
    w, h = surf.get_width(), surf.get_height()

    surf = pygame.transform.flip(surf, False, True)
    data = pygame.image.tostring(surf, "RGBA", True)

    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

    glEnable(GL_TEXTURE_2D)
    glColor4f(1.0, 1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x, y)
    glTexCoord2f(1, 0); glVertex2f(x + w, y)
    glTexCoord2f(1, 1); glVertex2f(x + w, y + h)
    glTexCoord2f(0, 1); glVertex2f(x, y + h)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    glDeleteTextures(1, [tex])


def draw_overlay_screen(title, subtitle, score=None, background_alpha=0.8):
    """Desenha tela de sobreposição semi-transparente para menus, pause e fim de jogo."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glColor4f(0.05, 0.05, 0.05, background_alpha)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(WIDTH, 0)
    glVertex2f(WIDTH, HEIGHT); glVertex2f(0, HEIGHT)
    glEnd()

    glColor3fv(HUD_COLOR)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(WIDTH / 2 - 200, HEIGHT / 2)
    glVertex2f(WIDTH / 2 + 200, HEIGHT / 2)
    glEnd()

    draw_text(WIDTH / 2 - len(title) * 7, HEIGHT / 2 - 50, title, 28)
    draw_text(WIDTH / 2 - len(subtitle) * 5, HEIGHT / 2 + 20, subtitle, 20)

    if score is not None:
        sc_txt = f"Pontuacao Atual: {score}"
        draw_text(WIDTH / 2 - len(sc_txt) * 6, HEIGHT / 2 + 60, sc_txt, 22, YELLOW)

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hud(spin_state, score, message=""):
    """Renderiza a interface HUD (placar, controle de spin e comandos)."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    draw_text(30, 40, f"PONTOS: {score}", 24, YELLOW)
    draw_text(30, HEIGHT - 40, "[ P ] Pausar    [ R ] Reiniciar", 16, HUD_COLOR)

    if message:
        draw_text(WIDTH / 2 - len(message) * 6, 50, message, 24, RED)

    cx, cy, r = HUD_CX, HUD_CY, HUD_R

    # Fundo do mostrador de efeito
    glColor4f(HUD_COLOR[0], HUD_COLOR[1], HUD_COLOR[2], 0.2)
    glBegin(GL_QUADS)
    glVertex2f(cx - r - 10, cy - r - 10); glVertex2f(cx + r + 10, cy - r - 10)
    glVertex2f(cx + r + 10, cy + r + 10); glVertex2f(cx - r - 10, cy + r + 10)
    glEnd()

    # Círculo externo
    glColor3fv(HUD_COLOR)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    for i in range(360):
        rad = math.radians(i)
        glVertex2f(cx + math.cos(rad) * r, cy + math.sin(rad) * r)
    glEnd()

    # Retículo central
    glBegin(GL_LINES)
    glVertex2f(cx - r, cy); glVertex2f(cx + r, cy)
    glVertex2f(cx, cy - r); glVertex2f(cx, cy + r)
    glEnd()

    # Ponto indicador de impacto do efeito (spin)
    glColor3fv(RED)
    glPointSize(8)
    glBegin(GL_POINTS)
    glVertex2f(cx + spin_state.x * r, cy - spin_state.y * r)
    glEnd()

    draw_text(cx - 55, cy + r + 20, "Arraste o Ponto", 14, HUD_COLOR)

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def mouse_to_world_plane(mouse_x, mouse_y):
    """Mapeia as coordenadas de tela 2D do mouse para a interseção no plano da mesa 3D."""
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    mouse_y = viewport[3] - mouse_y

    obj_near = gluUnProject(mouse_x, mouse_y, 0.0, modelview, projection, viewport)
    obj_far = gluUnProject(mouse_x, mouse_y, 1.0, modelview, projection, viewport)

    p_near = pygame.math.Vector3(obj_near)
    p_far = pygame.math.Vector3(obj_far)
    ray = p_far - p_near
    if ray.y == 0:
        return None
    t = (BALL_RADIUS - p_near.y) / ray.y
    intersection = p_near + ray * t
    return pygame.math.Vector2(intersection.x, intersection.z)

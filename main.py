import math
import random
import sys
import pygame
from pygame.locals import *

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("Erro: PyOpenGL ausente no sistema.")
    sys.exit(1)

from constants import (
    WIDTH,
    HEIGHT,
    TABLE_WIDTH,
    TABLE_LENGTH,
    BALL_RADIUS,
    POCKET_RADIUS,
    MAX_SHOT_POWER,
    MAX_PULL_DIST,
    MIN_PULL_DIST,
    HUD_CX,
    HUD_CY,
    HUD_R,
    WHITE,
    POCKETS,
    STATE_MENU,
    STATE_PLAYING,
    STATE_GAME_OVER,
    STATE_PAUSED,
)
from assets import (
    load_sound,
    load_music,
    load_texture,
)
from graphics import (
    draw_cube,
    draw_disk,
    draw_textured_box,
    draw_overlay_screen,
    draw_hud,
    mouse_to_world_plane,
)
from entities import (
    Particle,
    Ball,
    create_triangle_rack,
)


def reset_game(ball_textures):
    """Reinicia o estado da mesa com as bolas posicionadas e pontuação zerada."""
    balls = [Ball(0, BALL_RADIUS, -8, ball_textures[0], is_cue=True)]
    balls.extend(create_triangle_rack(4.0, ball_textures))
    return balls, balls[0], 0


def main():
    pygame.init()
    pygame.mixer.init()

    # Reproduz música instrumental de fundo na tela de menu
    load_music("start_music.mp3", 0.3)

    pygame.display.gl_set_attribute(GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(GL_MULTISAMPLESAMPLES, 4)
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Simulador de Sinuca de Boteco 3D")
    clock = pygame.time.Clock()

    # Carregamento de Texturas
    tex_wood = load_texture("madeira.jpg", (100, 50, 20))
    tex_felt = load_texture("feltro.jpg", (0, 100, 40))
    tex_floor = load_texture("chao_boteco.jpg", (200, 180, 150), is_checker=True)

    ball_textures = [load_texture(f"poolballs{i}.jpg", (255, 255, 255)) for i in range(9)]

    # Inicialização das Quádricas para esferas texturizadas
    ball_quadric = gluNewQuadric()
    gluQuadricTexture(ball_quadric, GL_TRUE)
    gluQuadricNormals(ball_quadric, GLU_SMOOTH)

    # Carregamento de Efeitos Sonoros
    snd_hit = load_sound("tacada.wav")
    snd_collide = load_sound("colisao.wav")
    snd_pocket = load_sound("encacapar.wav")

    # Configuração do Pipeline OpenGL
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glLightfv(GL_LIGHT0, GL_POSITION, (0, 30, 0, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.35, 0.3, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.85, 0.8, 1))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1))

    # Matriz de Projeção em Perspectiva
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (WIDTH / HEIGHT), 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Estado Inicial do Jogo
    game_state = STATE_MENU
    system_message = ""
    game_result_msg = ""
    balls, cue_ball, score = reset_game(ball_textures)
    particles = []

    # Câmera e Controles Interativos
    cam_dist, cam_rot_x, cam_rot_y = 40.0, 30.0, 0.0
    is_aiming, is_rotating, is_dragging_spin = False, False, False
    shot_vector = pygame.math.Vector2(0, 0)
    target_spin = pygame.math.Vector2(0, 0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Comandos de Teclado
            if event.type == pygame.KEYDOWN:
                if cue_ball.vel.length() < 0.01:
                    step = 0.2
                    if event.key == K_UP: target_spin.y = min(1.0, target_spin.y + step)
                    if event.key == K_DOWN: target_spin.y = max(-1.0, target_spin.y - step)
                    if event.key == K_RIGHT: target_spin.x = min(1.0, target_spin.x + step)
                    if event.key == K_LEFT: target_spin.x = max(-1.0, target_spin.x - step)
                    if target_spin.length() > 1.0:
                        target_spin.normalize_ip()

                if event.key == K_p:
                    if game_state == STATE_PLAYING:
                        game_state = STATE_PAUSED
                    elif game_state == STATE_PAUSED:
                        game_state = STATE_PLAYING

                if event.key == K_r and game_state in [STATE_PLAYING, STATE_PAUSED]:
                    balls, cue_ball, score = reset_game(ball_textures)
                    system_message = "Jogo Reiniciado"
                    game_state = STATE_PLAYING

            # Transições de Telas por Clique do Mouse
            if game_state == STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pygame.mixer.music.fadeout(1000)
                    game_state = STATE_PLAYING
                continue

            elif game_state == STATE_GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    balls, cue_ball, score = reset_game(ball_textures)
                    system_message = ""
                    game_state = STATE_PLAYING
                continue

            elif game_state == STATE_PAUSED:
                continue

            # Controles Durante o Jogo
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    cam_dist = max(10.0, cam_dist - 3.0)
                if event.button == 5:
                    cam_dist = min(70.0, cam_dist + 3.0)
                if event.button == 1:
                    mx, my = event.pos
                    if math.hypot(mx - HUD_CX, my - HUD_CY) <= HUD_R + 10:
                        is_dragging_spin = True
                        target_spin.x = (mx - HUD_CX) / HUD_R
                        target_spin.y = (HUD_CY - my) / HUD_R
                        if target_spin.length() > 1.0:
                            target_spin.normalize_ip()
                    elif cue_ball.vel.length() < 0.01:
                        world_mouse = mouse_to_world_plane(mx, my)
                        if world_mouse and (world_mouse - cue_ball.pos).length() < BALL_RADIUS * 4:
                            is_aiming = True
                            system_message = ""
                        else:
                            is_rotating = True
                    else:
                        is_rotating = True

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if is_dragging_spin:
                        is_dragging_spin = False
                    elif is_aiming and shot_vector.length() >= MIN_PULL_DIST:
                        cue_ball.vel = -shot_vector * MAX_SHOT_POWER * 0.05
                        cue_ball.spin = target_spin.copy()
                        snd_hit.play()

                        dir_norm = shot_vector.normalize() if shot_vector.length() > 0 else pygame.math.Vector2(0, 1)
                        for _ in range(25):
                            px = cue_ball.pos.x - dir_norm.x * BALL_RADIUS
                            pz = cue_ball.pos.y - dir_norm.y * BALL_RADIUS
                            particles.append(
                                Particle(
                                    px,
                                    pz,
                                    dir_norm.x * random.uniform(0.1, 0.5),
                                    dir_norm.y * random.uniform(0.1, 0.5),
                                )
                            )

                    is_aiming, is_rotating = False, False
                    shot_vector = pygame.math.Vector2(0, 0)

            if event.type == pygame.MOUSEMOTION:
                if is_dragging_spin:
                    mx, my = event.pos
                    target_spin.x = (mx - HUD_CX) / HUD_R
                    target_spin.y = (HUD_CY - my) / HUD_R
                    if target_spin.length() > 1.0:
                        target_spin.normalize_ip()
                elif is_rotating:
                    cam_rot_y += event.rel[0] * 0.5
                    cam_rot_x = max(1.0, min(89.0, cam_rot_x + event.rel[1] * 0.5))
                elif is_aiming:
                    world_mouse = mouse_to_world_plane(event.pos[0], event.pos[1])
                    if world_mouse:
                        shot_vector = world_mouse - cue_ball.pos
                        vl = shot_vector.length()
                        if vl > MAX_PULL_DIST:
                            shot_vector.scale_to_length(MAX_PULL_DIST)
                        elif 0.01 < vl < MIN_PULL_DIST:
                            shot_vector.scale_to_length(MIN_PULL_DIST)

        # Atualização da Física da Partida
        if game_state == STATE_PLAYING:
            for ball in balls[:]:
                for px, pz in POCKETS:
                    if (ball.pos - pygame.math.Vector2(px, pz)).length() < POCKET_RADIUS:
                        snd_pocket.play()
                        if ball.is_cue:
                            ball.pos = pygame.math.Vector2(0, -8)
                            ball.vel = pygame.math.Vector2(0, 0)
                            ball.spin = pygame.math.Vector2(0, 0)
                            score -= 20
                            system_message = "FALTA! -20 Pontos"
                        elif ball.is_black:
                            if len(balls) > 2:
                                game_result_msg = "DERROTA. Bola 8 encacapada antecipadamente."
                            else:
                                score += 50
                                game_result_msg = "VITORIA! Mesa limpa."
                            game_state = STATE_GAME_OVER
                            balls.remove(ball)
                        else:
                            score += 10
                            balls.remove(ball)
                            if len(balls) == 2:
                                system_message = "Apenas a Bola 8 restante!"
                        break

            for ball in balls:
                ball.update()

            for p in particles[:]:
                p.update()
                if p.life <= 0:
                    particles.remove(p)

            # Resolução de Colisões Elásticas entre as Bolas
            for i in range(len(balls)):
                for j in range(i + 1, len(balls)):
                    b1, b2 = balls[i], balls[j]
                    rel_pos = b2.pos - b1.pos
                    dist = rel_pos.length()

                    if dist < b1.radius + b2.radius:
                        impact_force = (b1.vel - b2.vel).length()
                        if impact_force > 0.1:
                            snd_collide.set_volume(min(1.0, impact_force * 2))
                            snd_collide.play()

                        overlap = (b1.radius + b2.radius) - dist
                        normal = rel_pos.normalize()
                        b1.pos -= normal * (overlap / 2)
                        b2.pos += normal * (overlap / 2)

                        v1_n, v2_n = b1.vel.dot(normal), b2.vel.dot(normal)
                        v1_pre_dir = b1.vel.normalize() if b1.vel.length() > 0 else pygame.math.Vector2(0, 0)

                        b1.vel += (v2_n - v1_n) * normal
                        b2.vel += (v1_n - v2_n) * normal

                        if b1.is_cue:
                            b1.vel += v1_pre_dir * (b1.spin.y * 0.1)
                            b1.spin.y *= 0.5

        # Renderização Tridimensional do Cenário
        glClearColor(0.02, 0.02, 0.03, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        ax, ay = math.radians(cam_rot_x), math.radians(cam_rot_y)
        cx = cam_dist * math.sin(ax) * math.cos(ay)
        cy = max(BALL_RADIUS * 2, cam_dist * math.cos(ax))
        cz = cam_dist * math.sin(ax) * math.sin(ay)

        if game_state in [STATE_MENU, STATE_PAUSED]:
            cam_rot_y += 0.2
            ay_rad = math.radians(cam_rot_y)
            cx = 50.0 * math.sin(math.radians(30)) * math.cos(ay_rad)
            cy = 30.0
            cz = 50.0 * math.sin(math.radians(30)) * math.sin(ay_rad)

        gluLookAt(cx, cy, cz, 0, 0, 0, 0, 1, 0)
        glEnable(GL_LIGHTING)

        # 1. Chão Texturizado
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_floor)
        glColor3fv((0.6, 0.6, 0.6))
        glMaterialfv(GL_FRONT, GL_SPECULAR, (0.0, 0.0, 0.0, 1))
        glBegin(GL_QUADS)
        floor_size = 100.0
        floor_y = -20.0
        glTexCoord2f(0, 0); glVertex3f(-floor_size, floor_y, -floor_size)
        glTexCoord2f(8, 0); glVertex3f(floor_size, floor_y, -floor_size)
        glTexCoord2f(8, 8); glVertex3f(floor_size, floor_y, floor_size)
        glTexCoord2f(0, 8); glVertex3f(-floor_size, floor_y, floor_size)
        glEnd()
        glDisable(GL_TEXTURE_2D)

        # 2. Sombra da Mesa
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.6)
        glPushMatrix()
        glTranslatef(1.5, floor_y + 0.1, 1.5)
        glScalef(TABLE_WIDTH + 6.0, 0.01, TABLE_LENGTH + 6.0)
        draw_cube(1.0)
        glPopMatrix()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

        # 3. Superfície de Feltro da Mesa
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_felt)
        glColor3fv(WHITE)
        glNormal3f(0, 1, 0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-TABLE_WIDTH / 2, 0, -TABLE_LENGTH / 2)
        glTexCoord2f(1, 0); glVertex3f(TABLE_WIDTH / 2, 0, -TABLE_LENGTH / 2)
        glTexCoord2f(1, 1); glVertex3f(TABLE_WIDTH / 2, 0, TABLE_LENGTH / 2)
        glTexCoord2f(0, 1); glVertex3f(-TABLE_WIDTH / 2, 0, TABLE_LENGTH / 2)
        glEnd()

        # 4. Bordas e Pernas de Madeira
        glBindTexture(GL_TEXTURE_2D, tex_wood)
        border_h, border_w = BALL_RADIUS * 1.5, 2.0
        draw_textured_box(0, border_h / 2, -TABLE_LENGTH / 2 - border_w / 2, TABLE_WIDTH + border_w * 2, border_h, border_w)
        draw_textured_box(0, border_h / 2, TABLE_LENGTH / 2 + border_w / 2, TABLE_WIDTH + border_w * 2, border_h, border_w)
        draw_textured_box(-TABLE_WIDTH / 2 - border_w / 2, border_h / 2, 0, border_w, border_h, TABLE_LENGTH)
        draw_textured_box(TABLE_WIDTH / 2 + border_w / 2, border_h / 2, 0, border_w, border_h, TABLE_LENGTH)

        leg_w = 2.0
        leg_h = 20.0
        leg_y = -10.01
        dx = TABLE_WIDTH / 2 - leg_w / 2
        dz = TABLE_LENGTH / 2 - leg_w / 2
        draw_textured_box(-dx, leg_y, -dz, leg_w, leg_h, leg_w)
        draw_textured_box(dx, leg_y, -dz, leg_w, leg_h, leg_w)
        draw_textured_box(-dx, leg_y, dz, leg_w, leg_h, leg_w)
        draw_textured_box(dx, leg_y, dz, leg_w, leg_h, leg_w)
        glDisable(GL_TEXTURE_2D)

        # 5. Caçapas
        glDisable(GL_LIGHTING)
        glColor3fv((0.05, 0.05, 0.05))
        for px, pz in POCKETS:
            glPushMatrix()
            glTranslatef(px, 0.1, pz)
            glRotatef(90, 1, 0, 0)
            draw_disk(0, POCKET_RADIUS, 30)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(px, 0.1, pz)
            glColor3fv((0.15, 0.15, 0.15))
            glRotatef(90, 1, 0, 0)
            draw_disk(POCKET_RADIUS, POCKET_RADIUS + 0.2, 30)
            glColor3fv((0.05, 0.05, 0.05))
            glPopMatrix()

        # 6. Sombras das Bolas no Feltro
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.6)
        for ball in balls:
            glPushMatrix()
            glTranslatef(ball.pos.x - 0.2, 0.12, ball.pos.y - 0.2)
            glRotatef(90, 1, 0, 0)
            draw_disk(0, ball.radius, 15)
            glPopMatrix()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

        # 7. Sistema de Partículas (Pó de Giz)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        for p in particles:
            p.render()
        glDisable(GL_BLEND)

        # 8. Renderização das Bolas Texturizadas
        glEnable(GL_LIGHTING)
        glMaterialfv(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, 1))
        glMaterialf(GL_FRONT, GL_SHININESS, 80.0)
        for ball in balls:
            ball.render(ball_quadric)

        # 9. Linha de Mira do Taco
        if is_aiming and game_state == STATE_PLAYING:
            glDisable(GL_LIGHTING)
            glLineWidth(3)
            intensity = (shot_vector.length() - MIN_PULL_DIST) / (MAX_PULL_DIST - MIN_PULL_DIST)
            glColor3fv((1.0, 1.0 - intensity, 1.0 - intensity))
            glBegin(GL_LINES)
            glVertex3f(cue_ball.pos.x, cue_ball.height, cue_ball.pos.y)
            glVertex3f(cue_ball.pos.x + shot_vector.x, cue_ball.height, cue_ball.pos.y + shot_vector.y)
            glEnd()
            glEnable(GL_LIGHTING)

        # 10. Camada Bidimensional de Interface (HUD / Menus)
        if game_state == STATE_MENU:
            draw_overlay_screen("SIMULADOR DE BOTECO 3D", "[ Clique para Iniciar ]")
        elif game_state == STATE_GAME_OVER:
            draw_overlay_screen(game_result_msg, "[ Clique para Reiniciar ]", score)
        elif game_state == STATE_PAUSED:
            draw_overlay_screen("JOGO PAUSADO", "[ P ] Continuar   |   [ R ] Reiniciar", score, background_alpha=0.6)
        elif game_state == STATE_PLAYING:
            draw_hud(target_spin, score, system_message)

        pygame.display.flip()
        clock.tick(60)

    gluDeleteQuadric(ball_quadric)
    pygame.quit()


if __name__ == '__main__':
    main()
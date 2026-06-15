import sys
import pygame
from pygame.locals import *
import math
import random

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
except ImportError:
    print("Erro: PyOpenGL/GLUT ausentes.")
    quit()

# --- Configurações Básicas ---
WIDTH, HEIGHT = 1280, 720
TABLE_WIDTH, TABLE_LENGTH = 15.0, 30.0
BALL_RADIUS = 0.5
POCKET_RADIUS = 0.9

MAX_SHOT_POWER = 1.2
MAX_PULL_DIST = 15.0
MIN_PULL_DIST = 2.0
FRICTION = 0.992

# Variáveis do HUD Interativo
HUD_CX = WIDTH - 100
HUD_CY = 100
HUD_R = 50

# Cores e Constantes
FELT_GREEN = (0.0, 0.4, 0.15)
WHITE = (1.0, 1.0, 1.0)
RED = (0.8, 0.1, 0.1)
YELLOW = (0.9, 0.7, 0.0)
BLACK = (0.1, 0.1, 0.1)
WOOD_BROWN = (0.3, 0.15, 0.05)
HUD_COLOR = (0.8, 0.75, 0.6)

POCKETS = [
    (-TABLE_WIDTH/2, -TABLE_LENGTH/2), (TABLE_WIDTH/2, -TABLE_LENGTH/2),
    (-TABLE_WIDTH/2, TABLE_LENGTH/2), (TABLE_WIDTH/2, TABLE_LENGTH/2),
    (-TABLE_WIDTH/2, 0), (TABLE_WIDTH/2, 0)
]

# Nova Máquina de Estados (Incluindo PAUSE)
STATE_MENU, STATE_PLAYING, STATE_GAME_OVER, STATE_PAUSED = 0, 1, 2, 3

# --- Carregadores Seguros (Fallbacks) ---
class DummySound:
    def play(self): pass
    def set_volume(self, v): pass

def load_sound(filename):
    try:
        return pygame.mixer.Sound(filename)
    except:
        return DummySound()

def load_texture(filename, fallback_color, is_checker=False):
    try:
        img = pygame.image.load(filename)
        img_surface = img.convert_alpha()
        img_data = pygame.image.tostring(img_surface, "RGBA", True)
        gl_format = GL_RGBA
    except:
        img_surface = pygame.Surface((128, 128), pygame.SRCALPHA)
        img_surface.fill(fallback_color + (255,))
        if is_checker:
            pygame.draw.rect(img_surface, (20, 20, 20, 255), (0, 0, 64, 64))
            pygame.draw.rect(img_surface, (20, 20, 20, 255), (64, 64, 64, 64))
        img_data = pygame.image.tostring(img_surface, "RGBA", True)
        gl_format = GL_RGBA

    w, h = img_surface.get_width(), img_surface.get_height()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    
    gluBuild2DMipmaps(GL_TEXTURE_2D, 4, w, h, gl_format, GL_UNSIGNED_BYTE, img_data)
    return tex_id

# --- Classes de Engenharia ---
class Particle:
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
        glutSolidCube(0.1) 
        glPopMatrix()

class Ball:
    def __init__(self, x, y, z, texture_id, radius=BALL_RADIUS, is_cue=False, is_black=False):
        self.pos = pygame.math.Vector2(x, z) 
        self.vel = pygame.math.Vector2(0, 0)
        self.height = y 
        self.texture_id = texture_id
        self.radius = radius
        self.is_cue = is_cue
        self.is_black = is_black
        self.spin = pygame.math.Vector2(0, 0)
        self.rot_matrix = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

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

        if self.pos.x - self.radius < -TABLE_WIDTH/2:
            self.pos.x = -TABLE_WIDTH/2 + self.radius
            self.vel.x *= -0.8
            self.vel.y -= self.spin.x * 0.3 
        if self.pos.x + self.radius > TABLE_WIDTH/2:
            self.pos.x = TABLE_WIDTH/2 - self.radius
            self.vel.x *= -0.8
            self.vel.y += self.spin.x * 0.3
        if self.pos.y - self.radius < -TABLE_LENGTH/2:
            self.pos.y = -TABLE_LENGTH/2 + self.radius
            self.vel.y *= -0.8
            self.vel.x -= self.spin.x * 0.3
        if self.pos.y + self.radius > TABLE_LENGTH/2:
            self.pos.y = TABLE_LENGTH/2 - self.radius
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

# --- Funções Gráficas 2D e Auxiliares ---
def draw_text(x, y, text, font=GLUT_BITMAP_9_BY_15, color=HUD_COLOR):
    glColor3fv(color)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))

def draw_overlay_screen(title, subtitle, score=None, background_alpha=0.8):
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
    glVertex2f(WIDTH/2 - 200, HEIGHT/2)
    glVertex2f(WIDTH/2 + 200, HEIGHT/2)
    glEnd()

    draw_text(WIDTH/2 - len(title)*4.5, HEIGHT/2 - 20, title, GLUT_BITMAP_HELVETICA_18)
    draw_text(WIDTH/2 - len(subtitle)*4.5, HEIGHT/2 + 30, subtitle)
    
    if score is not None:
        sc_txt = f"Pontuacao Atual: {score}"
        draw_text(WIDTH/2 - len(sc_txt)*4.5, HEIGHT/2 + 80, sc_txt, color=YELLOW)

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hud(spin_state, score, message=""):
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

    draw_text(30, 40, f"PONTOS: {score}", GLUT_BITMAP_HELVETICA_18, YELLOW)
    
    # Comandos de teclado exibidos sutilmente na tela
    draw_text(30, HEIGHT - 40, "[ P ] Pausar    [ R ] Reiniciar", GLUT_BITMAP_HELVETICA_12, HUD_COLOR)
    
    if message:
        draw_text(WIDTH/2 - len(message)*4.5, 50, message, GLUT_BITMAP_HELVETICA_18, RED)

    cx, cy, r = HUD_CX, HUD_CY, HUD_R

    glColor4f(HUD_COLOR[0], HUD_COLOR[1], HUD_COLOR[2], 0.2)
    glBegin(GL_QUADS)
    glVertex2f(cx-r-10, cy-r-10); glVertex2f(cx+r+10, cy-r-10)
    glVertex2f(cx+r+10, cy+r+10); glVertex2f(cx-r-10, cy+r+10)
    glEnd()

    glColor3fv(HUD_COLOR)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    for i in range(360):
        glVertex2f(cx + math.cos(math.radians(i))*r, cy + math.sin(math.radians(i))*r)
    glEnd()

    glBegin(GL_LINES)
    glVertex2f(cx-r, cy); glVertex2f(cx+r, cy)
    glVertex2f(cx, cy-r); glVertex2f(cx, cy+r)
    glEnd()

    glColor3fv(RED)
    glPointSize(8)
    glBegin(GL_POINTS)
    glVertex2f(cx + spin_state.x * r, cy - spin_state.y * r) 
    glEnd()

    draw_text(cx - 55, cy + r + 20, "Arraste o Ponto", GLUT_BITMAP_HELVETICA_10, HUD_COLOR)

    glDisable(GL_BLEND) 
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def mouse_to_world_plane(mouse_x, mouse_y):
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    mouse_y = viewport[3] - mouse_y

    obj_near = gluUnProject(mouse_x, mouse_y, 0.0, modelview, projection, viewport)
    obj_far = gluUnProject(mouse_x, mouse_y, 1.0, modelview, projection, viewport)

    p_near = pygame.math.Vector3(obj_near)
    p_far = pygame.math.Vector3(obj_far)
    ray = p_far - p_near
    if ray.y == 0: return None 
    t = (BALL_RADIUS - p_near.y) / ray.y
    intersection = p_near + ray * t
    return pygame.math.Vector2(intersection.x, intersection.z)

def create_triangle_rack(start_z, tex_list):
    rack_balls = []
    tex_idx = 1 
    for row in range(5):
        for col in range(row + 1):
            x_pos = (col * BALL_RADIUS * 2) - (row * BALL_RADIUS)
            z_pos = start_z + (row * BALL_RADIUS * math.sqrt(3))
            
            if row == 2 and col == 1:
                rack_balls.append(Ball(x_pos, BALL_RADIUS, z_pos, tex_list[8], is_black=True))
            else:
                rack_balls.append(Ball(x_pos, BALL_RADIUS, z_pos, tex_list[tex_idx]))
                tex_idx += 1
                if tex_idx > 7: tex_idx = 1 
    return rack_balls

# --- Loop Principal ---
def main():
    pygame.init()
    pygame.mixer.init() 
    
    # Música de Fundo (Apenas no Menu Inicial)
    try:
        pygame.mixer.music.load("start_music.mp3")
        pygame.mixer.music.set_volume(0.3) 
        pygame.mixer.music.play(-1) 
    except Exception as e:
        print("Aviso: Música start_music.mp3 não encontrada.")

    pygame.display.gl_set_attribute(GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(GL_MULTISAMPLESAMPLES, 4)
    
    glutInit(sys.argv)
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF|OPENGL)
    pygame.display.set_caption("Motor de Sinuca")
    clock = pygame.time.Clock()

    # Carrega Texturas
    tex_wood = load_texture("madeira.jpg", (100, 50, 20))
    tex_felt = load_texture("feltro.jpg", (0, 100, 40))
    tex_floor = load_texture("chao_boteco.jpg", (200, 180, 150), is_checker=True)

    ball_textures = []
    for i in range(9):
        tex = load_texture(f"poolballs{i}.jpg", (255, 255, 255))
        ball_textures.append(tex)

    ball_quadric = gluNewQuadric()
    gluQuadricTexture(ball_quadric, GL_TRUE)
    gluQuadricNormals(ball_quadric, GLU_SMOOTH)

    snd_hit = load_sound("tacada.wav")
    snd_collide = load_sound("colisao.wav")
    snd_pocket = load_sound("encacapar.wav")

    glEnable(GL_DEPTH_TEST) 
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0) 
    glEnable(GL_COLOR_MATERIAL) 
    
    glLightfv(GL_LIGHT0, GL_POSITION,  (0, 30, 0, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.35, 0.3, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.85, 0.8, 1))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1))

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (WIDTH / HEIGHT), 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    game_state = STATE_MENU
    score = 0
    system_message = ""
    game_result_msg = ""
    
    balls = [Ball(0, BALL_RADIUS, -8, ball_textures[0], is_cue=True)] 
    balls.extend(create_triangle_rack(4.0, ball_textures))
    cue_ball = balls[0]
    particles = []

    cam_dist, cam_rot_x, cam_rot_y = 40.0, 30.0, 0.0  
    is_aiming, is_rotating, is_dragging_spin = False, False, False
    shot_vector = pygame.math.Vector2(0,0)
    target_spin = pygame.math.Vector2(0,0) 

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            # --- Sistema de Atalhos e Teclado ---
            if event.type == pygame.KEYDOWN:
                # Comandos do Efeito (Spin)
                if cue_ball.vel.length() < 0.01:
                    step = 0.2
                    if event.key == K_UP: target_spin.y = min(1.0, target_spin.y + step)
                    if event.key == K_DOWN: target_spin.y = max(-1.0, target_spin.y - step)
                    if event.key == K_RIGHT: target_spin.x = min(1.0, target_spin.x + step)
                    if event.key == K_LEFT: target_spin.x = max(-1.0, target_spin.x - step)
                    if target_spin.length() > 1.0: target_spin.normalize_ip()
                
                # Comando de Pausa [ P ]
                if event.key == K_p:
                    if game_state == STATE_PLAYING:
                        game_state = STATE_PAUSED
                    elif game_state == STATE_PAUSED:
                        game_state = STATE_PLAYING

                # Comando de Restart [ R ]
                if event.key == K_r and game_state in [STATE_PLAYING, STATE_PAUSED]:
                    balls = [Ball(0, BALL_RADIUS, -8, ball_textures[0], is_cue=True)]
                    balls.extend(create_triangle_rack(4.0, ball_textures))
                    cue_ball = balls[0]
                    score = 0
                    system_message = "Jogo Reiniciado"
                    game_state = STATE_PLAYING

            # --- Lógica de Transição de Telas ---
            if game_state == STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pygame.mixer.music.fadeout(1000) # Música desliga suavemente em 1s
                    game_state = STATE_PLAYING
                continue 

            elif game_state == STATE_GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    balls = [Ball(0, BALL_RADIUS, -8, ball_textures[0], is_cue=True)]
                    balls.extend(create_triangle_rack(4.0, ball_textures))
                    cue_ball = balls[0]
                    score = 0
                    system_message = ""
                    game_state = STATE_PLAYING
                continue

            elif game_state == STATE_PAUSED:
                continue # Trava comandos de mouse se estiver pausado

            # --- Controles do Jogo (Apenas no estado PLAYING) ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: cam_dist = max(10.0, cam_dist - 3.0)
                if event.button == 5: cam_dist = min(70.0, cam_dist + 3.0)
                if event.button == 1:
                    mx, my = event.pos
                    if math.hypot(mx - HUD_CX, my - HUD_CY) <= HUD_R + 10:
                        is_dragging_spin = True
                        target_spin.x = (mx - HUD_CX) / HUD_R
                        target_spin.y = (HUD_CY - my) / HUD_R
                        if target_spin.length() > 1.0: target_spin.normalize_ip()
                    elif cue_ball.vel.length() < 0.01:
                        world_mouse = mouse_to_world_plane(mx, my)
                        if world_mouse and (world_mouse - cue_ball.pos).length() < BALL_RADIUS * 4:
                            is_aiming = True
                            system_message = "" 
                        else: is_rotating = True
                    else: is_rotating = True 

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if is_dragging_spin:
                        is_dragging_spin = False
                    elif is_aiming and shot_vector.length() >= MIN_PULL_DIST:
                        cue_ball.vel = -shot_vector * MAX_SHOT_POWER * 0.05
                        cue_ball.spin = target_spin.copy()
                        snd_hit.play() 
                        
                        dir_norm = shot_vector.normalize() if shot_vector.length()>0 else pygame.math.Vector2(0,1)
                        for _ in range(25):
                            px = cue_ball.pos.x - dir_norm.x * BALL_RADIUS
                            pz = cue_ball.pos.y - dir_norm.y * BALL_RADIUS
                            particles.append(Particle(px, pz, dir_norm.x * random.uniform(0.1,0.5), dir_norm.y * random.uniform(0.1,0.5)))
                            
                    is_aiming, is_rotating = False, False
                    shot_vector = pygame.math.Vector2(0,0) 

            if event.type == pygame.MOUSEMOTION:
                if is_dragging_spin:
                    mx, my = event.pos
                    target_spin.x = (mx - HUD_CX) / HUD_R
                    target_spin.y = (HUD_CY - my) / HUD_R
                    if target_spin.length() > 1.0: target_spin.normalize_ip()
                elif is_rotating:
                    cam_rot_y += event.rel[0] * 0.5
                    cam_rot_x = max(1.0, min(89.0, cam_rot_x + event.rel[1] * 0.5))
                elif is_aiming:
                    world_mouse = mouse_to_world_plane(event.pos[0], event.pos[1])
                    if world_mouse:
                        shot_vector = world_mouse - cue_ball.pos
                        vl = shot_vector.length()
                        if vl > MAX_PULL_DIST: shot_vector.scale_to_length(MAX_PULL_DIST)
                        elif vl > 0.01 and vl < MIN_PULL_DIST: shot_vector.scale_to_length(MIN_PULL_DIST)

        # Atualiza a física apenas se o jogo estiver rodando
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
                            if len(balls) == 2: system_message = "Apenas a Bola 8 restante!"
                        break

            for ball in balls: ball.update()
            
            for p in particles[:]:
                p.update()
                if p.life <= 0: particles.remove(p)

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
                        v1_pre_dir = b1.vel.normalize() if b1.vel.length() > 0 else pygame.math.Vector2(0,0)
                        
                        b1.vel += (v2_n - v1_n) * normal
                        b2.vel += (v1_n - v2_n) * normal
                        
                        if b1.is_cue:
                            b1.vel += v1_pre_dir * (b1.spin.y * 0.1)
                            b1.spin.y *= 0.5 

        # --- Renderização 3D ---
        glClearColor(0.02, 0.02, 0.03, 1.0) 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        ax, ay = math.radians(cam_rot_x), math.radians(cam_rot_y)
        cx, cy, cz = cam_dist * math.sin(ax) * math.cos(ay), max(BALL_RADIUS * 2, cam_dist * math.cos(ax)), cam_dist * math.sin(ax) * math.sin(ay)
        
        # Câmera cinemática no Menu Principal ou Pausa
        if game_state in [STATE_MENU, STATE_PAUSED]:
            cam_rot_y += 0.2
            cx, cy, cz = 50.0 * math.sin(math.radians(30)) * math.cos(math.radians(cam_rot_y)), 30.0, 50.0 * math.sin(math.radians(30)) * math.sin(math.radians(cam_rot_y))
            
        gluLookAt(cx, cy, cz,  0, 0, 0,  0, 1, 0)

        glEnable(GL_LIGHTING)
        
        # 1. Chão
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

        # 1.5 Sombra da Mesa
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.6)
        glPushMatrix()
        glTranslatef(1.5, floor_y + 0.1, 1.5) 
        glScalef(TABLE_WIDTH + 6.0, 0.01, TABLE_LENGTH + 6.0)
        glutSolidCube(1.0)
        glPopMatrix()
        glDisable(GL_BLEND)

        # 2. Mesa (Feltro)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_felt)
        glColor3fv(WHITE) 
        glNormal3f(0, 1, 0) 
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-TABLE_WIDTH/2, 0, -TABLE_LENGTH/2)
        glTexCoord2f(1, 0); glVertex3f(TABLE_WIDTH/2, 0, -TABLE_LENGTH/2)
        glTexCoord2f(1, 1); glVertex3f(TABLE_WIDTH/2, 0, TABLE_LENGTH/2)
        glTexCoord2f(0, 1); glVertex3f(-TABLE_WIDTH/2, 0, TABLE_LENGTH/2)
        glEnd()

        # 3. Bordas e Pernas
        glBindTexture(GL_TEXTURE_2D, tex_wood)
        border_h, border_w = BALL_RADIUS * 1.5, 2.0               
        def draw_textured_box(bx, by, bz, bw, bh, bd):
            glPushMatrix()
            glTranslatef(bx, by, bz)
            glScalef(bw, bh, bd)
            glutSolidCube(1.0)
            glPopMatrix()

        draw_textured_box(0, border_h/2, -TABLE_LENGTH/2 - border_w/2, TABLE_WIDTH + border_w*2, border_h, border_w) 
        draw_textured_box(0, border_h/2, TABLE_LENGTH/2 + border_w/2, TABLE_WIDTH + border_w*2, border_h, border_w)  
        draw_textured_box(-TABLE_WIDTH/2 - border_w/2, border_h/2, 0, border_w, border_h, TABLE_LENGTH)              
        draw_textured_box(TABLE_WIDTH/2 + border_w/2, border_h/2, 0, border_w, border_h, TABLE_LENGTH)               
        
        leg_w = 2.0
        leg_h = 20.0
        leg_y = -10.01 
        dx = TABLE_WIDTH/2 - leg_w/2
        dz = TABLE_LENGTH/2 - leg_w/2
        draw_textured_box(-dx, leg_y, -dz, leg_w, leg_h, leg_w)
        draw_textured_box(dx, leg_y, -dz, leg_w, leg_h, leg_w)
        draw_textured_box(-dx, leg_y, dz, leg_w, leg_h, leg_w)
        draw_textured_box(dx, leg_y, dz, leg_w, leg_h, leg_w)
        glDisable(GL_TEXTURE_2D)

        # 4. Caçapas
        glColor3fv(BLACK)
        quad = gluNewQuadric()
        for px, pz in POCKETS:
            glPushMatrix()
            glTranslatef(px, 0.01, pz) 
            glRotatef(90, 1, 0, 0) 
            gluDisk(quad, 0, POCKET_RADIUS, 30, 1)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(px, 0.01, pz)
            glColor3fv((0.1, 0.1, 0.1)) 
            glMaterialfv(GL_FRONT, GL_SPECULAR, (0.0, 0.0, 0.0, 1)) 
            glScalef(1.0, 0.25, 1.0) 
            glRotatef(90, 1, 0, 0) 
            glutSolidTorus(0.2, POCKET_RADIUS, 15, 30) 
            glPopMatrix()

        # 5. Sombras das Bolas
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.6) 
        for ball in balls:
            glPushMatrix()
            glTranslatef(ball.pos.x - 0.2, 0.02, ball.pos.y - 0.2)
            glScalef(1.0, 0.001, 1.0)
            glutSolidSphere(ball.radius, 15, 15)
            glPopMatrix()
        glDisable(GL_BLEND)

        # 6. Partículas
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        for p in particles: p.render()
        glDisable(GL_BLEND)

        # 7. Bolas 
        glEnable(GL_LIGHTING)
        glMaterialfv(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, 1))
        glMaterialf(GL_FRONT, GL_SHININESS, 80.0)
        for ball in balls: 
            ball.render(ball_quadric)

        # 8. Mira do Taco
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

        # Telas 2D
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
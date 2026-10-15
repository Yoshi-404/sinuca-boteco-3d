import os
import sys
import pygame
from OpenGL.GL import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(filename):
    """Localiza arquivos de assets no diretório assets/, raiz ou empacotamento PyInstaller."""
    # Ambiente empacotado pelo PyInstaller
    if getattr(sys, '_MEIPASS', False):
        candidate_assets = os.path.join(sys._MEIPASS, 'assets', filename)
        if os.path.exists(candidate_assets):
            return candidate_assets
        candidate_root = os.path.join(sys._MEIPASS, filename)
        if os.path.exists(candidate_root):
            return candidate_root

    # Ambiente de desenvolvimento / execução direta
    candidate_assets = os.path.join(BASE_DIR, 'assets', filename)
    if os.path.exists(candidate_assets):
        return candidate_assets

    candidate_root = os.path.join(BASE_DIR, filename)
    if os.path.exists(candidate_root):
        return candidate_root

    return os.path.join('assets', filename)


class DummySound:
    """Fallback seguro para quando áudios não puderem ser carregados."""
    def play(self):
        pass

    def set_volume(self, v):
        pass


def load_sound(filename):
    """Carrega efeito sonoro com fallback seguro."""
    path = get_asset_path(filename)
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return DummySound()


def load_music(filename, volume=0.3):
    """Carrega e inicia música de fundo com fallback seguro."""
    path = get_asset_path(filename)
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
        return True
    except Exception:
        return False


def load_texture(filename, fallback_color, is_checker=False):
    """Carrega textura de imagem e envia para o contexto OpenGL com suporte a mipmapping."""
    path = get_asset_path(filename)
    try:
        img = pygame.image.load(path)
        img_surface = img.convert_alpha()
        img_data = pygame.image.tostring(img_surface, "RGBA", True)
        gl_format = GL_RGBA
    except Exception:
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

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    # GL_GENERATE_MIPMAP (0x8191) para evitar crash de gluBuild2DMipmaps no Windows 64-bit
    try:
        glTexParameteri(GL_TEXTURE_2D, 0x8191, GL_TRUE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, gl_format, GL_UNSIGNED_BYTE, img_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    except Exception:
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, gl_format, GL_UNSIGNED_BYTE, img_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    return tex_id

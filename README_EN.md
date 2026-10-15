# 3D Brazilian Bar Pool Simulator (Sinuca de Boteco)

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-green.svg)](https://www.pygame.org/)
[![PyOpenGL](https://img.shields.io/badge/PyOpenGL-3.1%2B-red.svg)](https://pyopengl.sourceforge.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build & Release](https://github.com/Yoshi-404/Pool_Game/actions/workflows/build.yml/badge.svg)](https://github.com/Yoshi-404/Pool_Game/actions)

> **Language switch**: [Versão em Português](README.md)

**Student**: Yan Yoshinori Arakaki  
**Academic ID (RGA)**: 20210712196401  
**Course**: Computer Graphics — UFGD / Computer Engineering  

---

## Visual Demonstration

![Game Demonstration](docs/screenshots/gameplay.gif)

*Full view of the textured billiard table featuring Phong illumination, projected shadows, ball rolling physics, and interactive HUD.*

![Aiming Line Screenshot](docs/screenshots/screenshot.png)

---

## 1. Project Description and Motivation

The **3D Brazilian Bar Pool Simulator** is an interactive three-dimensional environment built using Python, Pygame, and PyOpenGL. The scene captures the nostalgic ambiance of a classic Brazilian bar billiard table:

- Handcrafted table geometry featuring textured green felt, polished wood borders and table legs, and multi-layered pockets.
- Checkerboard retro floor with surface texturing, diffuse, and specular lighting.
- Pool balls rendered as quadric spheres under the **Phong reflection model** (ambient, diffuse, and specular highlights with tuned shininess).
- Custom physics engine with sphere rolling, quaternion-based ball spin rotation, elastic ball-ball collisions, and cushion bounce damping.
- Real-time cue ball spin adjustment (**English / Spin**).
- 3D particle system simulating chalk dust dispersed from cue impact.
- Sound effects for cue hits, collisions, and ball potting, with an introductory background soundtrack in the menu.

### Academic Background

This project represents a complete reimagining and technical leap from the author's final project developed while studying abroad at **Wakayama University in Japan**.

The preliminary version was rudimentary: it relied entirely on an orthogonal camera (yielding a flat table with no depth cues), lacked 3D pockets, and had basic visual effects.

This definitive version showcases advanced Computer Graphics concepts:
- **Depth Illusion for Pockets**: Concentric multi-pass circular disks utilizing depth testing (Z-buffer).
- **Interactive Perspective Camera**: Spherical orbit around the table and scroll-wheel zoom.
- **2D HUD Overlay Layer**: Clean vector graphic interface for spin manipulation and score tracking.
- **Mipmapping and Anti-Aliasing**: Automatic mipmap generation avoiding Moiré artifacts on the floor and balls.
- **Modular Codebase Architecture**: Clean separation between constants, asset loading, graphics primitives, entities, and the game loop.

---

## 2. Technologies and Libraries

- **[Python](https://www.python.org/) (3.10+)**: Core programming language.
- **[Pygame](https://www.pygame.org/)**: Window management, event processing (mouse and keyboard), 60 FPS timing, and audio playback.
- **[PyOpenGL](https://pyopengl.sourceforge.net/) (`GL`, `GLU`)**: Hardware-accelerated 3D rendering pipeline, matrix transformations, spherical quadrics, normal vectors, and lighting.
- **[PyInstaller](https://pyinstaller.org/)**: Standalone Windows binary generation (.exe) via GitHub Actions CI/CD workflows.

---

## 3. Mathematical Justification of Projections

This application strategically combines two distinct OpenGL projection models:

### Perspective Projection (`gluPerspective`)
Applied to the entire 3D virtual world (table, balls, chalk particles, and floor).
- **Justification**: Perspective delivers realistic *foreshortening* (objects appear smaller as distance increases), an essential visual cue in billiards for accurate perception of ball distances, aim angles, and shot power.

### Orthographic Projection (`gluOrtho2D`)
Reserved strictly for the user interface layer (score overlay, interactive spin widget, pause screen, and game-over dialogs).
- **Justification**: Two-dimensional HUD elements must remain pixel-stable on screen, completely independent of the 3D camera's position and orientation.

---

## 4. Controls

| Control | Action |
| :--- | :--- |
| **Mouse (Left Click & Drag - Table)** | Click and pull backward from the cue ball to set aim direction and shot power. Release to shoot. |
| **Mouse (Free Movement)** | Orbits the camera around the pool table. |
| **Mouse Wheel (Scroll)** | Zoom in and zoom out. |
| **HUD (Top-Right Widget)** | Click and drag the red dot to apply spin (English) to the cue ball. |
| **Arrow Keys (Keyboard)** | Fine-tune spin offset on the cue ball. |
| **Key `[ P ]`** | Pause and resume the active match. |
| **Key `[ R ]`** | Reset the table (re-racks the balls and resets score). |

---

## 5. Repository Structure

```text
pinball_game/
├── .github/
│   └── workflows/
│       └── build.yml          # CI/CD: Automated Windows build and GitHub Releases
├── assets/
│   ├── README.md              # Asset catalog and provenance notes
│   ├── chao_boteco.jpg        # Checkerboard bar floor texture
│   ├── feltro.jpg             # Green table felt texture
│   ├── madeira.jpg            # Polished wood texture
│   ├── poolballs[0-8].jpg     # Billiard ball textures (0 to 8)
│   ├── start_music.mp3        # Menu soundtrack
│   └── tacada.wav             # Cue strike sound effect
├── docs/
│   └── screenshots/           # Documentation media (animated GIF and screenshot)
├── assets.py                  # Resilient asset, texture, and audio loading
├── constants.py               # Table dimensions, physics limits, colors, and game states
├── entities.py                # Ball physics & rotation, Particle system, and Triangle rack
├── graphics.py                # OpenGL drawing primitives, HUD, and ray unprojection
├── main.py                    # Main game loop, event dispatcher, and render pass
├── requirements.txt           # Python package requirements
├── CREDITS.md                 # Media provenance, licensing, and attribution details
├── LICENSE                    # MIT License
├── README.md                  # Documentation in Portuguese
└── README_EN.md               # Documentation in English
```

---

## 6. Installation and Running

### Option A: Run from Source (Python)

1. Clone the repository:
   ```bash
   git clone https://github.com/Yoshi-404/Pool_Game.git
   cd Pool_Game
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   ```

3. Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```

4. Launch the simulator:
   ```bash
   python main.py
   ```

### Option B: Download Windows Executable (.exe)

Pre-built binaries are available through GitHub Releases:
1. Navigate to the **[Releases](https://github.com/Yoshi-404/Pool_Game/releases)** page.
2. Download the latest `.zip` archive (`Simulador-Boteco-3D-Windows.zip`).
3. Extract the contents and double-click `Simulador-Boteco-3D.exe`.

---

## 7. Media Origins and Licensing

All textures and audio tracks comply with permissive licensing terms, detailed in [CREDITS.md](CREDITS.md):

| Asset | Source / Origin | License / Terms |
| :--- | :--- | :--- |
| `assets/feltro.jpg` | AI-generated (OpenAI ChatGPT / DALL-E 3, C2PA verified) | OpenAI Terms of Use / Educational |
| `assets/madeira.jpg` | AI-generated (OpenAI ChatGPT / DALL-E 3, C2PA verified) | OpenAI Terms of Use / Educational |
| `assets/chao_boteco.jpg` | AI-generated (OpenAI ChatGPT / DALL-E 3, C2PA verified) | OpenAI Terms of Use / Educational |
| `assets/poolballs*.jpg` | Textured with GIMP | Public Domain / MIT License |
| `assets/tacada.wav` | Recorded by Russ Garrett (Freesound #2103) | [CC Sampling+ 1.0](https://creativecommons.org/licenses/sampling+/1.0/) / CC BY 3.0 |
| `assets/start_music.mp3` | Composed in FL Studio 11 (2014, 140 BPM) | Royalty-Free / Non-commercial |

---

## 8. License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

from pathlib import Path
import sys
import traceback

# Mostrar el error aunque se ejecute el archivo haciendo doble clic.
def mostrar_error(tipo, valor, traza):
    detalle = ''.join(traceback.format_exception(tipo, valor, traza))
    print(detalle, file=sys.stderr)
    try:
        Path(__file__).resolve().with_name('error_arcade.txt').write_text(
            detalle, encoding='utf-8'
        )
    except OSError:
        pass
    try:
        from tkinter import Tk, messagebox
        raiz = Tk()
        raiz.withdraw()
        messagebox.showerror('Error de ARCADE', str(valor) +
                             '\n\nConsulta la consola o error_arcade.txt.')
        raiz.destroy()
    except Exception:
        pass

sys.excepthook = mostrar_error

try:
    import pygame
except ModuleNotFoundError as exc:
    if exc.name == 'pygame':
        raise RuntimeError('Pygame no está instalado en este Python. Ejecuta: python -m pip install pygame') from exc
    raise

pygame.init()

# Fuentes para mensajes y contador
font = pygame.font.Font(None, 72)
font_small = pygame.font.Font(None, 36)

# Ajustes generales
win_width = 800
win_height = 600
left_bound = win_width // 40
right_bound = win_width - 8 * left_bound
gravedad = 0.25
salto = -9
h_width = 65
h_height = 90
FPS = 60

# Nuevas reglas
TOTAL_NIVELES = 3
TIEMPO_MAXIMO = 180  # 3 minutos para completar los tres niveles
MAX_VIDAS = 3

# Archivos de imágenes originales
img_file_back = 'cave.jpg'
img_file_hero = 'hero.png'
img_file_enemy = 'enemy.png'
img_file_bomb = 'bomb.png'
img_file_princess = 'princess.png'

# Colores
C_BLACK = (0, 0, 0)
C_RED = (255, 0, 0)
C_GREEN = (32, 128, 32)
C_WHITE = (255, 255, 255)
C_YELLOW = (255, 220, 70)

# Ventana y fondo
pygame.display.set_caption('ARCADE' )
window = pygame.display.set_mode((win_width, win_height))
# Buscar imágenes junto al archivo .py y en la carpeta de trabajo.
CARPETA_JUEGO = Path(__file__).resolve().parent
imagenes_faltantes = set()
cache_imagenes = {}


def cargar_imagen(nombre, width, height, transparente=True):
    clave = (nombre, width, height, transparente)
    if clave in cache_imagenes:
        return cache_imagenes[clave]

    for ruta in (CARPETA_JUEGO / nombre, Path.cwd() / nombre):
        if ruta.is_file():
            try:
                imagen = pygame.image.load(str(ruta))
                imagen = imagen.convert_alpha() if transparente else imagen.convert()
                imagen = pygame.transform.scale(imagen, (width, height))
                cache_imagenes[clave] = imagen
                return imagen
            except (pygame.error, OSError) as error:
                print(f'No se pudo cargar {ruta}: {error}')

    # Si falta una imagen, usar una figura temporal para que el juego no se cierre.
    imagenes_faltantes.add(nombre)
    print(f'AVISO: No se pudo cargar {nombre}. Se usará una figura temporal.')
    imagen = pygame.Surface((width, height), pygame.SRCALPHA if transparente else 0)
    if nombre == img_file_back:
        imagen.fill((29, 35, 48))
    else:
        colores = {
            img_file_hero: (65, 150, 245),
            img_file_enemy: (215, 60, 60),
            img_file_bomb: (230, 150, 35),
            img_file_princess: (220, 100, 190)
        }
        pygame.draw.rect(imagen, colores.get(nombre, C_WHITE), imagen.get_rect(), border_radius=8)
        etiqueta = pygame.font.Font(None, 20).render(Path(nombre).stem[:8], True, C_BLACK)
        imagen.blit(etiqueta, etiqueta.get_rect(center=imagen.get_rect().center))
    cache_imagenes[clave] = imagen
    return imagen


back = cargar_imagen(img_file_back, win_width, win_height, False)


# Clase de la princesa y las bombas
class FinalSprite(pygame.sprite.Sprite):
    def __init__(self, player_image, player_x, player_y,
                 width=60, height=120):
        super().__init__()
        self.image = cargar_imagen(player_image, width, height)
        self.rect = self.image.get_rect(topleft=(player_x, player_y))


# Clase del héroe
class Hero(pygame.sprite.Sprite):
    def __init__(self, filename, x, y, width, height):
        super().__init__()
        self.image = cargar_imagen(filename, width, height)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.x_speed = 0
        self.y_speed = 0
        self.y = float(y)  # Guarda decimales para una gravedad suave
        self.stands_on = False
        self.barriers = None

    def gravitate(self):
        self.y_speed += gravedad

    def jump(self, y):
        if self.stands_on:
            self.y_speed = y
            self.stands_on = False

    def update(self):
        # Movimiento horizontal y colisiones con muros
        self.rect.x += self.x_speed
        platforms_touched = pygame.sprite.spritecollide(
            self, self.barriers, False
        )
        if platforms_touched:
            if self.x_speed > 0:
                self.rect.right = min(p.rect.left for p in platforms_touched)
            elif self.x_speed < 0:
                self.rect.left = max(p.rect.right for p in platforms_touched)

        # Gravedad y movimiento vertical
        self.gravitate()
        self.y += self.y_speed
        self.rect.y = round(self.y)

        # Colisiones verticales con plataformas y suelo
        platforms_touched = pygame.sprite.spritecollide(
            self, self.barriers, False
        )
        if platforms_touched:
            if self.y_speed > 0:
                self.rect.bottom = min(p.rect.top for p in platforms_touched)
            elif self.y_speed < 0:
                self.rect.top = max(p.rect.bottom for p in platforms_touched)
            self.y_speed = 0
            self.y = float(self.rect.y)

        # Comprueba si hay suelo justo debajo del héroe
        self.stands_on = self.y_speed >= 0 and any(
            self.rect.move(0, 1).colliderect(p.rect) for p in self.barriers
        )
        if self.stands_on:
            self.y_speed = 0
            self.y = float(self.rect.y)


# Clase de plataformas
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=C_GREEN):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))


# Clase de enemigos
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, min_x, max_x,
                 filename=img_file_enemy, width=70, height=70, speed=3):
        super().__init__()
        self.image = cargar_imagen(filename, width, height)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.min_x = min_x
        self.max_x = max_x
        self.speed = speed

    def update(self):
        # Patrulla de izquierda a derecha
        self.rect.x += self.speed
        if self.rect.x <= self.min_x:
            self.rect.x = self.min_x
            self.speed = abs(self.speed)
        elif self.rect.x >= self.max_x:
            self.rect.x = self.max_x
            self.speed = -abs(self.speed)


# Cada nivel tiene un mapa, enemigos, bombas y velocidad diferentes.
# Plataformas: (x, y, ancho, alto)
# Enemigos: (x, y, límite izquierdo, límite derecho)
# Bombas: (x, y)
NIVELES = {
    1: {
        'ancho': 1450,
        'plataformas': [
            (0, 590, 1450, 20),
            (200, 470, 130, 20),
            (470, 430, 140, 20),
            (1050, 470, 120, 20)
        ],
        'enemigos': [(390, 520, 350, 500), (1160, 520, 1160, 1210)],
        'bombas': [(840, 540)],
        'velocidad': 2
    },
    2: {
        'ancho': 2500,
        'plataformas': [
            (0, 590, 1050, 20),
            (1170, 590, 1330, 20),
            (105, 470, 100, 20),
            (1245, 450, 100, 20)
        ],
        # Patrullas cortas, con suelo y espacio libre para saltar.
        'enemigos': [(330, 520, 300, 370),
                     (1490, 520, 1450, 1520),
                     (2240, 520, 2200, 2270)],
        # Bombas fuera de las patrullas y de los bordes del vacío.
        'bombas': [(720, 540), (1780, 540)],
        'velocidad': 3
    },
    3: {
        'ancho': 3650,
        'plataformas': [
            (0, 590, 1000, 20),
            (1125, 590, 1355, 20),
            (2610, 590, 1040, 20),
            (105, 470, 90, 20),
            (1155, 450, 90, 20),
            (2630, 450, 90, 20)
        ],
        # Mayor dificultad, pero cada peligro deja una zona de aterrizaje.
        'enemigos': [(350, 520, 320, 400),
                     (1400, 520, 1370, 1450),
                     (2110, 520, 2080, 2160),
                     (3190, 520, 3150, 3230)],
        'bombas': [(690, 540), (1790, 540), (2850, 540)],
        'velocidad': 4
    }
}


# Crear o reiniciar únicamente el nivel indicado
def crear_partida(nivel):
    datos = NIVELES[nivel]
    all_sprites = pygame.sprite.Group()
    barriers = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bombs = pygame.sprite.Group()

    # Crear plataformas
    for wall in datos['plataformas']:
        w = Wall(*wall)
        barriers.add(w)
        all_sprites.add(w)

    # Crear héroe sobre el suelo
    robin = Hero(img_file_hero, 20, 590 - h_height, h_width, h_height)
    robin.barriers = barriers
    robin.stands_on = True
    all_sprites.add(robin)

    # Crear enemigos
    for enemy_pos in datos['enemigos']:
        en = Enemy(*enemy_pos, speed=datos['velocidad'])
        enemies.add(en)
        all_sprites.add(en)

    # Crear bombas
    for x, y in datos['bombas']:
        bomb = FinalSprite(img_file_bomb, x, y, 50, 50)
        bombs.add(bomb)
        all_sprites.add(bomb)

    # La princesa marca la meta de cada nivel
    pr = FinalSprite(img_file_princess, datos['ancho'] - 100, 470)
    all_sprites.add(pr)

    return all_sprites, barriers, enemies, bombs, robin, pr


# Iniciar partida
nivel = 1
vidas = MAX_VIDAS
all_sprites, barriers, enemies, bombs, robin, pr = crear_partida(nivel)
run = True
finished = False
resultado = ''
camera = 0
clock = pygame.time.Clock()
inicio = pygame.time.get_ticks()

while run:
    clock.tick(FPS)

    # Procesar eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and not finished:
                robin.jump(salto)

            # R reinicia todos los niveles, vidas y tiempo
            elif event.key == pygame.K_r and finished:
                nivel = 1
                vidas = MAX_VIDAS
                all_sprites, barriers, enemies, bombs, robin, pr = crear_partida(nivel)
                finished = False
                resultado = ''
                camera = 0
                inicio = pygame.time.get_ticks()

    # Cronómetro general de tres minutos (no se reinicia al cambiar de nivel)
    transcurrido = (pygame.time.get_ticks() - inicio) // 1000
    tiempo_restante = max(0, TIEMPO_MAXIMO - transcurrido)

    # Actualizar el juego
    if not finished:
        if tiempo_restante == 0:
            resultado = 'tiempo'
            finished = True
        else:
            # Leer las flechas para mover al personaje
            keys = pygame.key.get_pressed()
            robin.x_speed = 5 * (int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT]))
            all_sprites.update()

            # Impedir que el héroe salga por los bordes del mapa
            ancho_mundo = NIVELES[nivel]['ancho']
            robin.rect.x = max(0, min(robin.rect.x, ancho_mundo - robin.rect.width))

            # Cámara lateral, sin modificar las posiciones reales de los objetos
            if robin.rect.x - camera > right_bound:
                camera = robin.rect.x - right_bound
            elif robin.rect.x - camera < left_bound:
                camera = robin.rect.x - left_bound
            camera = max(0, min(camera, ancho_mundo - win_width))

            # Perder una vida al tocar enemigos, bombas o caer en un vacío
            golpe = (pygame.sprite.spritecollide(robin, enemies, False)
                     or pygame.sprite.spritecollide(robin, bombs, False)
                     or robin.rect.top > win_height)

            if golpe:
                vidas -= 1
                if vidas <= 0:
                    robin.kill()
                    resultado = 'perdiste'
                    finished = True
                else:
                    # Reaparecer al inicio del nivel, conservando el tiempo
                    all_sprites, barriers, enemies, bombs, robin, pr = crear_partida(nivel)
                    camera = 0

            # Llegar a la princesa permite pasar al siguiente nivel
            elif pygame.sprite.collide_rect(robin, pr):
                if nivel < TOTAL_NIVELES:
                    nivel += 1
                    all_sprites, barriers, enemies, bombs, robin, pr = crear_partida(nivel)
                    camera = 0
                else:
                    resultado = 'ganaste'
                    finished = True

    # Dibujar el fondo continuo
    local_shift = (-camera) % win_width
    window.blit(back, (local_shift, 0))
    window.blit(back, (local_shift - win_width, 0))

    # Dibujar cada objeto teniendo en cuenta la cámara
    for sprite in all_sprites:
        window.blit(sprite.image, (sprite.rect.x - camera, sprite.rect.y))

    # Marcador: nivel, vidas y tiempo restante
    pygame.draw.rect(window, C_BLACK, (0, 0, win_width, 42))
    minutos, segundos = divmod(tiempo_restante, 60)
    texto_nivel = font_small.render(f'Nivel: {nivel}/{TOTAL_NIVELES}', True, C_WHITE)
    texto_vidas = font_small.render(f'Vidas: {vidas}', True, C_RED)
    color_tiempo = C_RED if tiempo_restante <= 30 else C_YELLOW
    texto_tiempo = font_small.render(f'Tiempo: {minutos:02d}:{segundos:02d}', True, color_tiempo)
    window.blit(texto_nivel, (15, 8))
    window.blit(texto_vidas, (315, 8))
    window.blit(texto_tiempo, (585, 8))

    # Pantalla final
    if finished:
        window.fill(C_BLACK)
        if resultado == 'ganaste':
            text = font.render('¡GANASTE!', True, C_GREEN)
        elif resultado == 'tiempo':
            text = font.render('¡SE ACABÓ EL TIEMPO!', True, C_RED)
        else:
            text = font.render('JUEGO TERMINADO', True, C_RED)
        window.blit(text, text.get_rect(center=(win_width // 2, win_height // 2 - 70)))

        resumen = font_small.render(f'Nivel: {nivel}/{TOTAL_NIVELES}   Vidas: {vidas}', True, C_WHITE)
        window.blit(resumen, resumen.get_rect(center=(win_width // 2, win_height // 2)))
        reiniciar = font_small.render('Presiona R para reiniciar', True, C_WHITE)
        window.blit(reiniciar, reiniciar.get_rect(center=(win_width // 2, win_height // 2 + 50)))

    # Informar si se están usando imágenes temporales.
    if imagenes_faltantes and not finished:
        aviso = pygame.font.Font(None, 22).render(
            'Faltan imágenes: revisa la consola y la carpeta del juego.', True, C_YELLOW
        )
        window.blit(aviso, (15, 46))

    pygame.display.update()

pygame.quit()

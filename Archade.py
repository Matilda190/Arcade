
import pygame
from random import randint

pygame.init()

# Fuente
font = pygame.font.Font(None, 72)

# Ajustes generales
win_width = 800
win_height = 600
left_bound = win_width / 40
right_bound = win_width - 8 * left_bound
gravedad = 0.25
salto = -9
x_start, y_start = 20, 10
h_width = 65
h_height = 90
FPS = 60

# Archivos de imágenes
img_file_back = 'cave.png'
img_file_hero = 'hero.png'
img_file_enemy = 'enemy.png'
img_file_bomb = 'bomb.png'
img_file_princess = 'princess.png'

# Colores
C_BLACK = (0, 0, 0)
C_RED = (255, 0, 0)
C_GREEN = (32, 128, 32)

# Ventana
pygame.display.set_caption('ARCADE')
window = pygame.display.set_mode((win_width, win_height))

back = pygame.transform.scale(
    pygame.image.load(img_file_back).convert(),
    (win_width, win_height)
)


# Clase de la princesa y objetos
class FinalSprite(pygame.sprite.Sprite):
    def __init__(self, player_image, player_x, player_y,
                 width=60, height=120):
        super().__init__()
        self.image = pygame.transform.scale(
            pygame.image.load(player_image).convert_alpha(),
            (width, height)
        )
        self.rect = self.image.get_rect(
            topleft=(player_x, player_y)
        )


# Clase del héroe
class Hero(pygame.sprite.Sprite):
    def __init__(self, filename, x, y, width, height):
        super().__init__()
        self.image = pygame.transform.scale(
            pygame.image.load(filename).convert_alpha(),
            (width, height)
        )
        self.rect = self.image.get_rect(topleft=(x, y))
        self.x_speed = 0
        self.y_speed = 0
        self.stands_on = False
        self.barriers = None

    def gravitate(self):
        self.y_speed += gravedad

    def jump(self, y):
        if self.stands_on:
            self.y_speed = y
            self.stands_on = False

    def update(self):
        # Movimiento horizontal
        self.rect.x += self.x_speed

        platforms_touched = pygame.sprite.spritecollide(
            self, self.barriers, False
        )

        for p in platforms_touched:
            if self.x_speed > 0:
                self.rect.right = p.rect.left
            elif self.x_speed < 0:
                self.rect.left = p.rect.right

        # Gravedad
        self.gravitate()
        self.rect.y += self.y_speed

        # Colisiones verticales
        platforms_touched = pygame.sprite.spritecollide(
            self, self.barriers, False
        )

        self.stands_on = False

        if self.y_speed > 0:
            for p in platforms_touched:
                self.y_speed = 0
                self.rect.bottom = p.rect.top
                self.stands_on = True

        elif self.y_speed < 0:
            for p in platforms_touched:
                self.y_speed = 0
                self.rect.top = p.rect.bottom


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
                 filename=img_file_enemy, width=100, height=100):
        super().__init__()
        self.image = pygame.transform.scale(
            pygame.image.load(filename).convert_alpha(),
            (width, height)
        )
        self.rect = self.image.get_rect(topleft=(x, y))
        self.min_x = min_x
        self.max_x = max_x
        self.speed = 3

    def update(self):
        self.rect.x += self.speed

        if self.rect.x <= self.min_x:
            self.rect.x = self.min_x
            self.speed = abs(self.speed)

        elif self.rect.x >= self.max_x:
            self.rect.x = self.max_x
            self.speed = -abs(self.speed)


# Crear o reiniciar la partida
def crear_partida():
    all_sprites = pygame.sprite.Group()
    barriers = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bombs = pygame.sprite.Group()

    # Héroe
    robin = Hero(
        img_file_hero, x_start, y_start, h_width, h_height
    )
    robin.barriers = barriers
    all_sprites.add(robin)

    # Plataformas
    for wall in [
        (50, 150, 480, 20),
        (700, 50, 50, 360),
        (350, 380, 640, 20),
        (-200, 590, 1600, 20)
    ]:
        w = Wall(*wall)
        barriers.add(w)
        all_sprites.add(w)

    # Enemigos
    for enemy_pos in [
        (50, 480, 20, 200),
        (400, 480, 300, 500)
    ]:
        en = Enemy(*enemy_pos)
        all_sprites.add(en)
        enemies.add(en)

    # Bomba
    bomb = FinalSprite(img_file_bomb, 550, 220, 60, 60)
    bombs.add(bomb)
    all_sprites.add(bomb)

    # Princesa
    pr = FinalSprite(
        img_file_princess,
        win_width + 500,
        win_height - 150
    )
    all_sprites.add(pr)

    return all_sprites, barriers, enemies, bombs, robin, pr


# Iniciar partida
all_sprites, barriers, enemies, bombs, robin, pr = crear_partida()

run = True
finished = False
resultado = ""
shift = 0

clock = pygame.time.Clock()

while run:
    clock.tick(FPS)

    # Eventos
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            run = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_LEFT and not finished:
                robin.x_speed = -5

            elif event.key == pygame.K_RIGHT and not finished:
                robin.x_speed = 5

            elif event.key == pygame.K_UP and not finished:
                robin.jump(salto)

            elif event.key == pygame.K_r and finished:
                all_sprites, barriers, enemies, bombs, robin, pr = crear_partida()
                finished = False
                resultado = ""
                shift = 0

        elif event.type == pygame.KEYUP:

            if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                robin.x_speed = 0

    # Actualizar el juego
    if not finished:
        all_sprites.update()

        # Movimiento de cámara
        desplazamiento = 0

        if robin.rect.x > right_bound:
            desplazamiento = robin.rect.x - right_bound
            robin.rect.x = int(right_bound)

        elif robin.rect.x < left_bound and robin.x_speed < 0:
            desplazamiento = robin.rect.x - left_bound
            robin.rect.x = int(left_bound)

        if desplazamiento != 0:
            shift -= desplazamiento

            for s in all_sprites:
                if s != robin:
                    s.rect.x -= desplazamiento

            # Ajustar límites de patrulla
            for en in enemies:
                en.min_x -= desplazamiento
                en.max_x -= desplazamiento

        # Colisiones con enemigos
        if pygame.sprite.spritecollide(robin, enemies, False):
            robin.kill()
            resultado = "perdiste"
            finished = True

        # Colisiones con bombas
        if pygame.sprite.spritecollide(robin, bombs, False):
            robin.kill()
            resultado = "perdiste"
            finished = True

        # Victoria
        if not finished and pygame.sprite.collide_rect(robin, pr):
            resultado = "ganaste"
            finished = True

        # Caer fuera de la pantalla
        if not finished and robin.rect.top > win_height:
            robin.kill()
            resultado = "perdiste"
            finished = True

    # Dibujar fondo continuo
    local_shift = int(shift % win_width)

    window.blit(back, (local_shift, 0))
    window.blit(back, (local_shift - win_width, 0))

    # Dibujar personajes y plataformas
    all_sprites.draw(window)

    # Pantalla final
    if finished:
        window.fill(C_BLACK)

        if resultado == "ganaste":
            text = font.render("¡GANASTE!", True, C_GREEN)
        else:
            text = font.render("JUEGO TERMINADO", True, C_RED)

        text_rect = text.get_rect(
            center=(win_width // 2, win_height // 2 - 30)
        )
        window.blit(text, text_rect)

        font_small = pygame.font.Font(None, 36)
        reiniciar = font_small.render(
            "Presiona R para reiniciar",
            True,
            (255, 255, 255)
        )

        reiniciar_rect = reiniciar.get_rect(
            center=(win_width // 2, win_height // 2 + 40)
        )
        window.blit(reiniciar, reiniciar_rect)

    pygame.display.update()

pygame.quit()




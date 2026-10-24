win_wi


img_file_back = 'cave.png'
img_file_hero = 'hero.png'
img_file_enemy = 'enemy.png'
img_file_bomb = 'bomb.png'
img_file_princess = 'princess.png'

C_BLACK = (0, 0, 0)
C_RED = (255, 0, 0)
C_GREEN = (32, 128, 32)

pygame.display.set_caption('ARCADE')
window = pygame.display.set_mode([win_width, win_height])
back = pygame.transform.scale(pygame.image.load(img_file_back).convert(), (win_width, win_height))

e(pygame.sprite.Sprite)
(self, player_image, player_x, player_y):
__init__(self, player_image, player_x, player_y)

Class FinalSprite(pygame.sprite.Sprite):
    def __init__(self, player_image, player_x, player_y):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load(player_image), (60, 120))
        self.rect = self.image.get_rect(topleft=(player_x, player_y))

Class Hero(pygame.sprite.Sprite):
    def__init__(self, filename, x, y, width, height):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load(filename), (width, height, convert_alpha))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.x_speed = 0
        self.y_speed = 0
        self.stands_on = False

    def gravitate(self):
        self.y_speed += gravedad

    def jump(self, y):
        # Comprobamos si nos encontramos sobre una plataforma para brincar
        if self.stands_on:
            self.y_speed = y

    def update(self):
        self.rect.x += self.x_speed
        platforms_touched = pygame.sprite.spritecollide(self. barriers, False)
        for p in platforms_touched:
            if self.x_speed > 0:
                self.rect.right = min(self.rect.right, p.rect.left)
            elif self.x_speed < 0:
                self.rect.left = max(self.rect.left, p.rect.right)
        self.gravitate()
        self.rect.y += self.y_speed
        platforms_touched = pygame.Sprite.spritecollide(self, barries, False)
        if self.y_speed > 0:
            for p in platforms_touched:
                if p.rect.top < self.rect.bottom:
                    self.y_speed = 0
                    self.rect.bottom = p.rect.top
                    self.stands_on = p
        elif self.y_speed < 0:
            self.stands_on = False
            for p in platforms_touched:
                self.y_speed = 0
                self.rect.top = max(self.rect.top, p.rect.bottom)
                
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color = C_GREEN):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, min_x, max_x, filename=img_file_enemy, width=100, height=100)
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load(filename), (width, heught)).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.min_x = min_x
        self.max_x = max_x
        self.speed = 3

            

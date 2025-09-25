import pygame
import random
import math
import json
import sys, os

def resource_path(relative_path):
    """Retourne le chemin absolu d'une ressource, compatible avec PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS  # dossier temporaire créé par PyInstaller
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === BLOC PYINSTALLER / DEBUG ===
# Permet de lancer le jeu en .exe avec toutes les ressources dans le même dossier
try:
    # Redirige les erreurs vers la console (visible dans PyInstaller)
    import traceback
except:
    pass


pygame.init()

# === CONST ===
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

PLAYER_SPEED = 5
BULLET_SPEED = 10
ENEMY_SPEED_MIN, ENEMY_SPEED_MAX = 2, 5
ENEMY_SPAWN_CHANCE = 0.02
SPECIAL_SPAWN_CHANCE = 0.001

DATA_FILE = resource_path("stats.json")

# === INIT ===
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# === CHARGEMENT MUSIQUE DE FOND ===
MUSIC_FILE = resource_path("Musique.mp3")
if os.path.exists(MUSIC_FILE):
    try:
        pygame.mixer.music.load(MUSIC_FILE)
        pygame.mixer.music.set_volume(0.5)  # volume initial 50%
        pygame.mixer.music.play(-1)
    except:
        print("Erreur chargement musique")

# === SONS ===
damage_sound = None
degat_path = resource_path("Degat.mp3")
if os.path.exists(degat_path):
    try:
        damage_sound = pygame.mixer.Sound(degat_path)
    except:
        print("Erreur chargement Degat.mp3")

# === GESTION DES STATS ===
def load_stats():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"high_score": 0, "last_score": 0, "bubbles_destroyed": 0, "bullets_missed": 0, "play_time": 0}


def save_stats(stats):
    with open(DATA_FILE, "w") as f:
        json.dump(stats, f)


def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"


stats = load_stats()

# === CLASSES ===
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        img = pygame.image.load(resource_path("Perso.png")).convert_alpha()
        self.image = pygame.transform.scale(img, (70, 55))  # joueur plus grand
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 60))
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = PLAYER_SPEED
        self.shot_cooldown = 250
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed
        if keys[pygame.K_SPACE]:
            self.shoot()

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shot_cooldown:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 12))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.speedy = -BULLET_SPEED

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            stats["bullets_missed"] += 1
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        size = random.randint(30, 60)  # minimum augmenté
        img = pygame.image.load(resource_path("Boules.png")).convert_alpha()
        self.image = pygame.transform.scale(img, (size, size))
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), -size))
        self.mask = pygame.mask.from_surface(self.image)
        self.speedy = random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        self.points = size // 2

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()


class Bubble(pygame.sprite.Sprite):
    def __init__(self, all_sprites, specials):
        super().__init__()
        self.all_sprites = all_sprites
        self.specials = specials
        self.size = 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (self.size // 2, self.size // 2), self.size // 2, 2)
        x = random.randint(self.size // 2, WIDTH - self.size // 2)
        self.rect = self.image.get_rect(center=(x, -self.size))
        self.mask = pygame.mask.from_surface(self.image)
        self.speedy = 2
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 3000

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.explode()

    def explode(self):
        for angle in range(0, 360, 30):
            p = BubbleProjectile(self.rect.centerx, self.rect.centery, angle)
            self.all_sprites.add(p)
            self.specials.add(p)
        self.kill()


class BubbleProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.Surface((6, 6))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        speed = 5
        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.right < 0 or self.rect.left > WIDTH or
                self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()


# === MENUS ===
def draw_text(surface, text, size, x, y, color=WHITE):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)


def menu():
    selected = 0
    options = ["Jouer", "Options", "Quitter"]
    while True:
        screen.fill(BLACK)
        draw_text(screen, "JEU PARFAIT", 64, WIDTH // 2, HEIGHT // 4)
        for i, option in enumerate(options):
            color = RED if i == selected else WHITE
            draw_text(screen, option, 40, WIDTH // 2, HEIGHT // 2 + i * 60, color)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == "Jouer":
                        game_loop()
                    elif options[selected] == "Options":
                        options_menu()
                    elif options[selected] == "Quitter":
                        pygame.quit()
                        exit()


def options_menu():
    selected = 0
    options = ["Sons", "Scores", "Retour"]
    while True:
        screen.fill(BLACK)
        draw_text(screen, "Options", 60, WIDTH // 2, HEIGHT // 4)
        for i, option in enumerate(options):
            color = RED if i == selected else WHITE
            draw_text(screen, option, 40, WIDTH // 2, HEIGHT // 2 + i * 60, color)
        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == "Sons":
                        sound_menu()
                    elif options[selected] == "Scores":
                        scores_menu()
                    elif options[selected] == "Retour":
                        return


def sound_menu():
    volume = pygame.mixer.music.get_volume()
    while True:
        screen.fill(BLACK)
        draw_text(screen, f"Volume : {int(volume*100)}%", 50, WIDTH // 2, HEIGHT // 2)
        draw_text(screen, "Flèches Gauche/Droite pour ajuster", 30, WIDTH // 2, HEIGHT // 2 + 50)
        draw_text(screen, "Entrée pour Retour", 30, WIDTH // 2, HEIGHT // 2 + 100)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    volume = max(0, volume - 0.1)
                    pygame.mixer.music.set_volume(volume)
                elif event.key == pygame.K_RIGHT:
                    volume = min(1, volume + 0.1)
                    pygame.mixer.music.set_volume(volume)
                elif event.key == pygame.K_RETURN:
                    return


def scores_menu():
    while True:
        screen.fill(BLACK)
        draw_text(screen, "Scores", 60, WIDTH // 2, HEIGHT // 6)
        draw_text(screen, f"High Score: {stats['high_score']}", 40, WIDTH // 2, HEIGHT // 3)
        draw_text(screen, f"Dernier Score: {stats['last_score']}", 40, WIDTH // 2, HEIGHT // 3 + 50)
        draw_text(screen, f"Ennemis détruits: {stats['bubbles_destroyed']}", 40, WIDTH // 2, HEIGHT // 3 + 100)
        draw_text(screen, f"Balles manquées: {stats['bullets_missed']}", 40, WIDTH // 2, HEIGHT // 3 + 150)
        draw_text(screen, f"Temps total de jeu: {format_time(stats['play_time'])}", 40, WIDTH // 2, HEIGHT // 3 + 200)
        draw_text(screen, "Entrée pour Retour", 30, WIDTH // 2, HEIGHT - 60)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return


# === GAME ===
def game_loop():
    global all_sprites, enemies, bullets, specials
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    specials = pygame.sprite.Group()

    player = Player()
    all_sprites.add(player)

    score = 0
    lives = 3
    start_time = pygame.time.get_ticks()
    shake = 0

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        if random.random() < ENEMY_SPAWN_CHANCE:
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)

        if random.random() < SPECIAL_SPAWN_CHANCE:
            bubble = Bubble(all_sprites, specials)
            specials.add(bubble)
            all_sprites.add(bubble)

        all_sprites.update()

        hits = pygame.sprite.groupcollide(enemies, bullets, True, True, pygame.sprite.collide_mask)
        for hit in hits:
            score += hit.points
            stats["bubbles_destroyed"] += 1

        hits2 = pygame.sprite.spritecollide(player, enemies, True, pygame.sprite.collide_mask)
        if hits2:
            lives -= 1
            shake = 10
            if damage_sound:
                damage_sound.play()

        hits3 = pygame.sprite.spritecollide(player, specials, True, pygame.sprite.collide_mask)
        if hits3:
            lives -= 1
            shake = 10
            if damage_sound:
                damage_sound.play()

        screen.fill(BLACK)

        offset_x, offset_y = 0, 0
        if shake > 0:
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            shake -= 1

        for sprite in all_sprites:
            screen.blit(sprite.image, sprite.rect.move(offset_x, offset_y))

        draw_text(screen, f"Score: {score}", 30, WIDTH // 2, 20)
        draw_text(screen, f"Vies: {lives}", 30, WIDTH - 60, 20)
        pygame.display.flip()

        if lives <= 0:
            running = False

    elapsed = (pygame.time.get_ticks() - start_time) // 1000
    stats["last_score"] = score
    stats["high_score"] = max(stats["high_score"], score)
    stats["play_time"] += elapsed
    save_stats(stats)


# === MAIN ===
while True:
    menu()

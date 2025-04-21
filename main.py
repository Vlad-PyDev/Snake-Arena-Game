import os
from sys import exit
import pygame
import pygame_menu
import math
import random as rd
from functools import partial

pygame.init()
pygame.display.set_caption('Snake Arena')
pygame.display.set_icon(pygame.image.load('data/icon.png'))
size = width, height = 750, 600
font = pygame.font.SysFont('timesNewRoman', 25)
clock = pygame.time.Clock()
fps = 60
screen = pygame.display.set_mode(size)

moves = {'u': 0, 'd': 0, 'l': 0, 'r': 0}
max_level = int(open('data/save.txt').readline())
game_is_running, player_is_dead, spawned_enemies, sf = True, False, 0, 0
level_selected, is_win, pause_time = '', False, 0
pause_image = pygame.Surface([width, height], pygame.SRCALPHA)
pygame.draw.rect(pause_image, (0, 0, 0, 100), (0, 0, width, height))
p_text = [font.render(text, True, (255, 255, 255)) for text in ('Пауза!', 'Нажмите на M, чтобы выйти в меню.',
                                                                    'ВНИМАНИЕ! Ваш прогресс НЕ сохранится.')]
w_text = [font.render(text, True, (255, 255, 255)) for text in ('Победа!', 'Нажмите на M, чтобы выйти в меню.',
                                                                'Нажмите на N, чтобы перейти к следующему уровню')]

sounds = {
    'shoot': pygame.mixer.Sound('data/shoot_sfx.wav'),
    'reload': pygame.mixer.Sound('data/reload_sfx.mp3'),
    'swing': pygame.mixer.Sound('data/knife_sfx.mp3'),
    'heal': pygame.mixer.Sound('data/heal_sfx.wav'),
    'pick': pygame.mixer.Sound('data/ammo_pick_sfx.mp3'),
    'hurt': pygame.mixer.Sound('data/hurt_sfx.wav'),
    'en_shoot': pygame.mixer.Sound('data/enemy_shoot.mp3'),
    'break_1': pygame.mixer.Sound('data/snd_break1.wav'),
    'break_2': pygame.mixer.Sound('data/snd_break2.wav')}
music = ['mus_death', 'mus_pause', 'mus_menu', 'mus_fight', 'mus_win']

player_sprite = pygame.sprite.Group()
tiles_sprite = pygame.sprite.Group()
border_sprite = pygame.sprite.Group()
g_border_sprite = pygame.sprite.Group()
bullets_sprite = pygame.sprite.Group()
enemy_sprite = pygame.sprite.Group()
spawner_sprite = pygame.sprite.Group()
after_player_sprite = pygame.sprite.Group()
knife_sprite = pygame.sprite.Group()
drops_sprite = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()

allow_shoot = pygame.USEREVENT + 0
allow_reload = pygame.USEREVENT + 1
enemy_shoot = pygame.USEREVENT + 2
allow_hit = pygame.USEREVENT + 3
allow_spawn = pygame.USEREVENT + 4

pygame.time.set_timer(enemy_shoot, 500)


def transition(surface, reverse=False):
    for alpha in range(0, 256, 10):
        screen.fill((0, 0, 0))
        surface.set_alpha(alpha if not reverse else 255 - alpha)
        screen.blit(surface, (0, 0))
        pygame.time.wait(30)
        pygame.display.flip()


def start_the_game(level):
    if int(level) > max_level: return
    global is_win, game_is_running, player_is_dead, spawned_enemies, sf
    global level_map, player, level_x, level_y, level_selected, boss
    pygame.mixer.music.load(f'data/{music[3]}.mp3')
    black_surface = pygame.Surface((width, height))
    black_surface.fill((0, 0, 0))
    transition(black_surface)
    pygame.time.wait(100)
    level_sel_menu.close()
    for i in all_sprites:
        i.kill()
    is_win, game_is_running, player_is_dead, spawned_enemies, sf = False, True, False, 0, 0
    level_selected = 'Уровень ' + level
    level_map = load_level(f'level{level}.txt')
    player, level_x, level_y, boss = generate_level(level_map)
    pygame.mixer.music.play(-1)
    mainloop()


def to_settings():
    menu.close()
    settings_menu.close()
    settings_menu.mainloop(screen)


def to_about():
    menu.close()
    about_menu.enable()
    about_menu.mainloop(screen)


def to_level_selection():
    menu.close()
    level_sel_menu.enable()
    level_sel_menu.mainloop(screen)


def to_main_menu(from_menu):
    from_menu.close()
    menu.enable()
    menu.mainloop(screen)


def change_volume(tip, value):
    if not tip:
        for i in sounds.values():
            i.set_volume(int(value) / 100)
    else:
        pygame.mixer.music.set_volume(int(value) / 100)


image = pygame_menu.BaseImage('data/bg2.png')
aboutTheme = pygame_menu.Theme(background_color=(0, 0, 0), widget_font_size=25, title=False,
                               widget_font_color=(215, 215, 215))
theme = pygame_menu.Theme(background_color=(0, 0, 0), widget_font_size=40,
                          title=False, widget_font_color=(215, 215, 215))
mainTheme = pygame_menu.Theme(background_color=image, widget_font=pygame_menu.font.FONT_MUNRO, widget_font_size=50,
                              title=False)
menu = pygame_menu.Menu('', width, height, theme=mainTheme)
settings_menu = pygame_menu.Menu('', width, height, theme=theme)
about_menu = pygame_menu.Menu('', width, height, theme=aboutTheme)
level_sel_menu = pygame_menu.Menu('', width, height, theme=theme, columns=3, rows=4)
level_sel_menu.add.label('')
for lvl in range(1, 4):
    level_sel_menu.add.button(f'Уровень {lvl}', partial(start_the_game, str(lvl)))
level_sel_menu.add.label('Выбор уровня')
for lvl in range(4, 7):
    level_sel_menu.add.button(f'Уровень {lvl}', partial(start_the_game, str(lvl)))
level_sel_menu.add.button('Назад', partial(to_main_menu, level_sel_menu))
for lvl in range(7, 9):
    level_sel_menu.add.button(f'Уровень {lvl}', partial(start_the_game, str(lvl)))
level_sel_menu.add.label('')
settings_menu.add.label('Настройки')
settings_menu.add.vertical_margin(50)
settings_menu.add.range_slider('Громкость звуков:', 75, (0, 100), 1, onchange=partial(change_volume, False),
                               value_format=lambda x: str(int(x)))
settings_menu.add.vertical_margin(50)
settings_menu.add.range_slider('Громкость музыки:', 75, (0, 100), 1, onchange=partial(change_volume, True),
                               value_format=lambda x: str(int(x)))
settings_menu.add.vertical_margin(200)
settings_menu.add.button('Назад', partial(to_main_menu, settings_menu))
about_menu.add.label(' '.join([i for i in open('about.txt', encoding='UTF-8')]))
about_menu.add.button('Назад', partial(to_main_menu, about_menu))
menu.add.button('Play', to_level_selection)
menu.add.button('Settings', to_settings)
menu.add.button('About', to_about)
menu.add.button('Quit', pygame_menu.events.EXIT)


def mainloop():
    global moves, game_is_running, sf, is_win, pause_time, spawned_enemies
    while True:
        if not player_is_dead:
            screen.fill((0, 0, 0))
            border_sprite.draw(screen)
            g_border_sprite.draw(screen)
            tiles_sprite.draw(screen)
            spawner_sprite.draw(screen)
            drops_sprite.draw(screen)
            bullets_sprite.draw(screen)
            knife_sprite.draw(screen)
            if (sf // 10) % 2 == 0:
                player_sprite.draw(screen)
            enemy_sprite.draw(screen)
            after_player_sprite.draw(screen)
            bullets_sprite.update()
            for line in text_display():
                screen.blit(line[0], line[1])
            display_ui()
            if game_is_running:
                if player.killed_enemies == 15:
                    is_win = True
                    game_is_running = False
                camera.update(player)
                for sprite in all_sprites:
                    camera.apply(sprite)
                spawner_sprite.update()
                drops_sprite.update()
                knife_sprite.update()
                enemy_sprite.update()
                if player.safe_frames:
                    sf += 1
                if sf == 100:
                    player.safe_frames = False
                    sf = 0
                player.move()
            else:
                screen.blit(pause_image, (0, 0))
                for i in range(3):
                    if is_win:
                        screen.blit(w_text[i], ((width - w_text[i].get_width()) // 2, height // 2 - 75 + i * 50))
                    else:
                        screen.blit(p_text[i], ((width - p_text[i].get_width()) // 2, height // 2 - 75 + i * 50))
        else:
            sounds['reload'].stop()
            game_over_screen()
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print('You quited')
                terminate()
            elif event.type == pygame.KEYDOWN and not is_win:
                if event.key == pygame.K_ESCAPE:
                    if not game_is_running:
                        game_is_running = True
                        moves = {'u': 0, 'd': 0, 'l': 0, 'r': 0}
                        pygame.mixer.music.load(f'data/{music[3]}.mp3')
                        pygame.mixer.music.play(-1, pause_time / 1000, 50)
                    else:
                        game_is_running = False
                        pause_time = pygame.mixer.music.get_pos()
                        pygame.mixer.music.load(f'data/{music[1]}.mp3')
                        pygame.mixer.music.play(-1, 0.0, 50)
            elif event.type == allow_spawn:
                spawned_enemies += 1
                rand_enemy = rd.randint(1, 3)
                if rand_enemy == 1:
                    speed = 2
                else:
                    speed = 1 if rand_enemy == 2 else 5
                try:
                    Enemy(boss.rect.x + 40, boss.rect.y + 20, speed, rand_enemy)
                except AttributeError:
                    ...
            if game_is_running:
                if event.type == allow_shoot and player.weapon and player.ammo and player.is_shooting:
                    pygame.time.set_timer(allow_shoot, 150)
                    player.shoot()
                elif event.type == allow_hit and not player.weapon and player.is_hitting:
                    pygame.time.set_timer(allow_hit, 500)
                    player.hit()
                if event.type == enemy_shoot:
                    for enemy in enemy_sprite:
                        enemy.shoot()
                if event.type == allow_reload and player.is_reloading:
                    player.reload()
                    player.is_reloading = False
                if not player.is_reloading:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        player.is_shooting, player.is_hitting = True, True
                        pygame.time.set_timer(allow_shoot, 10)
                        pygame.time.set_timer(allow_hit, 10)
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        player.is_shooting, player.is_hitting = False, False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        player.weapon = 1
                    elif event.key == pygame.K_2:
                        player.weapon = 0
                        player.is_reloading = False
                    elif event.key == pygame.K_r and player.weapon:
                        pygame.time.set_timer(allow_reload, 3000)
                        if player.is_reloading:
                            player.is_reloading = False
                            sounds['reload'].stop()
                        else:
                            player.is_reloading = True
                            sounds['reload'].play(0)
                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        moves['u'] = 1 if event.type == pygame.KEYDOWN else 0
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        moves['d'] = 1 if event.type == pygame.KEYDOWN else 0
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        moves['r'] = 1 if event.type == pygame.KEYDOWN else 0
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        moves['l'] = 1 if event.type == pygame.KEYDOWN else 0
            else:
                global max_level
                if is_win and pygame.mixer.get_busy():
                    pygame.mixer.music.stop()
                if is_win and max_level == 8:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_n, pygame.K_m):
                            pygame.mixer.music.stop()
                            menu.enable()
                            pygame.mixer.music.load(f'data/{music[2]}.mp3')
                            pygame.mixer.music.play(-1)
                            menu.mainloop(screen)
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_n, pygame.K_m) and is_win and level_selected[-1] == str(max_level):
                        max_level += 1
                        with open('data/save.txt', 'w') as f:
                            f.write(str(max_level))
                    if event.key == pygame.K_n and is_win:
                        start_the_game(f'{int(level_selected[-1]) + 1}')
                        return
                    if event.key == pygame.K_m:
                        pygame.mixer.music.stop()
                        menu.enable()
                        pygame.mixer.music.load(f'data/{music[2]}.mp3')
                        pygame.mixer.music.play(-1)
                        menu.mainloop(screen)
        clock.tick(fps)
        pygame.display.flip()


def terminate():
    pygame.quit()
    exit()


def load_image(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        exit()
    im = pygame.image.load(fullname).convert_alpha()
    return im


tile_images = {
    'wall': load_image('wall.png'),
    'empty': load_image('grass.png'),
    'water': load_image('water.png'),
    'sand': load_image('sand.png'),
    'dirt': load_image('dirt.png'),
    'box': load_image('box.png'),
    'tree': load_image('plant.png'),
    'plant_1': load_image('plant_123.png'),
    'plant_2': load_image('plant_2.png'),
    'plant_3': load_image('plant_3.png'),
    'block': load_image('block.png'),
    'spawner': load_image('spawner.png')
}
ui_images = {
    'heart': load_image('heart.png'),
    'empty_heart': load_image('empty_heart.png'),
    'bullet': load_image('bullet.png'),
    'ammo_pack': load_image('ammo_pack.png'),
    1: load_image('gun_icon.png'),
    0: load_image('knife_icon.png')
}
animated_images = {
        'player_stand': [pygame.image.load(f'data\player_{j}stand.png') for j in ('k', '')],
        'player_right': [[pygame.image.load(f'data\player_{j}right_{i}.png') for i in range(1, 5)] for j in ('k', '')],
        'player_left': [[pygame.image.load(f'data\player_{j}left_{i}.png') for i in range(1, 5)] for j in ('k', '')],
        'player_up': [[pygame.image.load(f'data\player_{j}up_{i}.png') for i in range(1, 5)] for j in ('k', '')],
        'player_down': [[pygame.image.load(f'data\player_{j}down_{i}.png') for i in range(1, 5)] for j in ('k', '')],
        'stand_enemy1': pygame.image.load('data\enemy_stand.png'),
        'right_enemy1': [pygame.image.load(f'data\enemy_right_{i}.png') for i in range(1, 5)],
        'left_enemy1': [pygame.image.load(f'data\enemy_left_{i}.png') for i in range(1, 5)],
        'up_enemy1': [pygame.image.load(f'data\enemy_up_{i}.png') for i in range(1, 5)],
        'down_enemy1': [pygame.image.load(f'data\enemy_down_{i}.png') for i in range(1, 5)],
        'stand_enemy2': pygame.image.load('data\_red_down_1.png'),
        'right_enemy2': [pygame.image.load(f'data\_red_right_{i}.png') for i in range(1, 5)],
        'left_enemy2': [pygame.image.load(f'data\_red_left_{i}.png') for i in range(1, 5)],
        'up_enemy2': [pygame.image.load(f'data\_red_up_{i}.png') for i in range(1, 5)],
        'down_enemy2': [pygame.image.load(f'data\_red_down_{i}.png') for i in range(1, 5)],
        'stand_enemy3': pygame.image.load('data\_yellow_down_1.png'),
        'right_enemy3': [pygame.image.load(f'data\_yellow_right_{i}.png') for i in range(1, 5)],
        'left_enemy3': [pygame.image.load(f'data\_yellow_left_{i}.png') for i in range(1, 5)],
        'up_enemy3': [pygame.image.load(f'data\_yellow_up_{i}.png') for i in range(1, 5)],
        'down_enemy3': [pygame.image.load(f'data\_yellow_down_{i}.png') for i in range(1, 5)],
        'stand_enemy4': pygame.image.load('data\snake_king_down_1.png'),
        'right_enemy4': [pygame.image.load(f'data\snake_king_right_{i}.png') for i in range(1, 5)],
        'left_enemy4': [pygame.image.load(f'data\snake_king_left_{i}.png') for i in range(1, 5)],
        'up_enemy4': [pygame.image.load(f'data\snake_king_up_{i}.png') for i in range(1, 5)],
        'down_enemy4': [pygame.image.load(f'data\snake_king_down_{i}.png') for i in range(1, 5)],
}
heart_break = [load_image(f'heartbreak_{i}.png') for i in range(1, 3)]
heart_pieces = [load_image(f'heart_piece_{i}.png') for i in range(1, 5)]
knife_image = load_image('knife.png')
box_image = load_image('ammo_drop.PNG')
heart_image = load_image('heart.png')
loose_screen = load_image('death_screen.png')


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vec_0, vec_1, b_type=True):
        super().__init__(bullets_sprite, all_sprites)
        self.type = b_type
        if not self.type:
            self.rect = pygame.draw.rect(screen, (255, 255, 0), (x, y, 8, 8))
        else:
            sounds['en_shoot'].play()
            self.rect = pygame.draw.rect(screen, (225, 0, 0), (x, y, 12, 12))
        self.image = pygame.Surface((12, 12) if self.type else (8, 8))
        self.mov_vect = pygame.math.Vector2(vec_0 - x, vec_1 - y)
        self.mov_vect.scale_to_length(12 if not self.type else 7)

    def update(self):
        if not self.type:
            pygame.draw.rect(screen, (255, 255, 0), (self.rect.x, self.rect.y, 8, 8))
        else:
            pygame.draw.rect(screen, (225, 0, 0), (self.rect.x, self.rect.y, 12, 12))
        if game_is_running:
            self.rect.x, self.rect.y = int(self.rect.x + self.mov_vect.x), int(self.rect.y + self.mov_vect.y)
            if pygame.sprite.spritecollideany(self, border_sprite) and not pygame.sprite.spritecollideany(
                    self, g_border_sprite):
                self.kill()
            if pygame.sprite.spritecollideany(self, enemy_sprite) and not self.type:
                pygame.sprite.spritecollide(self, enemy_sprite, False)[0].health -= 1
                self.kill()
            if pygame.sprite.spritecollideany(self, player_sprite) and self.type:
                player.damage()
                self.kill()


class Knife(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(knife_sprite, all_sprites)
        self.ticks = 0
        direction = (pygame.math.Vector2(x, y) - player.rect.center).angle_to((1, 0)) - 90
        self.x_move = -10 * math.sin(math.radians(direction))
        self.y_move = -10 * math.cos(math.radians(direction))
        self.image = pygame.transform.rotate(knife_image, direction)
        self.rect = self.image.get_rect(center=player.rect.center)

    def update(self):
        self.rect.x += (self.x_move if self.ticks < 10 else -self.x_move) - camera.dx
        self.rect.y += (self.y_move if self.ticks < 10 else -self.y_move) - camera.dy
        if self.ticks == 10:
            for en in pygame.sprite.spritecollide(self, enemy_sprite, False):
                en.health -= 1
        elif self.ticks == 20:
            self.kill()
        self.ticks += 1


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_sprite, all_sprites)
        self.hp, self.ammo, self.pack, self.killed_enemies = 5, 30, 5, 0
        self.weapon, self.is_hitting, self.animation_count = 1, False, 0
        self.is_reloading, self.is_shooting, self.safe_frames, self.flag = False, False, False, False
        self.image = load_image('player_stand.png')
        self.rect = self.image.get_rect(center=((50 * pos_x - self.image.get_width()) // 2,
                                                (50 * pos_y - self.image.get_height()) // 2
                                                )).move(50 * pos_x + 2, 50 * pos_y - 3)

    def move(self):
        if pygame.sprite.spritecollideany(self, border_sprite):
            sp = [player.rect.clip(i) for i in pygame.sprite.spritecollide(player, border_sprite, False)]
            sp = sorted([[i.left, i.right, i.bottom, i.top, i.width, i.height] for i in sp], key=lambda x: (x[4], x[5]))
            if len(sp) != 1:
                sp += [[min(sp[0][0], sp[1][0]), max(sp[0][1], sp[1][1]), max(sp[0][2], sp[1][2]), min(sp[0][3],
                                                                                                       sp[1][3])]]
                for _ in range(2):
                    del sp[0]
            for i in sp:
                if i[3] >= self.rect.bottom - 2:
                    moves['d'] = 0
                elif i[1] <= self.rect.left + 5:
                    moves['l'] = 0
                elif i[2] <= self.rect.top + 5:
                    moves['u'] = 0
                elif i[0] >= self.rect.right - 4:
                    moves['r'] = 0
            self.flag = True
        elif self.flag:
            keys, self.flag = pygame.key.get_pressed(), False
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                moves['d'] = 1
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                moves['u'] = 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                moves['l'] = 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                moves['r'] = 1
        if moves['r'] == 1:  # Анимация перемещения вправо
            self.image = animated_images['player_right'][self.weapon][self.animation_count // 4]
            self.animation_count = self.animation_count + 1 if self.animation_count < 15 else 0
        elif moves['l']:  # Анимация перемещения влево
            self.image = animated_images['player_left'][self.weapon][self.animation_count // 4]
            self.animation_count = self.animation_count + 1 if self.animation_count < 15 else 0
        elif moves['d']:  # Анимация перемещения вниз
            self.image = animated_images['player_down'][self.weapon][self.animation_count // 4]
            self.animation_count = self.animation_count + 1 if self.animation_count < 15 else 0
        elif moves['u']:  # Анимация перемещения вверх
            self.image = animated_images['player_up'][self.weapon][self.animation_count // 4]
            self.animation_count = self.animation_count + 1 if self.animation_count < 15 else 0
        else:
            self.image = animated_images['player_stand'][self.weapon]
        self.rect.x += 5 * (moves['r'] - moves['l'])
        self.rect.y += 5 * (moves['d'] - moves['u'])

    def shoot(self):
        Bullet(*self.rect.center, *pygame.mouse.get_pos(), False)
        sounds['shoot'].play(0)
        self.ammo -= 1

    def hit(self):
        sounds['swing'].play(0)
        Knife(*pygame.mouse.get_pos())

    def reload(self):
        if self.pack != 0:
            self.ammo = 30
            self.pack -= 1

    def damage(self):
        global player_is_dead
        if not self.safe_frames:
            sounds['hurt'].play(0)
            self.hp -= 1
            if self.hp <= 0:
                print('You lost :(')
                pygame.mixer.music.stop()
                player_is_dead = True
            self.safe_frames = True


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        if tile_type in ('wall', 'box'):
            super().__init__(border_sprite, all_sprites)
        elif tile_type == 'water':
            super().__init__(border_sprite, g_border_sprite, all_sprites)
        elif tile_type == 'tree':
            super().__init__(after_player_sprite, all_sprites)
        else:
            super().__init__(tiles_sprite, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(50 * pos_x, 50 * pos_y)


class Drop(pygame.sprite.Sprite):
    def __init__(self, x, y, drop_type):
        super().__init__(drops_sprite, all_sprites)
        self.drop_type = drop_type
        if drop_type == 1:
            self.image = box_image
        else:
            self.image = heart_image
        self.rect = self.image.get_rect().move(round(x * 2, -2) // 2, round(y * 2, -2) // 2)

    def update(self):
        if pygame.sprite.spritecollideany(self, player_sprite):
            if player.pack < 5 and self.drop_type == 1:
                player.pack += 1
                sounds['pick'].play(0)
                self.kill()
            if player.hp < 5 and self.drop_type == 2:
                player.hp += 1
                sounds['heal'].play(0)
                self.kill()


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - width // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - height // 2)


camera = Camera()


class Spawner(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, interval):
        super().__init__(spawner_sprite, all_sprites)
        self.interval = interval
        self.past_time = 0
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.image = tile_images['spawner']
        self.rect = self.image.get_rect().move(50 * pos_x, 50 * pos_y)

    def update(self):
        global spawned_enemies
        self.past_time += 1
        if self.past_time >= self.interval and spawned_enemies != 15:
            spawned_enemies += 1
            rand_enemy = rd.randint(1, 3)
            if rand_enemy == 1:
                speed = 2
            else:
                speed = 1 if rand_enemy == 2 else 5
            Enemy(self.rect.x + 40, self.rect.y + 20, speed, rand_enemy)
            self.past_time = 0


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x_enemy, y_enemy, speed, e_type, movement='m'):
        super().__init__(all_sprites, enemy_sprite)
        self.e_type = e_type
        self.animation = [False, False, False, False, False]  # left, right, down, up, enemy_is_near
        self.animation_count = 0
        self.flag = False
        self.movement = movement
        if e_type == 1:
            self.health = 7
        elif e_type == 2:
            self.health = 10
        elif e_type == 3:
            self.health = 3
        else:
            pygame.time.set_timer(allow_spawn, 5000)
            self.health = 100
        self.hp = self.health
        self.is_hit = 0
        self.speed = speed
        self.image = animated_images[f'stand_enemy{e_type}']
        self.rect = self.image.get_rect().move(x_enemy, y_enemy)
        if e_type == 4:
            self.rect.width = 100
            self.rect.height = 100

    def update(self):
        right, left, up, down = self.speed, -self.speed, -self.speed, self.speed
        if self.health <= 0:
            if self.e_type == 4:
                global is_win, game_is_running
                is_win = True
                game_is_running = False
            else:
                if level_selected != 'Уровень 8':
                    player.killed_enemies += 1
                if player.pack < 5 and rd.random() <= 0.2:
                    Drop(self.rect.left, self.rect.y, 1)
                if player.hp != 5 and rd.random() <= 0.35:
                    Drop(self.rect.right, self.rect.y, 2)
            if player.killed_enemies == 15:
                pygame.mixer.music.load(f'data/{music[4]}.mp3')
                pygame.mixer.music.play(-1)
            self.kill()
        elif self.health < self.hp:
            pygame.draw.rect(screen, (0, 0, 0), (self.rect.x - 10, self.rect.y - 15, self.rect.width + 20, 10))
            pygame.draw.rect(screen, (255, 0, 0), (self.rect.x - 10, self.rect.y - 15,
                                                   int((self.rect.width + 20) * (self.health / self.hp)), 10))
        if pygame.sprite.spritecollideany(self, border_sprite) and self.movement == 'm':
            sp = [self.rect.clip(i) for i in pygame.sprite.spritecollide(self, border_sprite, False)]
            sp = sorted([[i.left, i.right, i.bottom, i.top, i.width, i.height] for i in sp], key=lambda z: (z[4], z[5]))
            if len(sp) != 1:
                sp += [[min(sp[0][0], sp[1][0]), max(sp[0][1], sp[1][1]), max(sp[0][2], sp[1][2]), min(sp[0][3],
                                                                                                       sp[1][3])]]
                for _ in range(2):
                    del sp[0]
            for i in sp:
                if i[3] >= self.rect.bottom - (2 if self.e_type != 3 else 6):
                    down = 0
                if i[1] <= self.rect.left + (5 if self.e_type != 3 else 9):
                    left = 0
                if i[2] <= self.rect.top + (5 if self.e_type != 3 else 9):
                    up = 0
                if i[0] >= self.rect.right - (4 if self.e_type != 3 else 8):
                    right = 0
            self.flag = True
        elif self.flag and self.movement == 'm':
            right, left, up, down = self.speed, -self.speed, -self.speed, self.speed
            self.flag = False
        x, y = player.rect.x, player.rect.y
        if abs(self.rect.x - x) <= 200 and abs(self.rect.y - y) <= 200 and self.e_type != 2:
            if self.e_type == 1:
                self.animation = [False, False, False, False, True]
            else:
                self.speed = 4
        elif self.e_type != 2:
            if self.e_type == 1:
                self.animation[4] = False
            else:
                self.speed = 3
        if self.rect.x == x and self.rect.y == y and self.e_type in (2, 3):
            self.animation = [False, False, False, False, True]
        elif self.e_type in (2, 3):
            self.animation[4] = False
        if not self.animation[4] and self.movement == 'm':
            # Если вражеский персонаж не находится на оптимальных для стрельбы координатах
            if self.rect.x != x or self.rect.y != y:
                '''Условие, если координата x вражеского персонажа не равна координате x игрока 
                или координата y вражеского персонажа не равна координате y игрока'''
                if self.rect.x != x and self.rect.y != y and (abs(self.rect.x - x) > 1 if self.e_type == 3 else True):
                    '''Повторяется это условие, для того, чтобы под каждое перемещение вражеского игрока 
                    (вверх, вниз, влево, вправо) сделать анимацию'''
                    if self.rect.x > x and self.rect.y > y and (left or up):
                        '''Условие, если координата x вражеского персонажа больше координаты x игрока 
                    или координата y вражеского персонажа больше координаты y игрока'''
                        move_vec = pygame.math.Vector2(left, up)
                        move_vec.scale_to_length(self.speed)
                        self.animation = [True, False, False, False, self.animation[4]]
                        self.rect.x, self.rect.y = self.rect.x + move_vec.x, self.rect.y + move_vec.y
                    elif self.rect.x < x and self.rect.y < y and (right or down):
                        move_vec = pygame.math.Vector2(right, down)
                        move_vec.scale_to_length(self.speed)
                        self.animation = [False, True, False, False, self.animation[4]]
                        self.rect.x, self.rect.y = self.rect.x + move_vec.x, self.rect.y + move_vec.y
                    elif self.rect.x < x and self.rect.y > y and (right or up):
                        move_vec = pygame.math.Vector2(right, up)
                        move_vec.scale_to_length(self.speed)
                        self.animation = [False, True, False, False, self.animation[4]]
                        self.rect.x, self.rect.y = self.rect.x + move_vec.x, self.rect.y + move_vec.y
                    elif self.rect.x > x and self.rect.y < y and (self.rect.x - x > 1 if self.e_type == 3 else True):
                        if left or down:
                            move_vec = pygame.math.Vector2(left, down)
                            move_vec.scale_to_length(self.speed)
                            self.animation = [True, False, False, False, self.animation[4]]
                            self.rect.x, self.rect.y = self.rect.x + move_vec.x, self.rect.y + move_vec.y
                elif self.rect.y != y:
                    if self.rect.y < y:
                        self.animation = [False, False, True, False, self.animation[4]]
                        self.rect.y = self.rect.y + down
                    elif self.rect.y > y:
                        self.animation = [False, False, False, True, self.animation[4]]
                        self.rect.y = self.rect.y + up
                elif self.rect.x != x:
                    if self.rect.x < x:
                        self.rect.x = self.rect.x + right
                        self.animation = [False, True, False, False, self.animation[4]]
                    elif self.rect.x > x:
                        self.rect.x = self.rect.x + left
                        self.animation = [True, False, False, False, self.animation[4]]
            else:
                self.animation = [False, False, False, False, self.animation[4]]
        if self.movement == 'm':
            if self.animation[0]:  # Анимация перемещения влево
                self.image = animated_images[f'left_enemy{self.e_type}'][self.animation_count // 4]
                self.animation_count = self.animation_count + 1 if self.animation_count != 15 else 0
            elif self.animation[1]:  # Анимация перемещения вправо
                self.image = animated_images[f'right_enemy{self.e_type}'][self.animation_count // 4]
                self.animation_count = self.animation_count + 1 if self.animation_count != 15 else 0
            elif self.animation[2]:  # Анимация перемещения вниз
                self.image = animated_images[f'down_enemy{self.e_type}'][self.animation_count // 4]
                self.animation_count = self.animation_count + 1 if self.animation_count != 15 else 0
            elif self.animation[3]:  # Анимация перемещения вверх
                self.image = animated_images[f'up_enemy{self.e_type}'][self.animation_count // 4]
                self.animation_count = self.animation_count + 1 if self.animation_count != 15 else 0
            else:
                self.image = animated_images[f'stand_enemy{self.e_type}']
            if self.e_type == 4:
                self.image = pygame.transform.scale(self.image, (100, 100))
        if pygame.sprite.spritecollideany(self, player_sprite):
            player.damage()

    def shoot(self):
        if self.animation[4] and self.e_type == 1:
            Bullet(*self.rect.center, *player.rect.center)


def game_over_screen():
    pygame.mixer.music.load(f'data/{music[0]}.mp3')
    frames = 0
    x_pos, y_pos = player.rect.x, player.rect.y
    while frames < 3500:
        frames += 1
        screen.fill((0, 0, 0))
        if frames < 1500:
            screen.blit(heart_break[0], (x_pos + 10, y_pos + 10))
        else:
            screen.blit(heart_break[1], (x_pos + 5, y_pos + 10))
        if frames == 1500: sounds['break_1'].play(0)
        pygame.display.flip()
    sounds['break_2'].play(0)
    x_pos = [width // 2, width // 2, width // 2, width // 2]
    y_pos = player.rect.y + 10
    while frames < 6000:
        screen.fill((0, 0, 0))
        frames += 1
        if frames % 4 == 0:
            for piece, x_piece in enumerate(x_pos):
                screen.blit(heart_pieces[piece], (x_piece, y_pos))
                x_pos[piece] -= piece - (2 if piece < 2 else 1)
            y_pos += 1
        pygame.display.flip()
    frames = 255
    pygame.mixer.music.play(-1)
    loose_text = [font.render(text, True, (255, 255, 255)) for text in (level_selected,
                                                                        f'Врагов убито: {player.killed_enemies}')]
    btn_screen = pygame.Surface((150, 50))
    btn_screen.fill((255, 255, 255))
    btn_screen.blit(pygame.Surface((144, 44)), (3, 3))
    btn_screen.blit(font.render('Назад', True, (255, 255, 255)), (40, 7))
    while True:
        screen.blit(loose_screen, (0, 0))
        screen.blit(btn_screen, (500, 475))
        for pos, i in enumerate(loose_text):
            screen.blit(i, (500, 375 + (50 * pos)))
        if frames >= 0:
            s = pygame.Surface((width, height))
            s.set_alpha(int(frames))
            s.fill((0, 0, 0))
            screen.blit(s, (0, 0))
            frames -= 0.1
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                terminate()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if 500 <= ev.pos[0] <= 650 and 475 <= ev.pos[1] <= 525:
                    pygame.mixer.music.stop()
                    menu.enable()
                    pygame.mixer.music.load(f'data/{music[2]}.mp3')
                    pygame.mixer.music.play(-1)
                    menu.mainloop(screen)
                    break
        pygame.display.flip()


def load_level(filename):
    level = [string.strip() for string in open("data/" + filename, 'r')]
    return level


def generate_level(level):
    boss = None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
                Tile('plant_1', x, y)
            elif level[y][x] == '#':
                Tile('wall', x, y)
            elif level[y][x] == 'W':
                Tile('water', x, y)
            elif level[y][x] == 'S':
                Tile('sand', x, y)
            elif level[y][x] == 'D':
                Tile('dirt', x, y)
            elif level[y][x] == 'B':
                Tile('box', x, y)
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
            elif level[y][x] == 'T':
                Tile('tree', x, y)
                Tile('empty', x, y)
            elif level[y][x] == 's':
                Spawner(x, y, fps * 8)
                Tile('empty', x, y)
            elif level[y][x] == 'E':
                Enemy(x * 50, y * 50, 0, 1, 's')
                Tile('empty', x, y)
            elif level[y][x] == 'b':
                boss = Enemy(x * 50, y * 50, 3, 4)
                Tile('empty', x, y)
    return new_player, x, y, boss


def display_ui():
    for i in range(5):
        if i < player.hp:
            screen.blit(ui_images['heart'], (600 + i * 29, 10))
        else:
            screen.blit(ui_images['empty_heart'], (600 + i * 29, 10))
    screen.blit(ui_images['ammo_pack'], (width - 101, height - 77))
    screen.blit(ui_images['bullet'], (width - 195, height - 80))
    screen.blit(ui_images[player.weapon], (width - 350, height - 85))


def text_display():
    ev_disp = []
    s1 = font.render(level_selected, True, pygame.Color('white'))
    r1 = s1.get_rect().move(10, 10)
    s2 = font.render(f'x{player.ammo}', True, pygame.Color('white'))
    r2 = s2.get_rect().move(width - 240, height - 50)
    s3 = font.render(f'x{player.pack}', True, pygame.Color('white'))
    r3 = s3.get_rect().move(width - 135, height - 50)
    if level_selected != 'Уровень 8':
        s4 = font.render(f'Врагов: {player.killed_enemies} / 15', True, pygame.Color('white'))
        ev_disp += [(s4, s4.get_rect().move(10, height - s2.get_rect().height - 10))]
    if player.is_reloading:
        s5 = font.render('Перезарядка!', True, pygame.Color('white'))
        ev_disp += [(s5, s5.get_rect().move(width - s5.get_rect().width - 10, 35))]
    return [(s1, r1), (s2, r2), (s3, r3)] + ev_disp


level_map = load_level('level1.txt')
player, level_x, level_y, boss = generate_level(level_map)

logo_image = pygame.image.load('data/logo.png')
transition(logo_image)
pygame.time.wait(750)
transition(logo_image, True)

pygame.mixer.music.load(f'data/{music[2]}.mp3')
pygame.mixer.music.play(-1)
menu.mainloop(screen)
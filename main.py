import pygame
import sys
import random
import math 
from config import *
from player import Player
from enemy import Enemy
from vfx import ScreenShake
from rendering.ui_render import draw_archangel_portrait
from rendering.background import generate_cave_background
from entities.archangel_boss import ArchangelBoss 
from rendering.archangel_render import draw_archangel_boss

# Константы для отладки
DEBUG_HITBOX_COLOR_NORMAL = (0, 255, 0) # Зеленый
DEBUG_HITBOX_COLOR_INVUL = (255, 0, 0)  # Красный

# *** НОВАЯ ФУНКЦИЯ КОЛЛИЗИИ ***
def complex_collision_check(sprite_a, sprite_b):
    """
    Проверяет коллизию с учетом hitboxes, если они есть.
    Если hitboxes нет, использует collide_circle (или collide_rect по умолчанию в pygame).
    Но здесь мы явно реализуем логику:
    1. Если у A есть hitboxes -> проверяем их против B.rect
    2. Если у B есть hitboxes -> проверяем их против A.rect
    3. Иначе -> collide_circle (так как в игре используются круги для снарядов и игрока)
    """
    # Проверяем sprite_a (например, Босс)
    if hasattr(sprite_a, 'hitboxes') and sprite_a.hitboxes:
        for hb in sprite_a.hitboxes:
            if hb.colliderect(sprite_b.rect):
                return True
        return False
    
    # Проверяем sprite_b
    if hasattr(sprite_b, 'hitboxes') and sprite_b.hitboxes:
        for hb in sprite_b.hitboxes:
            if hb.colliderect(sprite_a.rect):
                return True
        return False
        
    # Фолбек на круги (радиус)
    return pygame.sprite.collide_circle(sprite_a, sprite_b)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gothic Procedural Arena - ARCHANGEL BOSS")
        self.clock = pygame.time.Clock()

        # --- ГЕНЕРАЦИЯ ФОНА ---
        print("Генерирую пещеру...")
        self.cave_bg = generate_cave_background()
        print("Готово.")
        
        # --- ШРИФТЫ (ИСПРАВЛЕНО) ---
        # Передаем список шрифтов ОДНОЙ строкой через запятую
        serif_font_path = pygame.font.match_font('cambria, georgia, timesnewroman, serif')
        
        # Если шрифт не найден, match_font вернет None, и Pygame использует стандартный шрифт
        # Шрифт для Имени (Крупный)
        self.font_boss_name = pygame.font.Font(serif_font_path, 28)
        self.font_boss_name.set_bold(True)
        
        # Шрифт для Титула (Поменьше)
        self.font_boss_title = pygame.font.Font(serif_font_path, 18)
        self.font_boss_title.set_italic(True)
        
        # Обычный шрифт для отладки
        self.font = pygame.font.SysFont("Arial", 18)
        
        # --- ЗАГРУЗКА ПОРТРЕТА ---
        try:
            original_image = pygame.image.load('boss_icon.jpg').convert()
            self.boss_portrait = pygame.transform.smoothscale(original_image, (80, 80))
            # Разворачиваем, чтобы смотрела влево (на поле боя)
            self.boss_portrait = pygame.transform.flip(self.boss_portrait, True, False)
        except:
            print("Ошибка: файл boss_icon.jpg не найден. Создаю заглушку.")
            self.boss_portrait = pygame.Surface((80, 80))
            self.boss_portrait.fill((50, 0, 50))

        self.screen_shake = ScreenShake()
        
        # Очистка групп спрайтов
        all_sprites.empty()
        bullets.empty()
        enemies.empty()
        particles.empty()
        
        self.player = Player(
            (WIDTH/2, HEIGHT/2), 
            all_sprites, 
            None, 
            [all_sprites, particles],
            self.screen_shake.shake
        )
        
        self.boss = ArchangelBoss(WIDTH/2, HEIGHT/2 - 300, self.player)
        self.spawn_timer = 0
        self.spawn_rate = 9999999

    def draw_boss_hud(self):
        """Отрисовка красивого интерфейса босса."""
        if not self.boss.alive():
            return

        # Настройки расположения (Правый верхний угол)
        margin_right = 20
        margin_top = 20
        
        # Размеры
        p_size = 80 # Размер портрета
        bar_width = 300
        bar_height = 12
        
        # Координаты портрета
        p_x = WIDTH - margin_right - p_size
        p_y = margin_top
        
        # Цвета
        C_GOLD = (218, 165, 32)
        C_GOLD_DARK = (184, 134, 11)
        C_DARK_BG = (20, 15, 25)
        C_HP_BG = (40, 10, 10)
        C_HP_FILL = (180, 30, 30)
        C_HP_GLOW = (220, 80, 80)
        
        # --- 1. ФОН ПОРТРЕТА И РАМКА ---
        # Темная подложка
        pygame.draw.rect(self.screen, C_DARK_BG, (p_x, p_y, p_size, p_size))
        # Сам портрет
        self.screen.blit(self.boss_portrait, (p_x, p_y))
        
        # Декоративная рамка (Двойной контур)
        pygame.draw.rect(self.screen, C_GOLD, (p_x-2, p_y-2, p_size+4, p_size+4), 2)
        pygame.draw.rect(self.screen, C_GOLD_DARK, (p_x-5, p_y-5, p_size+10, p_size+10), 1)
        
        # Уголки (ромбики) на рамке для готичности
        corners = [
            (p_x-2, p_y-2), (p_x+p_size+2, p_y-2),
            (p_x-2, p_y+p_size+2), (p_x+p_size+2, p_y+p_size+2)
        ]
        for cx, cy in corners:
            pygame.draw.circle(self.screen, C_GOLD, (cx, cy), 4)
            pygame.draw.circle(self.screen, (0,0,0), (cx, cy), 2)

        # --- 2. ИМЯ И ТИТУЛ ---
        name_text = "Ресалаида"
        title_text = "Хранительница честивости"
        
        # Рендер текста
        surf_name = self.font_boss_name.render(name_text, True, (255, 240, 200))
        surf_title = self.font_boss_title.render(title_text, True, (200, 200, 200))
        
        # Позиционирование (Слева от портрета)
        # Имя
        name_rect = surf_name.get_rect(topright=(p_x - 15, p_y + 5))
        # Тень для имени
        surf_name_shadow = self.font_boss_name.render(name_text, True, (0, 0, 0))
        self.screen.blit(surf_name_shadow, (name_rect.x + 2, name_rect.y + 2))
        self.screen.blit(surf_name, name_rect)
        
        # Титул
        title_rect = surf_title.get_rect(topright=(p_x - 15, p_y + 38))
        self.screen.blit(surf_title, title_rect)

        # --- 3. ПОЛОСКА ЗДОРОВЬЯ (HP BAR) ---
        bar_x = p_x - 15 - bar_width
        bar_y = p_y + 60
        
        # Вычисление процента
        hp_pct = max(0, self.boss.hp / self.boss.max_hp)
        current_bar_w = int(bar_width * hp_pct)
        
        # Фон полоски (ромбовидные края)
        bg_poly = [
            (bar_x - 10, bar_y + bar_height), (bar_x, bar_y), # Скос слева
            (p_x - 5, bar_y), (p_x - 15, bar_y + bar_height)  # Соединение с портретом
        ]
        pygame.draw.polygon(self.screen, C_HP_BG, bg_poly)
        
        # Заливка HP
        if current_bar_w > 0:
            fill_poly = [
                (bar_x - 10, bar_y + bar_height), (bar_x, bar_y),
                (bar_x + current_bar_w, bar_y), (bar_x + current_bar_w - 10, bar_y + bar_height)
            ]
            # Если полоска полная, корректируем правый край
            if hp_pct > 0.98:
                 fill_poly[2] = (p_x - 5, bar_y)
                 fill_poly[3] = (p_x - 15, bar_y + bar_height)
            
            pygame.draw.polygon(self.screen, C_HP_FILL, fill_poly)
            # Тонкая линия свечения сверху
            pygame.draw.line(self.screen, C_HP_GLOW, fill_poly[1], fill_poly[2], 2)

        # Окантовка полоски
        pygame.draw.polygon(self.screen, C_GOLD, bg_poly, 2)

    def draw_grid(self, offset):
        start_x = int(-offset.x) % TILE_SIZE
        start_y = int(-offset.y) % TILE_SIZE
        for x in range(start_x, WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, HEIGHT))
        for y in range(start_y, HEIGHT, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (WIDTH, y))

    # *** ОБНОВЛЕННАЯ ФУНКЦИЯ: Отрисовка хитбокса ***
    def draw_hitbox(self, target_sprite, offset):
        # Если есть сложные хитбоксы, рисуем их все
        if hasattr(target_sprite, 'hitboxes') and target_sprite.hitboxes:
            for hb in target_sprite.hitboxes:
                draw_rect = hb.move(offset.x, offset.y)
                # Голубой цвет для частей тела
                color = (0, 200, 255) 
                if hasattr(target_sprite, 'invulnerable') and target_sprite.invulnerable:
                    color = DEBUG_HITBOX_COLOR_INVUL
                pygame.draw.rect(self.screen, color, draw_rect, 1)
        else:
            # Стандартная отрисовка
            if hasattr(target_sprite, 'get_hitbox_rect'):
                hitbox_rect = target_sprite.get_hitbox_rect()
            else:
                hitbox_rect = target_sprite.rect
                
            draw_rect = hitbox_rect.move(offset.x, offset.y)
            color = DEBUG_HITBOX_COLOR_NORMAL
            if hasattr(target_sprite, 'invulnerable') and target_sprite.invulnerable:
                color = DEBUG_HITBOX_COLOR_INVUL
            pygame.draw.rect(self.screen, color, draw_rect, 1)

    def spawn_enemies(self):
        pass

    def check_collisions(self):
        # *** ИЗМЕНЕНИЕ: Используем complex_collision_check ***
        hits = pygame.sprite.groupcollide(enemies, bullets, False, True, complex_collision_check)
        for enemy, bullet_list in hits.items():
            for bullet in bullet_list:
                bullet.create_impact_vfx()
                enemy.take_damage(bullet.damage)
        
        enemies_hitting_player = pygame.sprite.spritecollide(
            self.player, 
            enemies, 
            False, 
            pygame.sprite.collide_circle 
        )
        
        if enemies_hitting_player:
            if not self.player.is_dashing:
                self.screen_shake.shake(10)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0 
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            self.player.update_custom(dt, enemies, bullets, all_sprites)
            
            for sprite in all_sprites:
                if sprite != self.player:
                    sprite.update(dt)
                
            
            self.check_collisions()
            
            
            shake_offset = self.screen_shake.get_offset()
            self.draw_grid(shake_offset)
            bg_x = -20 + shake_offset.x
            bg_y = -20 + shake_offset.y
            self.screen.blit(self.cave_bg, (bg_x, bg_y))
            
            for sprite in all_sprites:
                # Отрисовка спрайта
                if sprite != self.boss: 
                    draw_pos = sprite.rect.topleft + shake_offset
                    self.screen.blit(sprite.image, draw_pos)

            if self.boss.alive():
                
                # --- Отрисовка Босса ---
                mist_active = self.boss.vfx_mist_active
                mist_timer_val = self.boss.state_timer if self.boss.state == self.boss.STATE_MIST_EFFECT else 0
                
                target_pos_val = self.boss.fixed_target_pos if self.boss.state == self.boss.STATE_MIST_EFFECT else self.player.pos
                
                smite_progress = self.boss.smite_vfx_progress 
                shield_progress = self.boss.shield_animation_progress 
                phase_two = self.boss.is_phase_two
                
                wing_spread = self.boss.wing_spread_factor
                is_trans = self.boss.state == self.boss.STATE_PHASE_TRANSITION
                pose_factor = self.boss.transition_pose_factor
                tilt_x = self.boss.movement_tilt_x 

                draw_archangel_boss(
                    self.screen, 
                    self.boss.pos + shake_offset, 
                    self.boss.time_ticks, 
                    self.boss.spear_animation_progress,
                    mist_active, 
                    mist_timer_val,
                    target_pos_val,
                    smite_progress,
                    shield_progress,
                    phase_two,
                    wing_spread, 
                    is_trans,    
                    pose_factor,  
                    tilt_x 
                )
                
                # Отрисовка UI босса
                self.draw_boss_hud()

                
            
            # *** ОТЛАДКА: Отрисовка хитбокса игрока ***
            self.draw_hitbox(self.player, shake_offset)
            # *** ОТЛАДКА: Отрисовка хитбокса босса ***
            if self.boss.alive():
                self.draw_hitbox(self.boss, shake_offset)


            self.player.skill_manager.draw(self.screen, shake_offset)

            # *** UI: Отображение HP игрока ***
            fps_text = f"FPS: {int(self.clock.get_fps())} | Boss HP: {self.boss.hp} | Player HP: {self.player.hp}"
            fps_surf = self.font.render(fps_text, True, (255, 255, 255))
            self.screen.blit(fps_surf, (10, 10))
            
            skill_cd = max(0, self.player.skill_manager.skills['flurry'].cooldown - (pygame.time.get_ticks() - self.player.skill_manager.skills['flurry'].timer))
            if skill_cd == 0:
                col = (0, 255, 200)
                txt = "E: READY"
            else:
                col = (100, 100, 100)
                txt = f"E: {skill_cd//100/10:.1f}s"
            skill_surf = self.font.render(txt, True, col)
            self.screen.blit(skill_surf, (10, HEIGHT - 30))

              # *** НОВОЕ: Отрисовка кастомных VFX (Smite, Mist) ***
            for sprite in particles:
                if hasattr(sprite, 'draw_custom'):
                    sprite.draw_custom(self.screen, shake_offset)

            pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()

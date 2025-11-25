import pygame
import random
import sys # Нужно для выхода по ESC

# Импорты ядра
from core.config import *
from core.scene_manager import Scene
from core.asset_manager import AssetManager

# Импорты сущностей (пока они в корне)
from player import Player
from enemy import Enemy
from entities.archangel_boss import ArchangelBoss

# Импорты графики и эффектов
from vfx import ScreenShake
from rendering.background import generate_cave_background
from rendering.ui_render import (
    draw_boss_hud_new, 
    draw_player_hud, 
    draw_skill_icon, 
    draw_dash_icon
)
from rendering.archangel_render import draw_archangel_boss
from rendering.portal_render import draw_divine_portal

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ КОЛЛИЗИЙ ---
def complex_collision_check(sprite_a, sprite_b):
    """
    Универсальная проверка коллизий (Hitbox vs Hitbox).
    """
    def intersect(h1, h2):
        def get_shape(h):
            if isinstance(h, pygame.Rect): return ('rect', h)
            return ('circle', h)

        t1, d1 = get_shape(h1)
        t2, d2 = get_shape(h2)

        if t1 == 'rect' and t2 == 'rect':
            return d1.colliderect(d2)
        elif t1 == 'circle' and t2 == 'circle':
            dx = d1['center'][0] - d2['center'][0]
            dy = d1['center'][1] - d2['center'][1]
            r = d1['radius'] + d2['radius']
            return (dx**2 + dy**2) < (r**2)
        else:
            rect = d1 if t1 == 'rect' else d2
            circ = d1 if t1 == 'circle' else d2
            cx, cy = circ['center']
            r = circ['radius']
            closest_x = max(rect.left, min(cx, rect.right))
            closest_y = max(rect.top, min(cy, rect.bottom))
            dx = cx - closest_x
            dy = cy - closest_y
            return (dx**2 + dy**2) < (r**2)

    has_a = hasattr(sprite_a, 'hitboxes') and sprite_a.hitboxes
    has_b = hasattr(sprite_b, 'hitboxes') and sprite_b.hitboxes

    if has_a and has_b:
        for ha in sprite_a.hitboxes:
            for hb in sprite_b.hitboxes:
                if intersect(ha, hb): return True
        return False
    if has_a:
        for ha in sprite_a.hitboxes:
            if intersect(ha, sprite_b.rect): return True
        return False
    if has_b:
        for hb in sprite_b.hitboxes:
            if intersect(sprite_a.rect, hb): return True
        return False

    return pygame.sprite.collide_circle(sprite_a, sprite_b)


class GameScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.assets = AssetManager() # Получаем доступ к ресурсам
        
        # --- Инициализация игрового мира ---
        print("Сцена игры: Инициализация...")
        
        # Очищаем группы спрайтов перед началом
        all_sprites.empty()
        bullets.empty()
        enemies.empty()
        particles.empty()
        
        self.screen_shake = ScreenShake()
        
        # Создаем игрока
        self.player = Player(
            (WIDTH/2, HEIGHT/2), 
            all_sprites, 
            None, 
            [all_sprites, particles],
            self.screen_shake.shake
        )
        
        # Создаем босса
        self.boss = ArchangelBoss(WIDTH/2, HEIGHT/2, self.player)
        
        # Генерация фона
        self.cave_bg = generate_cave_background()
        
        self.auto_spawn_timer = 120 

    def enter(self):
        """Вызывается при входе в сцену."""
        print("Сцена игры: Старт")
        self.assets.play_music()

    def handle_input(self, events):
        """Обработка событий (нажатия кнопок, которые не обрабатывает игрок)."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                     self.boss.spawn_boss()
                # В будущем здесь можно сделать паузу вместо выхода
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def update(self, dt):
        """Обновление логики игры."""
        # Автоспавн босса (таймер)
        if self.auto_spawn_timer > 0:
            self.auto_spawn_timer -= 1
            if self.auto_spawn_timer == 0:
                self.boss.spawn_boss()
                self.assets.play_music() # На всякий случай убеждаемся, что музыка играет

        # Обновление игрока
        self.player.update_custom(dt, enemies, bullets, all_sprites)
        
        # Обновление остальных спрайтов
        for sprite in all_sprites:
            if sprite != self.player:
                sprite.update(dt)
        
        # Проверка коллизий
        self.check_collisions()

    def check_collisions(self):
        # Попадание пуль во врагов
        hits = pygame.sprite.groupcollide(enemies, bullets, False, True, complex_collision_check)
        for enemy, bullet_list in hits.items():
            for bullet in bullet_list:
                bullet.create_impact_vfx()
                enemy.take_damage(bullet.damage)
        
        # Столкновение врагов с игроком
        enemies_hitting_player = pygame.sprite.spritecollide(
            self.player, 
            enemies, 
            False, 
            pygame.sprite.collide_circle 
        )
        if enemies_hitting_player:
            if not self.player.is_dashing:
                self.screen_shake.shake(10)

    def draw(self, screen):
        """Отрисовка всего."""
        shake_offset = self.screen_shake.get_offset()
        
        # 1. Фон
        self.draw_grid(screen, shake_offset)
        bg_x = -20 + shake_offset.x
        bg_y = -20 + shake_offset.y
        screen.blit(self.cave_bg, (bg_x, bg_y))
        
        # 2. Портал (если нужен)
        is_boss_intro = self.boss.state == self.boss.STATE_INTRO
        if is_boss_intro:
            portal_center = (self.boss.spawn_pos.x + shake_offset.x, (self.boss.spawn_pos.y - 400) + shake_offset.y)
            draw_divine_portal(screen, portal_center, self.boss.intro_portal_progress, self.boss.time_ticks)
        
        # 3. Спрайты (кроме босса, он рисуется отдельно для красоты)
        for sprite in all_sprites:
            if sprite != self.boss: 
                draw_pos = sprite.rect.topleft + shake_offset
                screen.blit(sprite.image, draw_pos)
        
        # 4. Босс (Специальная отрисовка)
        if self.boss.alive() and (self.boss.is_active or is_boss_intro):
            # Собираем параметры для рендера
            mist_active = self.boss.vfx_mist_active
            mist_timer_val = self.boss.state_timer if self.boss.state == self.boss.STATE_MIST_EFFECT else 0
            target_pos_val = self.boss.fixed_target_pos if self.boss.state == self.boss.STATE_MIST_EFFECT else self.player.pos
            
            death_data = {
                'pose_factor': getattr(self.boss, 'death_pose_factor', 0.0),
                'item_alpha': getattr(self.boss, 'death_item_alpha', 255),
                'wing_alpha': getattr(self.boss, 'death_wing_alpha', 255),
                'wing_offset': getattr(self.boss, 'death_wing_offset', 0.0),
                'light_scale': getattr(self.boss, 'death_light_scale', 0.0),
                'flash_alpha': getattr(self.boss, 'death_flash_alpha', 0)
            }
            
            draw_archangel_boss(
                screen, 
                self.boss.pos + shake_offset, 
                self.boss.time_ticks, 
                self.boss.spear_animation_progress,
                mist_active, 
                mist_timer_val,
                target_pos_val,
                self.boss.smite_vfx_progress,
                self.boss.shield_animation_progress,
                self.boss.is_phase_two,
                self.boss.wing_spread_factor, 
                self.boss.state == self.boss.STATE_PHASE_TRANSITION,    
                self.boss.transition_pose_factor,  
                self.boss.movement_tilt_x,
                alpha=getattr(self.boss, 'current_alpha', 255),
                is_final_attack=(self.boss.state == self.boss.STATE_CHAOS_BARRAGE),
                death_params=death_data
            )
            
            # HUD Босса
            if self.boss.state != self.boss.STATE_HIDDEN:
                 draw_boss_hud_new(
                     screen, 
                     self.boss, 
                     self.assets.get_boss_icon(), 
                     self.assets.get_font_boss_name(), 
                     self.assets.get_font_boss_title()
                 )

        # 5. VFX и Интерфейс Игрока
        self.player.skill_manager.draw(screen, shake_offset)
        
        draw_player_hud(
            screen, 
            self.player, 
            self.assets.get_font_boss_name(), 
            self.assets.get_font_boss_title()
        )
        
        # Иконки скиллов
        skill_x = 20
        skill_y = 20 + 80 + 10 
        icon_size = 50
        icon_padding = 10
        
        draw_skill_icon(
            screen, 
            self.player.skill_manager.skills['flurry'], 
            (skill_x, skill_y), 
            self.assets.get_font_ui()
        )
        draw_dash_icon(
            screen,
            self.player,
            (skill_x + icon_size + icon_padding, skill_y),
            self.assets.get_font_ui()
        )
        
        # Частицы (отрисовка кастомная)
        for sprite in particles:
            if hasattr(sprite, 'draw_custom'):
                sprite.draw_custom(screen, shake_offset)

    def draw_grid(self, screen, offset):
        start_x = int(-offset.x) % TILE_SIZE
        start_y = int(-offset.y) % TILE_SIZE
        for x in range(start_x, WIDTH, TILE_SIZE):
            pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, HEIGHT))
        for y in range(start_y, HEIGHT, TILE_SIZE):
            pygame.draw.line(screen, COLOR_GRID, (0, y), (WIDTH, y))
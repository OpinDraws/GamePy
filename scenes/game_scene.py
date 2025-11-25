import pygame
import sys

# Импорты ядра
from core.config import *
from core.scene_manager import Scene
from core.asset_manager import AssetManager
from core.camera import Camera

# Импорты мира и сущностей
from world.tile_map import Map
from player import Player
# Не забудь поменять импорт на правильный, если переносил файл
# from entities.tentacle_enemy import TentacleEnemy (если будем спавнить врагов)
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

# Вспомогательная функция коллизий (оставляем как есть)
def complex_collision_check(sprite_a, sprite_b):
    def intersect(h1, h2):
        def get_shape(h):
            if isinstance(h, pygame.Rect): return ('rect', h)
            return ('circle', h)
        t1, d1 = get_shape(h1)
        t2, d2 = get_shape(h2)
        if t1 == 'rect' and t2 == 'rect': return d1.colliderect(d2)
        elif t1 == 'circle' and t2 == 'circle':
            return (d1['center'][0]-d2['center'][0])**2 + (d1['center'][1]-d2['center'][1])**2 < (d1['radius']+d2['radius'])**2
        else:
            rect = d1 if t1 == 'rect' else d2
            circ = d1 if t1 == 'circle' else d2
            cx, cy = circ['center']
            closest_x = max(rect.left, min(cx, rect.right))
            closest_y = max(rect.top, min(cy, rect.bottom))
            return (cx-closest_x)**2 + (cy-closest_y)**2 < circ['radius']**2

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
        self.assets = AssetManager()
        
        print("Сцена игры: Инициализация мира...")
        
        all_sprites.empty()
        bullets.empty()
        enemies.empty()
        particles.empty()
        
        self.screen_shake = ScreenShake()
        
        # 1. ГЕНЕРАЦИЯ КАРТЫ
        # Создаем большую "комнату" (60x40 тайлов = 2400x1600 пикселей)
        map_layout = []
        cols = 60 
        rows = 40
        
        # Верхняя стена
        map_layout.append('#' * cols)
        # Середина (пустота со стенами по бокам)
        for _ in range(rows - 2):
            map_layout.append('#' + '.' * (cols - 2) + '#')
        # Нижняя стена
        map_layout.append('#' * cols)

        self.map = Map(map_layout)
        
        # 2. КАМЕРА
        self.camera = Camera(self.map.width, self.map.height)

        # 3. ИГРОК
        # Спавним игрока в центре карты
        start_pos = (self.map.width / 2, self.map.height / 2)
        self.player = Player(
            start_pos, 
            all_sprites, 
            self.map.obstacles, # ВАЖНО: Передаем группу стен игроку
            [all_sprites, particles],
            self.screen_shake.shake
        )
        
        # 4. БОСС
        # Босс тоже спавнится относительно центра карты
        self.boss = ArchangelBoss(self.map.width / 2, self.map.height / 2, self.player)
        
        # Фон пещеры
        self.cave_bg = generate_cave_background()
        self.auto_spawn_timer = 60 

    def enter(self):
        print("Сцена игры: Старт")
        self.assets.play_music()

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                     self.boss.spawn_boss()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def update(self, dt):
        # Автоспавн босса
        if self.auto_spawn_timer > 0:
            self.auto_spawn_timer -= 1
            if self.auto_spawn_timer == 0:
                self.boss.spawn_boss()
                self.assets.play_music()

        self.player.update_custom(dt, enemies, bullets, all_sprites)
        
        for sprite in all_sprites:
            if sprite != self.player:
                sprite.update(dt)
        
        # ВАЖНО: Обновляем камеру, чтобы она следила за игроком
        self.camera.update(self.player.rect)
        
        self.check_collisions()

    def check_collisions(self):
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

    def draw(self, screen):
        # Получаем смещение от тряски
        shake = self.screen_shake.get_offset()
        # Итоговое смещение = Камера + Тряска
        total_offset = self.camera.offset + shake
        
        # 1. Фон (рисуем с небольшим параллаксом или просто со смещением)
        screen.blit(self.cave_bg, (total_offset.x - 20, total_offset.y - 20))
        
        # 2. Стены карты
        for tile in self.map.all_map_sprites:
            screen.blit(tile.image, tile.rect.topleft + total_offset)
        
        # 3. Портал Интро
        is_boss_intro = self.boss.state == self.boss.STATE_INTRO
        if is_boss_intro:
            portal_pos = self.boss.spawn_pos + total_offset
            # Смещаем портал выше точки спавна
            portal_draw_pos = (portal_pos.x, portal_pos.y - 400)
            draw_divine_portal(screen, portal_draw_pos, self.boss.intro_portal_progress, self.boss.time_ticks)
        
        # 4. Спрайты (Игрок, снаряды, враги)
        # Рисуем все спрайты со смещением камеры!
        for sprite in all_sprites:
            if sprite != self.boss: # Босс рисуется отдельно через спец функцию
                screen.blit(sprite.image, sprite.rect.topleft + total_offset)
        
        # 5. Босс (Специальная отрисовка)
        if self.boss.alive() and (self.boss.is_active or is_boss_intro):
            # Собираем параметры смерти
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
                self.boss.pos + total_offset,  # ВАЖНО: Позиция + Камера
                self.boss.time_ticks, 
                self.boss.spear_animation_progress,
                self.boss.vfx_mist_active, 
                self.boss.state_timer if self.boss.state == self.boss.STATE_MIST_EFFECT else 0,
                self.boss.fixed_target_pos if self.boss.state == self.boss.STATE_MIST_EFFECT else self.player.pos,
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
            
            # HUD Босса (Рисуется поверх всего, БЕЗ смещения камеры)
            if self.boss.state != self.boss.STATE_HIDDEN:
                 draw_boss_hud_new(
                     screen, 
                     self.boss, 
                     self.assets.get_boss_icon(), 
                     self.assets.get_font_boss_name(), 
                     self.assets.get_font_boss_title()
                 )

        # 6. VFX и UI Игрока (Поверх всего)
        self.player.skill_manager.draw(screen, total_offset)
        
        draw_player_hud(
            screen, 
            self.player, 
            self.assets.get_font_boss_name(), 
            self.assets.get_font_boss_title()
        )
        
        # Иконки
        skill_x = 20
        skill_y = 20 + 80 + 10 
        icon_size = 50
        draw_skill_icon(screen, self.player.skill_manager.skills['flurry'], (skill_x, skill_y), self.assets.get_font_ui())
        draw_dash_icon(screen, self.player, (skill_x + icon_size + 10, skill_y), self.assets.get_font_ui())
        
        # Частицы
        for sprite in particles:
            if hasattr(sprite, 'draw_custom'):
                sprite.draw_custom(screen, total_offset)
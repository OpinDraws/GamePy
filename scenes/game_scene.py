# scenes/game_scene.py

import pygame
import sys

from core.config import *
from core.scene_manager import Scene
from core.asset_manager import AssetManager
from core.camera import Camera
from core.save_manager import SaveManager, get_default_save_data

from world.tile_map import Map, Tile 
from world.world_manager import WorldManager 
from entities.player import Player
from entities.bosses.archangel_boss import ArchangelBoss
from entities.gate import Gate
from entities.tentacle_enemy import TentacleEnemy

from systems.vfx import ScreenShake
from rendering.background import generate_cave_background
from rendering.ui_render import (
    draw_boss_hud_new, 
    draw_player_hud, 
    draw_skill_icon, 
    draw_dash_icon
)
from rendering.archangel_render import draw_archangel_boss
from rendering.portal_render import draw_divine_portal

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
        
        self.save_data = SaveManager.load_game()
        if self.save_data is None:
            self.save_data = get_default_save_data()
        
        start_pos = self.save_data["spawn_pos"]
        current_room = self.save_data["current_room"]
        
        self.camera = Camera(2000, 3200) 

        self.player = Player(
            start_pos, 
            all_sprites, 
            None, 
            [all_sprites, particles],
            self.screen_shake.shake,
            self.on_player_death 
        )
        self.player.hp = self.save_data["hp"]
        self.player.max_hp = self.save_data["max_hp"]
        
        self.world_manager = WorldManager(
            self.player,
            self.camera,
            self.screen_shake.shake,
            complex_collision_check 
        )

        # 1. СНАЧАЛА ЗАГРУЖАЕМ КОМНАТУ (Это создает стены и очищает старых врагов)
        self.world_manager.load_room(current_room, start_pos) 
        
        # 2. ТЕПЕРЬ СОЗДАЕМ ВАШИХ МОНСТРОВ (Чтобы они добавились в чистую группу enemies)
        
        # Монстр 1 (Слева)
        pos_m1 = self.player.pos + pygame.math.Vector2(-60, 50) # -60 чтобы не перекрывать игрока, если стоять вплотную
        m1 = TentacleEnemy(
            pos_m1, 
            self.player, 
            [all_sprites, enemies], # Теперь enemies не очистится после этого
            [all_sprites, particles], 
            self.screen_shake.shake
        )
        m1.health = 150
        m1.base_speed = 0            
        m1.attention_state = 'FOCUS' 
        m1.attention_timer = -99999 

        # Монстр 2 (Справа)
        pos_m2 = self.player.pos + pygame.math.Vector2(60, 50)
        m2 = TentacleEnemy(
            pos_m2, 
            self.player, 
            [all_sprites, enemies], 
            [all_sprites, particles], 
            self.screen_shake.shake
        )
        m2.health = 150
        m2.base_speed = 0
        m2.attention_state = 'FOCUS'
        m2.attention_timer = -99999
        # --------------------------------------------
        
        self.boss = ArchangelBoss(-1000, -1000, self.player)
        self.boss.set_state(self.boss.STATE_HIDDEN) 
        self.boss.invulnerable = True
        
        self.auto_spawn_timer = -1 
        self.game_over = False
        self.death_timer = 0
        
        self.cave_bg = generate_cave_background()

    def enter(self):
        print("Сцена игры: Старт")
        # Музыка теперь запускается в update
        
    def on_player_death(self):
        if not self.game_over:
            print("Игрок мертв. Запускаем Game Over таймер.")
            self.game_over = True
            self.death_timer = 60 

    def handle_input(self, events):
        if self.game_over: return 
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    player_data = self.player.get_save_data()
                    world_data = {
                        "current_room": self.world_manager.current_room,
                        "spawn_pos": [self.player.pos.x, self.player.pos.y] 
                    }
                    SaveManager.save_game(player_data, world_data)

                if event.key == pygame.K_ESCAPE:
                    print("GameScene: Выход в меню")
                    from scenes.menu_scene import MenuScene
                    menu_scene = MenuScene(self.manager)
                    self.manager.switch_to(menu_scene)

    def update(self, dt):
        if self.game_over:
            self.death_timer -= 1
            if self.death_timer <= 0:
                from scenes.game_over_scene import GameOverScene
                self.manager.switch_to(GameOverScene(self.manager))
            
            for sprite in all_sprites:
                if sprite != self.player:
                    sprite.update(dt)
            for sprite in particles:
                sprite.update(dt)

            self.screen_shake.update(dt)
            return 

        self.world_manager.update(dt) 
        self.player.update_custom(dt, enemies, bullets, all_sprites, self.camera.offset) 
        
        for sprite in all_sprites:
            if sprite != self.player:
                sprite.update(dt)
        
        self.camera.update(self.player.rect)
        self.screen_shake.update(dt)
        self.check_collisions()

        # --- ЛОГИКА ТРИГГЕРОВ (Обновленные координаты) ---
        
        # 1. Ворота (Y ~ 2000)
        GATE_TRIGGER_Y = 2200 # Открываем, когда подходим снизу
        if self.player.pos.y < GATE_TRIGGER_Y:
            for gate in self.world_manager.gates:
                gate.open()

        # 2. Босс (Y ~ 2000 - вход)
        BOSS_TRIGGER_Y = 1500 
        
        if self.boss.state == self.boss.STATE_HIDDEN and self.player.pos.y < BOSS_TRIGGER_Y:
            print("Триггер босса сработал!")
            
            # --- ВАЖНО: Устанавливаем точку назначения ---
            # Было (1000, 1000) - это слишком низко.
            # Ставим (1000, 600) - это выше по экрану (меньше Y).
            # Босс появится еще выше (в портале) и спустится сюда.
            self.boss.spawn_pos = pygame.math.Vector2(1000, 1000)
            
            # Запускаем интро
            self.boss.spawn_boss()
            self.assets.play_music()

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
        shake = self.screen_shake.get_offset()
        total_offset = self.camera.offset + shake
        
        screen.blit(self.cave_bg, (total_offset.x - 20, total_offset.y - 20))
        self.world_manager.draw_map(screen, total_offset)
        
        # Рисуем портал
        if self.boss.state == self.boss.STATE_INTRO:
            portal_pos = self.boss.spawn_pos + total_offset
            # Портал рисуется выше целевой точки
            portal_draw_pos = (portal_pos.x, portal_pos.y - self.boss.portal_offset_y)
            draw_divine_portal(screen, portal_draw_pos, self.boss.intro_portal_progress, self.boss.time_ticks)
        
        for sprite in all_sprites:
            if sprite != self.boss and not isinstance(sprite, Tile) and not isinstance(sprite, Gate): 
                screen.blit(sprite.image, sprite.rect.topleft + total_offset)
        
        if self.boss.alive() and self.boss.state != self.boss.STATE_HIDDEN: 
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
                self.boss.pos + total_offset, 
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
            
            draw_boss_hud_new(
                screen, 
                self.boss, 
                self.assets.get_boss_icon(), 
                self.assets.get_font_boss_name(), 
                self.assets.get_font_boss_title()
            )

        self.player.skill_manager.draw(screen, total_offset)
        
        draw_player_hud(
            screen, 
            self.player, 
            self.assets.get_font_boss_name(), 
            self.assets.get_font_boss_title()
        )
        
        skill_x = 20
        skill_y = 20 + 80 + 10 
        draw_skill_icon(screen, self.player.skill_manager.skills['flurry'], (skill_x, skill_y), self.assets.get_font_ui())
        draw_dash_icon(screen, self.player, (skill_x + 60, skill_y), self.assets.get_font_ui())
        
        for sprite in particles:
            if hasattr(sprite, 'draw_custom'):
                sprite.draw_custom(screen, total_offset)
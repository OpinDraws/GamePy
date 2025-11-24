import pygame
import sys
import random
import math 
from config import *
from player import Player
from enemy import Enemy
from vfx import ScreenShake

# Импорты рендеринга
from rendering.ui_render import draw_archangel_portrait, draw_boss_hud_new, draw_player_hud, draw_skill_icon, draw_dash_icon
from rendering.background import generate_cave_background
from entities.archangel_boss import ArchangelBoss 
from rendering.archangel_render import draw_archangel_boss
from rendering.portal_render import draw_divine_portal

# Константы для отладки
DEBUG_HITBOX_COLOR_NORMAL = (0, 255, 0) 
DEBUG_HITBOX_COLOR_INVUL = (255, 0, 0)  

# --- УМНАЯ ФУНКЦИЯ КОЛЛИЗИЙ (Hitbox vs Hitbox) ---
def complex_collision_check(sprite_a, sprite_b):
    """
    Универсальная проверка коллизий. 
    Поддерживает списки хитбоксов (rect/circle) у обоих объектов.
    """
    # Вспомогательная функция: пересекается ли Фигура 1 с Фигурой 2?
    def intersect(h1, h2):
        # 1. Приводим к стандарту: (type, data)
        # Rect -> ('rect', Rect)
        # Dict -> ('circle', dict)
        
        def get_shape(h):
            if isinstance(h, pygame.Rect): return ('rect', h)
            return ('circle', h)

        t1, d1 = get_shape(h1)
        t2, d2 = get_shape(h2)

        # --- RECT vs RECT ---
        if t1 == 'rect' and t2 == 'rect':
            return d1.colliderect(d2)
        
        # --- CIRCLE vs CIRCLE ---
        elif t1 == 'circle' and t2 == 'circle':
            dx = d1['center'][0] - d2['center'][0]
            dy = d1['center'][1] - d2['center'][1]
            r = d1['radius'] + d2['radius']
            return (dx**2 + dy**2) < (r**2)

        # --- RECT vs CIRCLE ---
        else:
            # Определяем, кто круг, кто рект
            rect = d1 if t1 == 'rect' else d2
            circ = d1 if t1 == 'circle' else d2
            
            cx, cy = circ['center']
            r = circ['radius']
            
            closest_x = max(rect.left, min(cx, rect.right))
            closest_y = max(rect.top, min(cy, rect.bottom))
            
            dx = cx - closest_x
            dy = cy - closest_y
            return (dx**2 + dy**2) < (r**2)

    # Логика выбора проверки
    has_a = hasattr(sprite_a, 'hitboxes') and sprite_a.hitboxes
    has_b = hasattr(sprite_b, 'hitboxes') and sprite_b.hitboxes

    # 1. Если у ОБОИХ есть детальные хитбоксы -> проверяем "Каждый с Каждым"
    if has_a and has_b:
        for ha in sprite_a.hitboxes:
            for hb in sprite_b.hitboxes:
                if intersect(ha, hb): return True
        return False

    # 2. Если только у A есть хитбоксы -> проверяем их об B.rect
    if has_a:
        for ha in sprite_a.hitboxes:
            if intersect(ha, sprite_b.rect): return True
        return False

    # 3. Если только у B есть хитбоксы -> проверяем их об A.rect
    if has_b:
        for hb in sprite_b.hitboxes:
            if intersect(sprite_a.rect, hb): return True
        return False

    # 4. Иначе -> простая проверка кругов (стандарт для спрайтов)
    return pygame.sprite.collide_circle(sprite_a, sprite_b)

class Game:
    # ... (ВЕСЬ ОСТАЛЬНОЙ КОД КЛАССА GAME БЕЗ ИЗМЕНЕНИЙ) ...
    # ... (Скопируйте содержимое класса Game из предыдущего шага, там ничего менять не надо) ...
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gothic Procedural Arena - ARCHANGEL BOSS")
        self.clock = pygame.time.Clock()
        print("Генерирую пещеру...")
        self.cave_bg = generate_cave_background()
        print("Готово.")
        serif_font_path = pygame.font.match_font('cambria, georgia, timesnewroman, serif')
        self.font_boss_name = pygame.font.Font(serif_font_path, 28)
        self.font_boss_name.set_bold(True)
        self.font_boss_title = pygame.font.Font(serif_font_path, 18)
        self.font_boss_title.set_italic(True)
        self.font = pygame.font.SysFont("Arial", 18)
        try:
            original_image = pygame.image.load('boss_icon.jpg').convert()
            self.boss_portrait = pygame.transform.smoothscale(original_image, (80, 80))
            self.boss_portrait = pygame.transform.flip(self.boss_portrait, True, False)
        except:
            print("Ошибка: файл boss_icon.jpg не найден.")
            self.boss_portrait = pygame.Surface((80, 80))
            self.boss_portrait.fill((50, 0, 50))
        self.screen_shake = ScreenShake()
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
        self.boss = ArchangelBoss(WIDTH/2, HEIGHT/2, self.player)
        self.auto_spawn_timer = 120 

    def spawn_enemies(self):
        pass

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

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0 
            if self.auto_spawn_timer > 0:
                self.auto_spawn_timer -= 1
                if self.auto_spawn_timer == 0:
                    self.boss.spawn_boss()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                         self.boss.spawn_boss()
                    if event.key == pygame.K_ESCAPE:
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
            is_boss_intro = self.boss.state == self.boss.STATE_INTRO
            if is_boss_intro:
                portal_center = (self.boss.spawn_pos.x + shake_offset.x, (self.boss.spawn_pos.y - 400) + shake_offset.y)
                draw_divine_portal(self.screen, portal_center, self.boss.intro_portal_progress, self.boss.time_ticks)
            for sprite in all_sprites:
                if sprite != self.boss: 
                    draw_pos = sprite.rect.topleft + shake_offset
                    self.screen.blit(sprite.image, draw_pos)
            if self.boss.alive() and (self.boss.is_active or is_boss_intro):
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
                is_final = self.boss.state == self.boss.STATE_CHAOS_BARRAGE
                boss_alpha = getattr(self.boss, 'current_alpha', 255)
                death_data = {
                    'pose_factor': getattr(self.boss, 'death_pose_factor', 0.0),
                    'item_alpha': getattr(self.boss, 'death_item_alpha', 255),
                    'wing_alpha': getattr(self.boss, 'death_wing_alpha', 255),
                    'wing_offset': getattr(self.boss, 'death_wing_offset', 0.0),
                    'light_scale': getattr(self.boss, 'death_light_scale', 0.0),
                    'flash_alpha': getattr(self.boss, 'death_flash_alpha', 0)
                }
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
                    tilt_x,
                    alpha=boss_alpha,
                    is_final_attack=is_final,
                    death_params=death_data
                )
                if self.boss.state != self.boss.STATE_HIDDEN:
                     draw_boss_hud_new(self.screen, self.boss, self.boss_portrait, self.font_boss_name, self.font_boss_title)
            # self.draw_hitbox(self.player, shake_offset)
            # if self.boss.alive() and self.boss.is_active:
            #     self.draw_hitbox(self.boss, shake_offset)
            self.player.skill_manager.draw(self.screen, shake_offset)
            draw_player_hud(self.screen, self.player, self.font_boss_name, self.font_boss_title)
            skill_x = 20
            skill_y = 20 + 80 + 10 
            icon_size = 50
            icon_padding = 10
            draw_skill_icon(
                self.screen, 
                self.player.skill_manager.skills['flurry'], 
                (skill_x, skill_y), 
                self.font 
            )
            dash_x = skill_x + icon_size + icon_padding
            dash_y = skill_y
            draw_dash_icon(
                self.screen,
                self.player,
                (dash_x, dash_y),
                self.font
            )
            for sprite in particles:
                if hasattr(sprite, 'draw_custom'):
                    sprite.draw_custom(self.screen, shake_offset)
            pygame.display.flip()

    def draw_grid(self, offset):
        start_x = int(-offset.x) % TILE_SIZE
        start_y = int(-offset.y) % TILE_SIZE
        for x in range(start_x, WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, HEIGHT))
        for y in range(start_y, HEIGHT, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (WIDTH, y))

    def draw_hitbox(self, target_sprite, offset):
        if hasattr(target_sprite, 'hitboxes') and target_sprite.hitboxes:
            for hb in target_sprite.hitboxes:
                color = (0, 200, 255) 
                if hasattr(target_sprite, 'invulnerable') and target_sprite.invulnerable:
                    color = DEBUG_HITBOX_COLOR_INVUL
                
                if isinstance(hb, pygame.Rect):
                    draw_rect = hb.move(offset.x, offset.y)
                    pygame.draw.rect(self.screen, color, draw_rect, 1)
                elif isinstance(hb, dict) and hb['type'] == 'circle':
                    cx, cy = hb['center']
                    r = hb['radius']
                    draw_pos = (int(cx + offset.x), int(cy + offset.y))
                    pygame.draw.circle(self.screen, color, draw_pos, int(r), 1)
        else:
            if hasattr(target_sprite, 'get_hitbox_rect'):
                hitbox_rect = target_sprite.get_hitbox_rect()
            else:
                hitbox_rect = target_sprite.rect
            draw_rect = hitbox_rect.move(offset.x, offset.y)
            color = DEBUG_HITBOX_COLOR_NORMAL
            if hasattr(target_sprite, 'invulnerable') and target_sprite.invulnerable:
                color = DEBUG_HITBOX_COLOR_INVUL
            pygame.draw.rect(self.screen, color, draw_rect, 1)

if __name__ == '__main__':
    game = Game()
    game.run()
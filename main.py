import pygame
import sys
import random
import math 
from config import *
from player import Player
from enemy import Enemy
from vfx import ScreenShake

# Импорты рендеринга
from rendering.ui_render import draw_archangel_portrait, draw_boss_hud_new # Новая функция
from rendering.background import generate_cave_background
from entities.archangel_boss import ArchangelBoss 
from rendering.archangel_render import draw_archangel_boss
# Импорт портала
from rendering.portal_render import draw_divine_portal
from rendering.ui_render import draw_archangel_portrait, draw_boss_hud_new, draw_player_hud, draw_skill_icon
from rendering.ui_render import draw_archangel_portrait, draw_boss_hud_new, draw_player_hud, draw_skill_icon, draw_dash_icon # <-- Добавлено draw_dash_icon

# Константы для отладки
DEBUG_HITBOX_COLOR_NORMAL = (0, 255, 0) 
DEBUG_HITBOX_COLOR_INVUL = (255, 0, 0)  

def complex_collision_check(sprite_a, sprite_b):
    if hasattr(sprite_a, 'hitboxes') and sprite_a.hitboxes:
        for hb in sprite_a.hitboxes:
            if hb.colliderect(sprite_b.rect): return True
        return False
    if hasattr(sprite_b, 'hitboxes') and sprite_b.hitboxes:
        for hb in sprite_b.hitboxes:
            if hb.colliderect(sprite_a.rect): return True
        return False
    return pygame.sprite.collide_circle(sprite_a, sprite_b)

class Game:
    def __init__(self):
        pygame.init()
        
        # 1. Обычное окно, но с новым большим разрешением из config.py
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
        pygame.display.set_caption("Gothic Procedural Arena - ARCHANGEL BOSS")
        self.clock = pygame.time.Clock()

        print("Генерирую пещеру...")
        self.cave_bg = generate_cave_background()
        print("Готово.")
        
        # Шрифты
        serif_font_path = pygame.font.match_font('cambria, georgia, timesnewroman, serif')
        self.font_boss_name = pygame.font.Font(serif_font_path, 28)
        self.font_boss_name.set_bold(True)
        self.font_boss_title = pygame.font.Font(serif_font_path, 18)
        self.font_boss_title.set_italic(True)
        self.font = pygame.font.SysFont("Arial", 18)
        
        # Портрет
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
        
        # Создаем босса, но он СКРЫТ
        self.boss = ArchangelBoss(WIDTH/2, HEIGHT/2, self.player)
        
        # Можно автоматически запустить спавн через 2 секунды для демонстрации
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
            
            # Автоспавн для демо (убери, если не нужно)
            if self.auto_spawn_timer > 0:
                self.auto_spawn_timer -= 1
                if self.auto_spawn_timer == 0:
                    self.boss.spawn_boss()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # Тестовая кнопка P для призыва
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                         self.boss.spawn_boss()
            
            self.player.update_custom(dt, enemies, bullets, all_sprites)
            
            # Обновляем все спрайты (включая босса)
            for sprite in all_sprites:
                if sprite != self.player:
                    sprite.update(dt)
            
            self.check_collisions()
            
            shake_offset = self.screen_shake.get_offset()
            self.draw_grid(shake_offset)
            bg_x = -20 + shake_offset.x
            bg_y = -20 + shake_offset.y
            self.screen.blit(self.cave_bg, (bg_x, bg_y))
            
            # --- ОТРИСОВКА ---
            
            # 1. Сначала рисуем портал (если босс в интро и он открыт), чтобы босс был ПЕРЕД ним
            # Или ПОЗАДИ? Обычно выходят ИЗ портала.
            # Давайте нарисуем Портал -> Босс -> Свечение портала
            
            is_boss_intro = self.boss.state == self.boss.STATE_INTRO
            if is_boss_intro:
                # Портал рисуем на высоте portal_offset_y (400px) над точкой спавна
                portal_center = (self.boss.spawn_pos.x + shake_offset.x, (self.boss.spawn_pos.y - 400) + shake_offset.y)
                draw_divine_portal(self.screen, portal_center, self.boss.intro_portal_progress, self.boss.time_ticks)

            # 2. Обычные спрайты
            for sprite in all_sprites:
                if sprite != self.boss: 
                    draw_pos = sprite.rect.topleft + shake_offset
                    self.screen.blit(sprite.image, draw_pos)

            # 3. Босс (рисуем, только если активен или в интро)
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

                # Достаем alpha (если переменной нет, по умолчанию 255)
                is_final = self.boss.state == self.boss.STATE_CHAOS_BARRAGE
                boss_alpha = getattr(self.boss, 'current_alpha', 255)
                
                # Собираем параметры смерти
                death_data = {
                    'pose_factor': getattr(self.boss, 'death_pose_factor', 0.0),
                    'item_alpha': getattr(self.boss, 'death_item_alpha', 255),
                    'wing_alpha': getattr(self.boss, 'death_wing_alpha', 255),
                    'wing_offset': getattr(self.boss, 'death_wing_offset', 0.0),
                    
                    # НОВЫЕ ПАРАМЕТРЫ
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
                    death_params=death_data # <--- НОВЫЙ ПАРАМЕТР
                )
                
                # Рисуем интерфейс босса (НОВАЯ ФУНКЦИЯ)
                # Показываем только если интро почти закончилось или идет бой
                if self.boss.state != self.boss.STATE_HIDDEN:
                     draw_boss_hud_new(self.screen, self.boss, self.boss_portrait, self.font_boss_name, self.font_boss_title)
            
            # 4. Отладка Хитбоксов
           # self.draw_hitbox(self.player, shake_offset)
          #  if self.boss.alive() and self.boss.is_active:
            #    self.draw_hitbox(self.boss, shake_offset)

            self.player.skill_manager.draw(self.screen, shake_offset)

            # 1. HUD Босса (Справа)
            if self.boss.state != self.boss.STATE_HIDDEN:
                 draw_boss_hud_new(self.screen, self.boss, self.boss_portrait, self.font_boss_name, self.font_boss_title)
            
            # 2. HUD Игрока (Слева - НОВОЕ)
            draw_player_hud(self.screen, self.player, self.font_boss_name, self.font_boss_title)
            
            # 3. Скилл (Отдельный квадрат - НОВОЕ)
            # Рисуем под портретом игрока или в углу. Давайте сделаем аккуратно под баром HP.
            # Координаты: margin_left (20) + отступ, margin_top (20) + высота бара (60) + отступ
            skill_x = 20
            skill_y = 20 + 80 + 10 # Под портретом

            icon_size = 50
            icon_padding = 10
            
            draw_skill_icon(
                self.screen, 
                self.player.skill_manager.skills['flurry'], 
                (skill_x, skill_y), 
                self.font # Используем обычный шрифт для таймера
            )

            # 4. Дэш (SPACE - Сапог) - НОВОЕ
            # Рисуем справа от первой иконки
            dash_x = skill_x + icon_size + icon_padding
            dash_y = skill_y
            
            draw_dash_icon(
                self.screen,
                self.player, # Передаем объект игрока для проверки КД
                (dash_x, dash_y),
                self.font
            )

            # 4. УБРАНО: Старый текст FPS и Boss State
            # fps_text = f"FPS: {int(self.clock.get_fps())} | Boss State: {self.boss.state}"
            # self.screen.blit(fps_surf, (10, 10)) # <-- ЭТО УБРАЛИ
            
            # 5. УБРАНО: Старый текст скилла
            # skill_cd = ... 
            # self.screen.blit(skill_surf, (10, HEIGHT - 30)) # <-- ЭТО УБРАЛИ

            # VFX (оставляем)
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
                draw_rect = hb.move(offset.x, offset.y)
                color = (0, 200, 255) 
                if hasattr(target_sprite, 'invulnerable') and target_sprite.invulnerable:
                    color = DEBUG_HITBOX_COLOR_INVUL
                pygame.draw.rect(self.screen, color, draw_rect, 1)
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
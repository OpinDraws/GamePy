import pygame
import sys
import random
import math 
from config import *
from player import Player
from enemy import Enemy
from vfx import ScreenShake

from entities.archangel_boss import ArchangelBoss 
from rendering.archangel_render import draw_archangel_boss

# Константы для отладки
DEBUG_HITBOX_COLOR_NORMAL = (0, 255, 0) # Зеленый
DEBUG_HITBOX_COLOR_INVUL = (255, 0, 0)  # Красный

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gothic Procedural Arena - ARCHANGEL BOSS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        
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
        
        # Спавн Архангела
        self.boss = ArchangelBoss(WIDTH/2, HEIGHT/2 - 300, self.player)
        
        self.spawn_timer = 0
        self.spawn_rate = 9999999  # Отключаем монстров

    def draw_grid(self, offset):
        start_x = int(-offset.x) % TILE_SIZE
        start_y = int(-offset.y) % TILE_SIZE
        for x in range(start_x, WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, HEIGHT))
        for y in range(start_y, HEIGHT, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (WIDTH, y))

    # *** НОВАЯ ФУНКЦИЯ: Отрисовка хитбокса ***
    def draw_hitbox(self, target_sprite, offset):
        if hasattr(target_sprite, 'get_hitbox_rect'):
            # Получаем прямоугольник хитбокса в мировых координатах
            hitbox_rect = target_sprite.get_hitbox_rect()
            
            # Применяем смещение экрана
            draw_rect = hitbox_rect.move(offset.x, offset.y)
            
            # Определяем цвет (красный для неуязвимости, зеленый в норме)
            color = DEBUG_HITBOX_COLOR_NORMAL
            if hasattr(target_sprite, 'invulnerable') and target_sprite.invulnerable:
                color = DEBUG_HITBOX_COLOR_INVUL
                
            pygame.draw.rect(self.screen, color, draw_rect, 1)

    def spawn_enemies(self):
        pass

    def check_collisions(self):
        hits = pygame.sprite.groupcollide(enemies, bullets, False, True, pygame.sprite.collide_circle)
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
            
            self.screen.fill(COLOR_BG)
            shake_offset = self.screen_shake.get_offset()
            self.draw_grid(shake_offset)
            
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
                
                # Новые параметры
                wing_spread = self.boss.wing_spread_factor
                is_trans = self.boss.state == self.boss.STATE_PHASE_TRANSITION

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
                    wing_spread, # factor
                    is_trans     # is_transitioning
                )
                
                # Отрисовка UI босса
                self.boss.draw_boss_ui(self.screen, shake_offset)
            
       
          
            
            # *** ОТЛАДКА: Отрисовка хитбокса игрока ***
            self.draw_hitbox(self.player, shake_offset)


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
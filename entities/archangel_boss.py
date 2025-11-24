# archangel_boss.py

import pygame
import math
import random
from config import WIDTH, HEIGHT, all_sprites, enemies, FPS 
from boss_weapons import AngelSpearProjectile 
from rendering.archangel_render import draw_archangel_boss
from vfx import GhostMistVFX, CelestialSmiteVFX, ShieldWaveVFX 

class ArchangelBoss(pygame.sprite.Sprite):
    # --- Состояния машины ---
    STATE_HOVER = 0
    STATE_PREPARE_SPEAR = 1
    STATE_LAUNCH_SPEAR = 2 
    STATE_MIST_EFFECT = 3 
    STATE_PREPARE_SMITE = 4 
    STATE_SHIELD_ATTACK = 5
    STATE_PHASE_TRANSITION = 6 # <--- НОВОЕ СОСТОЯНИЕ ПЕРЕХОДА

    # --- Константы времени (в кадрах) ---
    PREPARE_DURATION = 45 
    LAUNCH_DURATION = 45   
    COOLDOWN_DURATION = 180 
    
    TOTAL_VFX_AND_WAIT_FRAMES = 120 
    MIST_EFFECT_DURATION = TOTAL_VFX_AND_WAIT_FRAMES - PREPARE_DURATION
    
    # --- КОНСТАНТЫ ДЛЯ ПЕРЕХОДА ---
    PHASE_TRANSITION_DURATION = 120 # 2 секунды (при 60 FPS)

    # --- КОНСТАНТЫ ДЛЯ SMITE ---
    SMITE_PREPARE_DURATION = 60 
    SMITE_BLAST_DURATION = 15   
    SMITE_DAMAGE = 25           
    
    SMITE_SECOND_BLAST_DELAY = int(0.5 * FPS) 
    SMITE_FADE_OUT_DURATION = int(0.5 * FPS) 

    # --- КОНСТАНТЫ ДЛЯ ЩИТА ---
    SHIELD_ATTACK_RANGE = 250 
    # ИЗМЕНЕНИЕ: Увеличено время атаки для более плавного возврата
    SHIELD_ATTACK_DURATION = 45 # Было 30
    SHIELD_COOLDOWN = 180 

    # --- ОФФСЕТЫ ДЛЯ ВЕЕРНОЙ АТАКИ ---
    SPEAR_X_OFFSETS = [-500, -250, 250, 500] 
    FIXED_FLIGHT_TIME_MS = 500 

    def __init__(self, x, y, player):
        super().__init__()
        self.groups = all_sprites, enemies
        pygame.sprite.Sprite.__init__(self, self.groups)
        
        self.player = player
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x - 40, y - 20, 80, 60)
        self.radius = 40

        self.fixed_target_pos = pygame.math.Vector2(0, 0)
        
        self.image = pygame.Surface((0, 0))
        
        self.hp = 2000
        self.max_hp = 2000
        self.time_ticks = 0
        
        self.target_pos = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
        self.move_speed = 0.5 
        
        # --- МАШИНА СОСТОЯНИЙ И АНИМАЦИИ ---
        self.state = self.STATE_HOVER 
        self.state_timer = 0
        self.cooldown_timer = self.COOLDOWN_DURATION
        self.spear_animation_progress = 0.0 
        self.smite_vfx_progress = 0.0 
        self.shield_animation_progress = 0.0 
        
        # --- ФАЗЫ БОССА ---
        self.is_phase_two = False 
        self.wing_spread_factor = 0.0 # 0.0 - обычные, 1.0 - широко расправленные
        
        # --- НОВЫЕ ПЕРЕМЕННЫЕ ---
        self.phantom_spears = [] 
        self.vfx_mist_active = False 
        self.attack_counter = 0 
        self.shake_func = player.shake_func 
        
        self.shield_cooldown_timer = 0 

    def update(self, dt):
        self.time_ticks += 1
        self.state_timer += 1
        
        # --- ПРОВЕРКА ПЕРЕХОДА ВО ВТОРУЮ ФАЗУ ---
        health_pct = self.hp / self.max_hp
        # Переход начинается, если HP < 99% (тест), мы не во 2 фазе и не в процессе перехода
        if not self.is_phase_two and self.state != self.STATE_PHASE_TRANSITION and health_pct < 0.99:
            self.enter_phase_two()

        # Уменьшаем кулдаун щита
        if self.shield_cooldown_timer > 0:
            self.shield_cooldown_timer -= 1
        
        # ЛОГИКА ПЕРЕМЕЩЕНИЯ
        current_speed = self.move_speed * (1.5 if self.is_phase_two else 1.0) 
        
        # Во время перехода босс замедляется или останавливается для пафоса
        if self.state == self.STATE_PHASE_TRANSITION:
            current_speed *= 0.1 

        direction = self.target_pos - self.pos
        distance = direction.length()
        if distance > 1:
            self.pos += direction.normalize() * current_speed * dt * 60
        self.rect.center = self.pos
        
        # --- ПРОВЕРКА НА БЛИЖНИЙ БОЙ (ЩИТ) ---
        # Запрещаем атаки во время перехода
        if self.state != self.STATE_PHASE_TRANSITION:
            dist_to_player = (self.player.pos - self.pos).length()
            
            can_shield_bash = (
                dist_to_player < self.SHIELD_ATTACK_RANGE and
                self.shield_cooldown_timer <= 0 and
                self.state not in [self.STATE_PREPARE_SPEAR, self.STATE_LAUNCH_SPEAR, self.STATE_MIST_EFFECT]
            )

            if can_shield_bash:
                if self.state == self.STATE_HOVER:
                    self.set_state(self.STATE_SHIELD_ATTACK)
        
        
        # --- ОБНОВЛЕНИЕ МАШИНЫ СОСТОЯНИЙ ---
        if self.state == self.STATE_HOVER:
            self.cooldown_timer -= 1
            self.spear_animation_progress = max(0.0, self.spear_animation_progress - 0.02) 
            self.smite_vfx_progress = 0.0 
            self.shield_animation_progress = max(0.0, self.shield_animation_progress - 0.1) 

            if self.cooldown_timer <= 0:
                if self.attack_counter % 2 == 0:
                    self.set_state(self.STATE_PREPARE_SPEAR)
                    self.start_mist_effect() 
                    self.spawn_visual_spears() 
                else:
                    self.set_state(self.STATE_PREPARE_SMITE)
                    self.start_smite_attack() 
                    
                self.attack_counter += 1

        # ... (Остальные состояния без изменений) ...
        elif self.state == self.STATE_PREPARE_SPEAR:
            progress = self.state_timer / self.PREPARE_DURATION
            self.spear_animation_progress = min(1.0, progress)
            self.smite_vfx_progress = 0.0 
            if self.state_timer >= self.PREPARE_DURATION:
                self.set_state(self.STATE_MIST_EFFECT)
                
        elif self.state == self.STATE_MIST_EFFECT:
            self.spear_animation_progress = 1.0 
            self.smite_vfx_progress = 0.0 
            if self.state_timer >= self.MIST_EFFECT_DURATION:
                self.activate_spears_flight() 
                self.set_state(self.STATE_LAUNCH_SPEAR)

        elif self.state == self.STATE_LAUNCH_SPEAR:
            progress = self.state_timer / self.LAUNCH_DURATION
            self.spear_animation_progress = max(0.0, 1.0 - progress) 
            self.smite_vfx_progress = 0.0 
            if self.state_timer >= self.LAUNCH_DURATION:
                base_cd = self.COOLDOWN_DURATION
                actual_cd = base_cd * 0.7 if self.is_phase_two else base_cd
                self.cooldown_timer = actual_cd
                self.set_state(self.STATE_HOVER)

        elif self.state == self.STATE_PREPARE_SMITE:
            self.spear_animation_progress = 0.0 
            total_smite_time = (
                self.SMITE_SECOND_BLAST_DELAY + 
                self.SMITE_PREPARE_DURATION + 
                self.SMITE_BLAST_DURATION +
                self.SMITE_FADE_OUT_DURATION 
            )
            self.smite_vfx_progress = min(1.0, self.state_timer / total_smite_time) 
            if self.state_timer >= total_smite_time:
                base_cd = self.COOLDOWN_DURATION
                actual_cd = base_cd * 0.7 if self.is_phase_two else base_cd
                self.cooldown_timer = actual_cd
                self.set_state(self.STATE_HOVER)

        elif self.state == self.STATE_SHIELD_ATTACK:
            self.spear_animation_progress = 0.0
            self.smite_vfx_progress = 0.0 
            strike_time = self.SHIELD_ATTACK_DURATION * 0.3 # Удар быстрее, возврат дольше
            
            if self.state_timer <= strike_time:
                self.shield_animation_progress = self.state_timer / strike_time
                if self.state_timer == int(strike_time): 
                     self.spawn_shield_wave()
            else:
                return_progress = (self.state_timer - strike_time) / (self.SHIELD_ATTACK_DURATION - strike_time)
                self.shield_animation_progress = 1.0 - return_progress
            if self.state_timer >= self.SHIELD_ATTACK_DURATION:
                self.shield_cooldown_timer = self.SHIELD_COOLDOWN 
                self.set_state(self.STATE_HOVER)

        # --- НОВОЕ СОСТОЯНИЕ: ПЕРЕХОД В ФАЗУ 2 ---
        elif self.state == self.STATE_PHASE_TRANSITION:
            # Плавное увеличение wing_spread_factor от 0 до 1
            self.wing_spread_factor = min(1.0, self.state_timer / self.PHASE_TRANSITION_DURATION)
            
            # Каждые 20 кадров небольшая тряска (нарастание напряжения)
            if self.state_timer % 20 == 0:
                self.shake_func(2 + self.wing_spread_factor * 5)

            if self.state_timer >= self.PHASE_TRANSITION_DURATION:
                # Завершение перехода
                self.is_phase_two = True
                self.wing_spread_factor = 1.0 # Фиксируем крылья в широком положении
                self.shake_func(20) # Финальный взрыв энергии
                self.set_state(self.STATE_HOVER)


    def enter_phase_two(self):
        """Запускает состояние перехода."""
        self.set_state(self.STATE_PHASE_TRANSITION)
        # Сбрасываем анимации
        self.spear_animation_progress = 0.0
        self.smite_vfx_progress = 0.0
        self.shield_animation_progress = 0.0
        print("!!! STARTING PHASE TWO TRANSITION !!!")

    def set_state(self, new_state):
        self.state = new_state
        self.state_timer = 0
    
    def spawn_shield_wave(self):
        wave_pos = self.pos + pygame.math.Vector2(10, -20)
        ShieldWaveVFX(wave_pos, max_radius=360, damage=30, push_force=25, duration=30)
        self.shake_func(10) 

    def start_mist_effect(self):
        self.fixed_target_pos = self.player.pos.copy() 
        self.vfx_mist_active = True 

    def start_smite_attack(self):
        fixed_pos = self.player.pos.copy() 
        CelestialSmiteVFX(
            fixed_pos, 
            self.SMITE_PREPARE_DURATION,
            self.SMITE_BLAST_DURATION,
            self.SMITE_DAMAGE,
            self.player,
            self.shake_func,
            prep_delay_frames=0 
        )
        pos_getter_func = lambda: self.player.pos.copy() 
        CelestialSmiteVFX(
            pos_getter_func, 
            self.SMITE_PREPARE_DURATION,
            self.SMITE_BLAST_DURATION,
            self.SMITE_DAMAGE,
            self.player,
            self.shake_func,
            prep_delay_frames=self.SMITE_SECOND_BLAST_DELAY 
        )

    def spawn_visual_spears(self):
        P_target = self.fixed_target_pos 
        relative_y_offset = -50 
        self.phantom_spears = []
        total_vfx_ms = self.TOTAL_VFX_AND_WAIT_FRAMES * 1000 / 60 
        for x_offset in self.SPEAR_X_OFFSETS:
            P_start = pygame.math.Vector2(self.pos.x + x_offset, self.pos.y + relative_y_offset)
            V_to_target = P_target - P_start
            if V_to_target.length_squared() == 0:
                 direction_for_angle = pygame.math.Vector2(1, 0)
            else:
                 direction_for_angle = V_to_target.normalize()
            spear = AngelSpearProjectile(
                P_start, direction_for_angle, P_target, self.FIXED_FLIGHT_TIME_MS, total_vfx_ms, all_sprites          
            )
            self.phantom_spears.append(spear)

    def activate_spears_flight(self):
        for spear in self.phantom_spears:
            spear.activate_flight()
        self.phantom_spears = [] 
        self.vfx_mist_active = False 
        self.fixed_target_pos = pygame.math.Vector2(0, 0)
            
    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()

    def draw_boss_ui(self, surface, offset):
        bar_w, bar_h = 200, 8
        bar_x = self.pos.x - bar_w // 2 + offset.x
        bar_y = self.pos.y - 180 + offset.y
        pygame.draw.rect(surface, (30, 30, 0), (bar_x, bar_y, bar_w, bar_h))
        pct = max(0, self.hp / self.max_hp)
        
        hp_color = (200, 150, 0) if not self.is_phase_two else (220, 50, 0)
        
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, bar_w * pct, bar_h))
        pygame.draw.rect(surface, (255, 215, 50), (bar_x, bar_y, bar_w * pct, bar_h/2))
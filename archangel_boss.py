# entities/archangel_boss.py

import pygame
import math
import random
from config import WIDTH, HEIGHT, all_sprites, enemies, FPS 
from boss_weapons import AngelSpearProjectile 
from rendering.archangel_render import draw_archangel_boss
from vfx import GhostMistVFX, CelestialSmiteVFX, ShieldWaveVFX, ChaosRiftVFX

class ArchangelBoss(pygame.sprite.Sprite):
    # --- Состояния машины ---
    STATE_HIDDEN = -1         # Босс скрыт (еще не заспавнен)
    STATE_INTRO = -2          # Анимация появления из портала
    STATE_DEATH = -3          # НОВОЕ: Состояние смерти
    
    STATE_HOVER = 0
    STATE_PREPARE_SPEAR = 1
    STATE_LAUNCH_SPEAR = 2 
    STATE_MIST_EFFECT = 3 
    STATE_PREPARE_SMITE = 4 
    STATE_SHIELD_ATTACK = 5
    STATE_PHASE_TRANSITION = 6 
    STATE_RECOVERY_PHASE_TWO = 7 
    STATE_PHASE_TWO_DASH = 8 
    STATE_CHAOS_BARRAGE = 9 

    # --- ТАЙМИНГИ ИНТРО ---
    INTRO_PORTAL_OPEN_TIME = 60
    INTRO_DESCEND_TIME = 150
    INTRO_PORTAL_CLOSE_TIME = 60

   # Обновите тайминги смерти
    DEATH_PHASE_1_DURATION = int(0.4 * FPS) # 24 кадра: Поза рук + исчезновение оружия
    DEATH_PHASE_2_DURATION = int(0.4 * FPS) # 24 кадра: Крылья отлетают
    DEATH_PHASE_3_DURATION = int(2.0 * FPS) # 120 кадров: Накопление света (НОВОЕ)
    DEATH_PHASE_4_DURATION = int(0.5 * FPS) # 30 кадров: Вспышка и исчезновение (НОВОЕ)
    
    # --- БАЗОВЫЕ Константы времени (в кадрах) ---
    PREPARE_DURATION = 45 
    LAUNCH_DURATION = 45   
    COOLDOWN_DURATION = 60 
    
    TOTAL_VFX_AND_WAIT_FRAMES = 120 
    
    # --- КОНСТАНТЫ ДЛЯ ПЕРЕХОДА ---
    PHASE_TRANSITION_DURATION = 120 
    PHASE_RECOVERY_DURATION = 30    

    # --- БАЗОВЫЕ КОНСТАНТЫ ДЛЯ SMITE ---
    SMITE_PREPARE_DURATION = 60 
    SMITE_BLAST_DURATION = 15   
    SMITE_DAMAGE = 25           
    
    SMITE_SECOND_BLAST_DELAY = int(0.5 * FPS) 
    SMITE_FADE_OUT_DURATION = int(0.5 * FPS) 

    # --- БАЗОВЫЕ КОНСТАНТЫ ДЛЯ ЩИТА ---
    SHIELD_ATTACK_RANGE = 250 
    SHIELD_ATTACK_DURATION = 45 
    SHIELD_COOLDOWN = 120 

    # --- КОНСТАНТЫ МОБИЛЬНОСТИ (ФАЗА 2) ---
    DASH_COOLDOWN = 210 
    DASH_DURATION = 18
    # *** ИЗМЕНЕНИЕ 1: Увеличено с 400 до 560 (1.4x) для широких экранов ***
    MOVEMENT_RADIUS = 560 
    
    # --- КОНСТАНТЫ ДЛЯ CHAOS BARRAGE ---
    CHAOS_BARRAGE_DURATION = 600 # 10 секунд ульты
    RIFT_SPAWN_INTERVAL = 72 

    # --- ОФФСЕТЫ ДЛЯ ВЕЕРНОЙ АТАКИ ---
    SPEAR_X_OFFSETS = [-500, -250, 250, 500] 
    
    SPEAR_WAVE2_OFFSETS = [
        (-600, -100), (-400, 50), (-200, -100), 
        (200, -100), (400, 50), (600, -100)
    ]
    
    FIXED_FLIGHT_TIME_MS = 500 

    def __init__(self, x, y, player):
        super().__init__()
        # НЕ добавляем в enemies сразу, чтобы не били, пока не появится
        self.groups = all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        
        self.player = player
        self.spawn_pos = pygame.math.Vector2(x, y) 
        
        # СМЕЩЕНИЕ ПОРТАЛА: Портал рисуется на spawn_pos.y - 400
        # Значит, босс должен вылетать из Y - 400
        self.portal_offset_y = 400 
        self.pos = pygame.math.Vector2(x, y - self.portal_offset_y) 
        
        self.rect = pygame.Rect(x - 40, y - 20, 80, 60)
        self.radius = 40 
        self.hitboxes = []

        self.fixed_target_pos = pygame.math.Vector2(0, 0)
        
        self.image = pygame.Surface((0, 0)) # Невидима
        
        self.hp = 2000
        self.max_hp = 2000
        self.time_ticks = 0
        
        self.arena_center = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
        self.target_pos = self.arena_center.copy()
        self.move_speed = 0.5 
        
        # Начинаем скрытым
        self.state = self.STATE_HIDDEN 
        self.is_active = False 
        
        self.state_timer = 0
        self.cooldown_timer = self.COOLDOWN_DURATION
        self.spear_animation_progress = 0.0 
        self.smite_vfx_progress = 0.0 
        self.shield_animation_progress = 0.0 
        
        # --- ФАЗЫ БОССА ---
        self.is_phase_two = False 
        self.wing_spread_factor = 0.0 
        self.transition_pose_factor = 0.0 
        
        self.invulnerable = True # Неуязвима по умолчанию (до спавна)
        self.final_attack_triggered = False 
        
        # --- МОБИЛЬНОСТЬ ---
        self.dash_timer = self.DASH_COOLDOWN 
        self.dash_start_pos = pygame.math.Vector2(0, 0) 
        self.movement_tilt_x = 0.0 
        
        # --- НОВЫЕ ПЕРЕМЕННЫЕ ---
        self.phantom_spears = [] 
        self.spear_wave_two_spawned = False 
        self.vfx_mist_active = False 
        self.attack_counter = 0 
        self.shake_func = player.shake_func 
        
        self.shield_cooldown_timer = 0 
        self.rift_timer = 0 
        
        # Переменные для Интро
        self.intro_portal_progress = 0.0
        self.current_alpha = 0

        # Параметры смерти для рендера
        self.death_pose_factor = 0.0
        self.death_item_alpha = 255
        self.death_wing_alpha = 255
        self.death_wing_offset = 0.0
        
        # НОВЫЕ ПЕРЕМЕННЫЕ
        self.death_light_scale = 0.0 # 0.0 -> 1.0 (Сила света)
        self.death_flash_alpha = 0   # 0 -> 255 (Яркость вспышки)

    def spawn_boss(self):
        """Вызвать босса (начать интро)."""
        if self.state == self.STATE_HIDDEN:
            print("BOSS SPAWN SEQUENCE INITIATED")
            self.state = self.STATE_INTRO
            self.state_timer = 0
            self.is_active = True
            # Ставим босса ВНУТРЬ портала (высоко)
            self.pos = pygame.math.Vector2(self.spawn_pos.x, self.spawn_pos.y - self.portal_offset_y)
            self.current_alpha = 0 # Скрыта

    def get_speed_factor(self):
        if self.state == self.STATE_CHAOS_BARRAGE:
            return 1.0
        return 0.5 if self.is_phase_two else 1.0

    def update(self, dt):
        self.time_ticks += 1
        
        # 0. Если скрыт - ничего не делаем
        if self.state == self.STATE_HIDDEN:
            return
        
        # --- ЛОГИКА СМЕРТИ (ОБНОВЛЕННАЯ) ---
        if self.state == self.STATE_DEATH:
            self.state_timer += 1
            self.invulnerable = True
            
            # Фаза 1: Руки в стороны и вверх, оружие исчезает (0.4 сек)
            if self.state_timer <= self.DEATH_PHASE_1_DURATION:
                progress = self.state_timer / self.DEATH_PHASE_1_DURATION
                self.death_pose_factor = progress
                self.death_item_alpha = int(255 * (1.0 - progress))
                
            # Фаза 2: Крылья отлетают (0.4 сек)
            elif self.state_timer <= self.DEATH_PHASE_1_DURATION + self.DEATH_PHASE_2_DURATION:
                self.death_pose_factor = 1.0
                self.death_item_alpha = 0
                
                p2_timer = self.state_timer - self.DEATH_PHASE_1_DURATION
                progress = p2_timer / self.DEATH_PHASE_2_DURATION
                self.death_wing_alpha = int(255 * (1.0 - progress))
                self.death_wing_offset = 30.0 * progress
                
            # Фаза 3: Накопление Света (2.0 сек)
            elif self.state_timer <= self.DEATH_PHASE_1_DURATION + self.DEATH_PHASE_2_DURATION + self.DEATH_PHASE_3_DURATION:
                self.death_wing_alpha = 0
                self.death_wing_offset = 30.0
                
                p3_timer = self.state_timer - (self.DEATH_PHASE_1_DURATION + self.DEATH_PHASE_2_DURATION)
                progress = p3_timer / self.DEATH_PHASE_3_DURATION
                
                self.death_light_scale = progress # Свет становится ярче и больше
                self.shake_func(2 * progress) # Нарастающая тряска
                
            # Фаза 4: Вспышка и Исчезновение (0.5 сек)
            elif self.state_timer <= self.DEATH_PHASE_1_DURATION + self.DEATH_PHASE_2_DURATION + self.DEATH_PHASE_3_DURATION + self.DEATH_PHASE_4_DURATION:
                self.death_light_scale = 1.0
                
                p4_timer = self.state_timer - (self.DEATH_PHASE_1_DURATION + self.DEATH_PHASE_2_DURATION + self.DEATH_PHASE_3_DURATION)
                progress = p4_timer / self.DEATH_PHASE_4_DURATION
                
                # Вспышка начинается с максимума и исчезает вместе с боссом
                self.death_flash_alpha = 255 # Максимально белый
                
                # Босс (вместе со вспышкой) растворяется
                self.current_alpha = int(255 * (1.0 - progress))
                
            else:
                self.kill()
            
            return

        # 1. ЛОГИКА ИНТРО (Появление)
        if self.state == self.STATE_INTRO:
            self.state_timer += 1
            
            # А. Открытие портала
            if self.state_timer < self.INTRO_PORTAL_OPEN_TIME:
                self.intro_portal_progress = self.state_timer / self.INTRO_PORTAL_OPEN_TIME
                self.current_alpha = 0
                self.shake_func(1)
                
            # Б. Спуск босса
            elif self.state_timer < self.INTRO_PORTAL_OPEN_TIME + self.INTRO_DESCEND_TIME:
                self.intro_portal_progress = 1.0
                descend_progress = (self.state_timer - self.INTRO_PORTAL_OPEN_TIME) / self.INTRO_DESCEND_TIME
                
                # Плавный спуск (Ease Out Cubic - быстро вылетает, плавно тормозит)
                t = descend_progress
                ease = 1 - pow(1 - t, 3)
                
                start_y = self.spawn_pos.y - self.portal_offset_y
                end_y = self.spawn_pos.y
                
                self.pos.y = start_y + (end_y - start_y) * ease
                
                # Прозрачность: Проявляется быстрее, чем долетает
                alpha_progress = min(1.0, descend_progress * 2.0)
                self.current_alpha = int(255 * alpha_progress)
                
                self.shake_func(2)

            # В. Закрытие портала
            elif self.state_timer < self.INTRO_PORTAL_OPEN_TIME + self.INTRO_DESCEND_TIME + self.INTRO_PORTAL_CLOSE_TIME:
                self.current_alpha = 255
                close_t = (self.state_timer - (self.INTRO_PORTAL_OPEN_TIME + self.INTRO_DESCEND_TIME)) / self.INTRO_PORTAL_CLOSE_TIME
                self.intro_portal_progress = 1.0 - close_t
            
            else:
                # Конец интро - НАЧАЛО БОЯ
                self.state = self.STATE_HOVER
                self.intro_portal_progress = 0.0
                self.invulnerable = False
                self.cooldown_timer = 60
                enemies.add(self) # Теперь можно бить
                self.shake_func(10)
            
            self.update_hitboxes()
            return # Выходим, чтобы не сработала боевая логика

        # === ДАЛЕЕ: ОБЫЧНАЯ БОЕВАЯ ЛОГИКА ===
        
        self.state_timer += 1
        factor = self.get_speed_factor()
        
        # --- ЛОГИКА ПЕРЕХОДОВ ПО ХП ---
        health_pct = self.hp / self.max_hp
        
        # Переход во ВТОРУЮ ФАЗУ (70% HP)
        if not self.is_phase_two and self.state != self.STATE_PHASE_TRANSITION and self.state != self.STATE_RECOVERY_PHASE_TWO:
            if health_pct < 0.70:
                self.enter_phase_two()

        # ФИНАЛЬНАЯ АТАКА (< 250 HP)
        if self.is_phase_two and not self.final_attack_triggered and self.state != self.STATE_PHASE_TRANSITION:
            if self.hp < 250:
                self.start_final_chaos_attack()

        # Важно: держать крылья открытыми во второй фазе
        if self.is_phase_two and self.state != self.STATE_PHASE_TRANSITION:
            self.wing_spread_factor = 1.0 

        if self.shield_cooldown_timer > 0: self.shield_cooldown_timer -= 1
        
        # --- ЛОГИКА РЫВКОВ ---
        if self.is_phase_two and self.state not in [self.STATE_PHASE_TRANSITION, self.STATE_RECOVERY_PHASE_TWO, self.STATE_PHASE_TWO_DASH, self.STATE_CHAOS_BARRAGE]:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                if self.state == self.STATE_HOVER:
                    self.start_phase_two_dash()

        # --- ФИЗИКА ДВИЖЕНИЯ ---
        if self.state == self.STATE_PHASE_TWO_DASH:
            progress = min(1.0, self.state_timer / self.DASH_DURATION)
            smooth_t = progress * progress * (3 - 2 * progress)
            self.pos = self.dash_start_pos.lerp(self.target_pos, smooth_t)
            move_vec = self.target_pos - self.dash_start_pos
            if move_vec.length() > 0:
                self.movement_tilt_x = (move_vec.normalize().x) * (1.0 - progress) 
            if self.state_timer >= self.DASH_DURATION:
                self.movement_tilt_x = 0.0 
                self.dash_timer = self.DASH_COOLDOWN
                self.set_state(self.STATE_HOVER)
        
        elif self.state == self.STATE_CHAOS_BARRAGE:
            # Дрейф к центру во время ульты
            dir_to_center = self.arena_center - self.pos
            if dir_to_center.length() > 5:
                self.pos += dir_to_center.normalize() * 2.0 
            # Принудительная поза
            self.transition_pose_factor = 1.0
                
        else:
            target_speed = self.move_speed
            if self.is_phase_two: target_speed *= 0.2 
            if self.state == self.STATE_PHASE_TRANSITION:
                target_speed *= 0.1 

            direction = self.target_pos - self.pos
            distance = direction.length()
            if distance > 1:
                self.pos += direction.normalize() * target_speed * dt * 60
            
            self.movement_tilt_x = self.movement_tilt_x * 0.9
        

        # Обновление хитбоксов
        self.update_hitboxes()
        
        # --- ЛОГИКА ЩИТА (ОБНОВЛЕННАЯ) ---
        # Щит НЕЛЬЗЯ использовать, если босс занят чем-то важным (копья, ульта, переходы).
        # Но МОЖНО использовать во время взрыва (PREPARE_SMITE) или отдыха (HOVER).
        
        cant_shield_states = [
            self.STATE_PHASE_TRANSITION, 
            self.STATE_RECOVERY_PHASE_TWO, 
            self.STATE_PHASE_TWO_DASH, 
            self.STATE_CHAOS_BARRAGE,
            
            # Группа атаки копьями (НЕПРЕРЫВАЕМАЯ)
            self.STATE_PREPARE_SPEAR,
            self.STATE_MIST_EFFECT,
            self.STATE_LAUNCH_SPEAR,
            
            self.STATE_SHIELD_ATTACK   # Уже бьем щитом
        ]
        
        if self.state not in cant_shield_states:
            dist_to_player = (self.player.pos - self.pos).length()
            
            # Проверяем дистанцию и кулдаун щита
            if dist_to_player < self.SHIELD_ATTACK_RANGE and self.shield_cooldown_timer <= 0:
                self.set_state(self.STATE_SHIELD_ATTACK)
        
        self.update_state_logic(factor)

    def update_hitboxes(self):
        # Верхний хитбокс (тело/крылья) - Оставляем Rect
        hb_upper = pygame.Rect(0, 0, 50, 120)
        hb_upper.center = (self.pos.x, self.pos.y - 90)
        
        # Нижний хитбокс (подол платья) - ТЕПЕРЬ КРУГ
        # Это сделает углы "мягкими", и снаряды будут пролетать мимо краев платья
        hb_lower = {
            'type': 'circle', 
            'center': (self.pos.x, self.pos.y + 10), 
            'radius': 46 # Радиус 45 соответствует ширине 90
        }
        
        self.hitboxes = [hb_upper, hb_lower]
        
        # Обновляем self.rect для совместимости (берем описанный квадрат вокруг круга)
        # Это нужно для некоторых проверок, которые ожидают rect
        lower_rect_bounds = pygame.Rect(0, 0, 90, 90)
        lower_rect_bounds.center = (self.pos.x, self.pos.y + 10)
        self.rect = hb_upper.union(lower_rect_bounds)

    def update_state_logic(self, factor):
        if self.state == self.STATE_HOVER:
            self.cooldown_timer -= 1
            anim_recovery_speed = 0.02 if not self.is_phase_two else 0.04
            
            self.spear_animation_progress = max(0.0, self.spear_animation_progress - anim_recovery_speed) 
            self.smite_vfx_progress = 0.0 
            self.shield_animation_progress = max(0.0, self.shield_animation_progress - 0.1)
            self.transition_pose_factor = 0.0 

            if self.cooldown_timer <= 0:
                if self.attack_counter % 2 == 0:
                    self.set_state(self.STATE_PREPARE_SPEAR)
                    self.start_mist_effect(factor)
                    self.spawn_visual_spears(factor)
                else:
                    self.set_state(self.STATE_PREPARE_SMITE)
                    self.start_smite_attack(factor) 
                self.attack_counter += 1

        elif self.state == self.STATE_PREPARE_SPEAR:
            dur = int(self.PREPARE_DURATION * factor)
            progress = self.state_timer / dur
            self.spear_animation_progress = min(1.0, progress)
            self.smite_vfx_progress = 0.0 
            
            wave2_delay_frames = int(0.15 * 60 * factor) 
            if self.is_phase_two and not self.spear_wave_two_spawned:
                if self.state_timer >= wave2_delay_frames:
                    total_vfx_dur = int(self.TOTAL_VFX_AND_WAIT_FRAMES * factor)
                    remaining_frames_for_sync = total_vfx_dur - self.state_timer
                    remaining_ms = remaining_frames_for_sync * 1000 / 60
                    extra_delay_ms = 200 
                    self.spawn_visual_spears_wave2(factor, remaining_ms + extra_delay_ms)
                    self.spear_wave_two_spawned = True

            if self.state_timer >= dur:
                self.set_state(self.STATE_MIST_EFFECT)
                
        elif self.state == self.STATE_MIST_EFFECT:
            self.spear_animation_progress = 1.0 
            self.smite_vfx_progress = 0.0 
            total_dur = int(self.TOTAL_VFX_AND_WAIT_FRAMES * factor)
            prep_dur = int(self.PREPARE_DURATION * factor)
            mist_dur = total_dur - prep_dur
            if self.state_timer >= mist_dur:
                self.activate_spears_flight() 
                self.set_state(self.STATE_LAUNCH_SPEAR)

        elif self.state == self.STATE_LAUNCH_SPEAR:
            dur = int(self.LAUNCH_DURATION * factor)
            progress = self.state_timer / dur
            self.spear_animation_progress = max(0.0, 1.0 - progress) 
            self.smite_vfx_progress = 0.0 
            if self.state_timer >= dur:
                self.cooldown_timer = int(self.COOLDOWN_DURATION * factor)
                self.set_state(self.STATE_HOVER)

        elif self.state == self.STATE_PREPARE_SMITE:
            self.spear_animation_progress = 0.0 
            total_smite_time = int((
                self.SMITE_SECOND_BLAST_DELAY + 
                self.SMITE_PREPARE_DURATION + 
                self.SMITE_BLAST_DURATION +
                self.SMITE_FADE_OUT_DURATION 
            ) * factor)
            extra_delay = 0
            if self.is_phase_two:
                extra_delay = int(self.SMITE_SECOND_BLAST_DELAY * 2 * factor) 
            full_state_duration = total_smite_time + extra_delay
            self.smite_vfx_progress = min(1.0, self.state_timer / full_state_duration) 
            if self.state_timer >= full_state_duration:
                self.cooldown_timer = int(self.COOLDOWN_DURATION * factor)
                self.set_state(self.STATE_HOVER)

        elif self.state == self.STATE_SHIELD_ATTACK:
            self.spear_animation_progress = 0.0
            self.smite_vfx_progress = 0.0 
            total_dur = int(self.SHIELD_ATTACK_DURATION * factor)
            strike_time = total_dur * 0.3 
            if self.state_timer <= strike_time:
                self.shield_animation_progress = self.state_timer / strike_time
                if self.state_timer == int(strike_time): 
                     self.spawn_shield_wave()
            else:
                return_progress = (self.state_timer - strike_time) / (total_dur - strike_time)
                self.shield_animation_progress = 1.0 - return_progress
            if self.state_timer >= total_dur:
                cd_factor = 0.25 if self.is_phase_two else 1.0
                self.shield_cooldown_timer = int(self.SHIELD_COOLDOWN * cd_factor)
                self.set_state(self.STATE_HOVER)

        elif self.state == self.STATE_PHASE_TRANSITION:
            progress = min(1.0, self.state_timer / self.PHASE_TRANSITION_DURATION)
            self.wing_spread_factor = progress
            self.transition_pose_factor = progress 
            if self.state_timer % 20 == 0:
                self.shake_func(2 + self.wing_spread_factor * 5)
            if self.state_timer >= self.PHASE_TRANSITION_DURATION:
                self.is_phase_two = True
                self.wing_spread_factor = 1.0
                self.transition_pose_factor = 1.0
                self.shake_func(20) 
                self.set_state(self.STATE_RECOVERY_PHASE_TWO)

        elif self.state == self.STATE_RECOVERY_PHASE_TWO:
            self.wing_spread_factor = 1.0
            progress = self.state_timer / self.PHASE_RECOVERY_DURATION
            self.transition_pose_factor = max(0.0, 1.0 - progress)
            if self.state_timer >= self.PHASE_RECOVERY_DURATION:
                self.transition_pose_factor = 0.0
                self.set_state(self.STATE_HOVER)

        elif self.state == self.STATE_CHAOS_BARRAGE:
            self.transition_pose_factor = 1.0 
            self.smite_vfx_progress = 0.5     
            self.shake_func(5)
            self.rift_timer += 1
            if self.rift_timer >= self.RIFT_SPAWN_INTERVAL:
                self.rift_timer = 0
                self.spawn_chaos_rifts()
            
            if self.state_timer >= self.CHAOS_BARRAGE_DURATION:
                # БЫЛО: self.kill()
                # СТАЛО: Переход в состояние смерти после ульты
                self.set_state(self.STATE_DEATH)

    def start_final_chaos_attack(self):
        """Запускает финальную, смертельную атаку."""
        self.set_state(self.STATE_CHAOS_BARRAGE)
        self.final_attack_triggered = True
        self.invulnerable = True # Становится неуязвимым
        self.spear_animation_progress = 0.0
        self.shield_animation_progress = 0.0
        print("!!! FINAL CHAOS ATTACK STARTED !!!")

    def spawn_chaos_rifts(self):
        count = random.randint(5, 7)
        spawned_positions = [] # Список для хранения позиций порталов в этой волне

        for _ in range(count):
            for _ in range(15): # Чуть больше попыток, так как условий стало больше
                x = random.randint(50, WIDTH-50)
                y = random.randint(50, HEIGHT-50)
                pos = pygame.math.Vector2(x, y)
                
                # 1. Проверка расстояния от БОССА (было раньше)
                if abs(pos.x - self.pos.x) <= 200 or abs(pos.y - self.pos.y) <= 200:
                    continue

                # 2. Проверка расстояния от ДРУГИХ ПОРТАЛОВ (новое)
                too_close = False
                for existing_pos in spawned_positions:
                    if abs(pos.x - existing_pos.x) < 150 and abs(pos.y - existing_pos.y) < 150:
                        too_close = True
                        break
                
                if too_close:
                    continue

                # Если все проверки пройдены - спавним
                ChaosRiftVFX(pos, self.RIFT_SPAWN_INTERVAL, self.player)
                spawned_positions.append(pos)
                break

    def start_phase_two_dash(self):
        self.set_state(self.STATE_PHASE_TWO_DASH)
        self.dash_start_pos = self.pos.copy()
        target_x, target_y = self.pos.x, self.pos.y
        for _ in range(15):
            angle = random.uniform(0, math.pi * 2)
            # Увеличенная дистанция поиска цели
            dist = random.uniform(420, self.MOVEMENT_RADIUS) 
            offset = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * dist
            candidate_x = max(100, min(WIDTH - 100, self.arena_center.x + offset.x))
            candidate_y = max(100, min(HEIGHT - 100, self.arena_center.y + offset.y))
            if abs(candidate_x - self.pos.x) >= 260 and abs(candidate_y - self.pos.y) >= 260:
                target_x, target_y = candidate_x, candidate_y
                break
        self.target_pos = pygame.math.Vector2(target_x, target_y)
        self.shake_func(5)

    def enter_phase_two(self):
        self.set_state(self.STATE_PHASE_TRANSITION)
        self.spear_animation_progress = 0.0
        self.smite_vfx_progress = 0.0
        self.shield_animation_progress = 0.0
        print("!!! STARTING PHASE TWO TRANSITION !!!")

    def set_state(self, new_state):
        self.state = new_state
        self.state_timer = 0
        if new_state == self.STATE_PREPARE_SPEAR:
            self.spear_wave_two_spawned = False
    
    def spawn_shield_wave(self):
        wave_pos = self.pos + pygame.math.Vector2(10, -20)
        radius = 300 if self.is_phase_two else 190
        ShieldWaveVFX(wave_pos, max_radius=radius, damage=30, push_force=25, duration=30)
        self.shake_func(10) 

    def start_mist_effect(self, factor=1.0):
        self.fixed_target_pos = self.player.pos.copy() 
        self.vfx_mist_active = True 

    def start_smite_attack(self, factor=1.0):
        fixed_pos = self.player.pos.copy() 
        prep = int(self.SMITE_PREPARE_DURATION * factor)
        blast = int(self.SMITE_BLAST_DURATION * factor)
        delay = int(self.SMITE_SECOND_BLAST_DELAY * factor)
        CelestialSmiteVFX(fixed_pos, prep, blast, self.SMITE_DAMAGE, self.player, self.shake_func, prep_delay_frames=0, size_mult=1.0, color_mode='cyan')
        pos_getter_func = lambda: self.player.pos.copy() 
        CelestialSmiteVFX(pos_getter_func, prep, blast, self.SMITE_DAMAGE, self.player, self.shake_func, prep_delay_frames=delay, size_mult=1.0, color_mode='cyan')
        if self.is_phase_two:
            CelestialSmiteVFX(pos_getter_func, prep, blast, self.SMITE_DAMAGE, self.player, self.shake_func, prep_delay_frames=delay * 2, size_mult=1.1, color_mode='cyan_to_red')
            CelestialSmiteVFX(pos_getter_func, prep, blast, self.SMITE_DAMAGE, self.player, self.shake_func, prep_delay_frames=delay * 3, size_mult=1.1, color_mode='cyan_to_red')

    def spawn_visual_spears(self, factor=1.0):
        P_target = self.fixed_target_pos 
        relative_y_offset = -50 
        self.phantom_spears = []
        total_vfx_ms = (int(self.TOTAL_VFX_AND_WAIT_FRAMES * factor) * 1000) / 60 
        self._create_spears_from_offsets(self.SPEAR_X_OFFSETS, P_target, relative_y_offset, total_vfx_ms)

    def spawn_visual_spears_wave2(self, factor=1.0, remaining_ms=0):
        P_target = self.fixed_target_pos 
        relative_y_offset = -50 
        if remaining_ms < 0: remaining_ms = 0
        for offset in self.SPEAR_WAVE2_OFFSETS:
            off_x, off_y = offset
            P_start = pygame.math.Vector2(self.pos.x + off_x, self.pos.y + off_y)
            V_to_target = P_target - P_start
            if V_to_target.length_squared() == 0:
                 direction_for_angle = pygame.math.Vector2(1, 0)
            else:
                 direction_for_angle = V_to_target.normalize()
            spear = AngelSpearProjectile(P_start, direction_for_angle, P_target, self.FIXED_FLIGHT_TIME_MS, remaining_ms, all_sprites)
            self.phantom_spears.append(spear)

    def _create_spears_from_offsets(self, x_offsets, P_target, y_offset, total_ms):
        for x_offset in x_offsets:
            P_start = pygame.math.Vector2(self.pos.x + x_offset, self.pos.y + y_offset)
            V_to_target = P_target - P_start
            if V_to_target.length_squared() == 0:
                 direction_for_angle = pygame.math.Vector2(1, 0)
            else:
                 direction_for_angle = V_to_target.normalize()
            spear = AngelSpearProjectile(P_start, direction_for_angle, P_target, self.FIXED_FLIGHT_TIME_MS, total_ms, all_sprites)
            self.phantom_spears.append(spear)

    def activate_spears_flight(self):
        for spear in self.phantom_spears:
            spear.activate_flight() 
        self.phantom_spears = [] 
        self.vfx_mist_active = False 
        self.fixed_target_pos = pygame.math.Vector2(0, 0)
            
    def take_damage(self, amount):
        if self.invulnerable:
            return 
        self.hp -= amount
        
        if self.hp <= 0:
            # БЫЛО: self.kill() - мгновенное исчезновение
            # СТАЛО: Запускаем анимацию смерти
            self.set_state(self.STATE_DEATH)

    def draw_boss_ui(self, surface, offset):
        pass
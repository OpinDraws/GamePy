# entities/archangel_boss.py

import pygame
import math
import random
from core.config import WIDTH, HEIGHT, all_sprites, enemies, FPS 
from entities.weapons.boss_weapons import AngelSpearProjectile 
from rendering.archangel_render import draw_archangel_boss
from systems.vfx import GhostMistVFX, CelestialSmiteVFX, ShieldWaveVFX, ChaosRiftVFX

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
    STATE_PREPARE_DASH = 10 # <--- НОВОЕ СОСТОЯНИЕ
    STATE_PREPARE_PUNISHMENT_SPEARS = 11

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

    # --- КОНСТАНТЫ ДЛЯ НОВОЙ АТАКИ (Копья Наказания) ---
    PUNISHMENT_SPEAR_DELAY_MS = 500    # Начальная задержка перед всем паттерном
    PUNISHMENT_SPEAR_SIDE_OFFSET = 200 # Смещение вбок от игрока
    PUNISHMENT_SPEAR_DISTANCE = 50     # Расстояние между копьями (УВЕЛИЧЕНО до 50)
    PUNISHMENT_SPEAR_STAGGER_MS = 200  # Интервал между копьями (ритм атаки)
  
    # --- КОНСТАНТЫ МОБИЛЬНОСТИ (ФАЗА 2) ---
    DASH_COOLDOWN = 210 
    DASH_DURATION = 18
    # *** ИЗМЕНЕНИЕ 1: Увеличено с 400 до 560 (1.4x) для широких экранов ***
    MOVEMENT_RADIUS = 800 
    DASH_PREP_DURATION = int(0.7 * FPS) # 42 кадра
    
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
        self.groups = all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        
        self.player = player
        
        # Исходная точка (ЦЕЛЬ) - это Центр Круга
        self.spawn_pos = pygame.math.Vector2(x, y) 
        
        # Смещение портала ВВЕРХ
        # БЫЛО: 400. СТАЛО: 300. (Чтобы "чуть выше центра")
        self.portal_offset_y = 400 
        
        # При инициализации ставим босса сразу ВВЕРХУ (в портал)
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
        self.dash_prep_progress = 0.0 # Для отрисовки   
        
        # --- НОВЫЕ ПЕРЕМЕННЫЕ ---
        self.phantom_spears = [] 
        self.spear_wave_two_spawned = False 
        self.vfx_mist_active = False 
        self.attack_counter = 0 
        self.shake_func = player.shake_func 
        
        self.shield_cooldown_timer = 0 
        self.rift_timer = 0 
        self.dash_damage_dealt = False  # Флаг: нанесли ли урон рывком
        self.shield_scale_mult = 1.0    # Множитель размера щита (обычный = 1.0)
        
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
            print(f"BOSS SPAWN: Target={self.spawn_pos} (Center), Offset={self.portal_offset_y}")
            self.state = self.STATE_INTRO
            self.state_timer = 0
            self.is_active = True
            
            # Обновляем центр арены на точку спавна
            self.arena_center = self.spawn_pos.copy()
            
            # Телепортируем босса в точку ПОРТАЛА (ВВЕРХ: Y - Offset)
            self.pos = pygame.math.Vector2(self.spawn_pos.x, self.spawn_pos.y - self.portal_offset_y)
            self.current_alpha = 0

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
            
            # 1. Портал открывается
            if self.state_timer < self.INTRO_PORTAL_OPEN_TIME:
                self.intro_portal_progress = self.state_timer / self.INTRO_PORTAL_OPEN_TIME
                self.current_alpha = 0
                self.shake_func(1)
                
            # 2. Спуск босса (ВНИЗ: от Y-300 до Y)
            elif self.state_timer < self.INTRO_PORTAL_OPEN_TIME + self.INTRO_DESCEND_TIME:
                self.intro_portal_progress = 1.0
                descend_progress = (self.state_timer - self.INTRO_PORTAL_OPEN_TIME) / self.INTRO_DESCEND_TIME
                t = descend_progress
                ease = 1 - pow(1 - t, 3)
                
                # Точка старта (Верх)
                start_y = self.spawn_pos.y - self.portal_offset_y-400
                # Точка финиша (Центр)
                end_y = self.spawn_pos.y
                
                # Движение: Start -> End (Увеличение Y = Спуск вниз)
                self.pos.y = start_y + (end_y - start_y) * ease
                
                alpha_progress = min(1.0, descend_progress * 2.0)
                self.current_alpha = int(255 * alpha_progress)
                self.shake_func(2)
                
            # 3. Портал закрывается
            elif self.state_timer < self.INTRO_PORTAL_OPEN_TIME + self.INTRO_DESCEND_TIME + self.INTRO_PORTAL_CLOSE_TIME:
                self.current_alpha = 255
                self.pos.y = self.spawn_pos.y # Фиксируем ровно в центре
                close_t = (self.state_timer - (self.INTRO_PORTAL_OPEN_TIME + self.INTRO_DESCEND_TIME)) / self.INTRO_PORTAL_CLOSE_TIME
                self.intro_portal_progress = 1.0 - close_t
            
            else:
                self.state = self.STATE_HOVER
                self.intro_portal_progress = 0.0
                self.invulnerable = False
                self.cooldown_timer = 60
                enemies.add(self) 
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
        if self.is_phase_two and self.state not in [self.STATE_PHASE_TRANSITION, self.STATE_RECOVERY_PHASE_TWO, self.STATE_PHASE_TWO_DASH, self.STATE_CHAOS_BARRAGE, self.STATE_PREPARE_DASH]:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                if self.state == self.STATE_HOVER:
                    self.start_phase_two_dash() # Теперь это запускает подготовку

        # --- ФИЗИКА ДВИЖЕНИЯ ---
        if self.state == self.STATE_PHASE_TWO_DASH:
            progress = min(1.0, self.state_timer / self.DASH_DURATION)
            smooth_t = progress * progress * (3 - 2 * progress)
            self.pos = self.dash_start_pos.lerp(self.target_pos, smooth_t)
            move_vec = self.target_pos - self.dash_start_pos
            if move_vec.length() > 0:
                self.movement_tilt_x = (move_vec.normalize().x) * (1.0 - progress) 
            
            # --- НОВОЕ: УРОН ПРИ РЫВКЕ ---
            if not self.dash_damage_dealt:
                # Простая проверка коллизии (круг-круг)
                dist_to_player = (self.pos - self.player.pos).length()
                # Радиус босса + Радиус игрока + Запас
                collision_dist = self.radius + self.player.radius + 10
                
                if dist_to_player < collision_dist:
                    self.player.take_damage(10) # 10 единиц урона
                    self.dash_damage_dealt = True
                    self.shake_func(5) # Небольшая тряска при ударе
            # -----------------------------

            if self.state_timer >= self.DASH_DURATION:
                self.movement_tilt_x = 0.0 
                self.dash_timer = self.DASH_COOLDOWN
                
                # --- ИЗМЕНЕНИЕ: ПЕРЕХОД В АТАКУ ЩИТОМ ---
                # Вместо HOVER сразу бьем щитом
                self.shield_scale_mult = 1.5 # В 1.5 раза больше
                self.set_state(self.STATE_SHIELD_ATTACK)
                # ----------------------------------------
        
        elif self.state == self.STATE_CHAOS_BARRAGE:
            # Дрейф к центру во время ульты
            dir_to_center = self.arena_center - self.pos
            if dir_to_center.length() > 5:
                self.pos += dir_to_center.normalize() * 2.0 
            # Принудительная поза
            self.transition_pose_factor = 1.0
                
        else:
            if self.state == self.STATE_HOVER:
                self.target_pos = self.arena_center.copy()
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
                # --- ИЗМЕНЕНИЕ: Чередование 3-х атак ---
                # 0 = Обычные копья
                # 1 = Кара (Smite)
                # 2 = Копья Наказания (Новая)
                cycle = self.attack_counter % 3
                
                if cycle == 0:
                    self.set_state(self.STATE_PREPARE_SPEAR)
                    self.start_mist_effect(factor)
                    self.spawn_visual_spears(factor)
                elif cycle == 1:
                    self.set_state(self.STATE_PREPARE_SMITE)
                    self.start_smite_attack(factor) 
                else: # cycle == 2
                    self.set_state(self.STATE_PREPARE_PUNISHMENT_SPEARS)
                    # Спецэффекты для этой атаки (появление копий) 
                    # запускаются внутри логики этого состояния, здесь ничего звать не нужно.
                
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
        elif self.state == self.STATE_PREPARE_PUNISHMENT_SPEARS:
            # Используем время подготовки как для обычной атаки копьем
            full_state_duration = int(self.PREPARE_DURATION * factor)
            self.spear_animation_progress = self.state_timer / full_state_duration 
            
            if self.state_timer >= full_state_duration:
                # Спавним копья - они появятся и будут висеть 1 секунду
                self.spawn_punishment_spears()
                
                # Переходим в LAUNCH_SPEAR для завершающей анимации босса (45 кадров)
                self.set_state(self.STATE_LAUNCH_SPEAR) 
                self.state_timer = 0
                
                # Устанавливаем кулдаун, равный времени полета копья + небольшой буфер
                # Время полета: Задержка (1000мс) + Полет (500мс) + Буфер (~200мс) = 1700мс
                # Переводим в кадры: 1700 / (1000/FPS) ~ 102 кадра (при 60 FPS)
                cooldown_frames = int((self.PUNISHMENT_SPEAR_DELAY_MS + self.FIXED_FLIGHT_TIME_MS + 200) * (FPS / 1000))
                self.cooldown_timer = cooldown_frames

        elif self.state == self.STATE_LAUNCH_SPEAR:
            dur = int(self.LAUNCH_DURATION * factor) # <-- Здесь переменная называется dur
            progress = self.state_timer / dur
            self.spear_animation_progress = max(0.0, 1.0 - progress) 
            self.smite_vfx_progress = 0.0 
            
            # ИСПРАВЛЕНО: используем dur вместо full_state_duration
            if self.state_timer >= dur:
                # Если текущий кулдаун (установленный в Punishment Spears) больше обычного,
                # мы его НЕ перезаписываем. Если меньше или равен (обычная атака), сбрасываем.
                if self.cooldown_timer <= self.COOLDOWN_DURATION * factor:
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
                
                # СБРОС МНОЖИТЕЛЯ ЩИТА
                self.shield_scale_mult = 1.0
                
                self.set_state(self.STATE_HOVER)
        # --- НОВАЯ ЛОГИКА ПОДГОТОВКИ К РЫВКУ ---
        elif self.state == self.STATE_PREPARE_DASH:
            # Увеличиваем прогресс
            self.dash_prep_progress = self.state_timer / self.DASH_PREP_DURATION
            
            # Поворачиваем босса в сторону будущей точки рывка (для красоты)
            direction_to_target = self.target_pos.x - self.pos.x
            target_tilt = -1.0 if direction_to_target > 0 else 1.0 # Наклон в противоположную сторону (подготовка)
            self.movement_tilt_x += (target_tilt * 0.5 - self.movement_tilt_x) * 0.1

            if self.state_timer >= self.DASH_PREP_DURATION:
                self.execute_dash() # Переходим к самому рывку

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



    def spawn_punishment_spears(self):
        """
        Спавнит 8 копий (4 слева, 4 справа) вокруг ИГРОКА.
        Копья появляются по очереди и выстреливают сразу после появления следующего.
        """
        # 1. Фиксируем позицию цели (Игрока)
        # Если это первый кадр атаки, fixed_target_pos сбрасывается в (0,0) в update_state_logic,
        # поэтому здесь мы захватываем актуальную позицию игрока.
        if self.fixed_target_pos.length_squared() == 0: 
            self.fixed_target_pos = self.player.pos.copy()

        center_x = self.fixed_target_pos.x
        center_y = self.fixed_target_pos.y

        # Количество копий с каждой стороны
        SPEARS_PER_SIDE = 4
        
        # Общая высота построения (чтобы центрировать по вертикали относительно игрока)
        total_height = SPEARS_PER_SIDE * self.PUNISHMENT_SPEAR_DISTANCE
        start_y = center_y - (total_height / 2) + (self.PUNISHMENT_SPEAR_DISTANCE / 2)

        # Тайминг проявления копья (совпадает с интервалом, чтобы было бесшовно)
        APPEAR_TIME = self.PUNISHMENT_SPEAR_STAGGER_MS 

        # Счетчик для расчета задержек
        global_index = 0

        # --- 1. ЛЕВАЯ СТОРОНА (Летят ВПРАВО) ---
        X_LEFT = center_x - self.PUNISHMENT_SPEAR_SIDE_OFFSET
        
        for i in range(SPEARS_PER_SIDE):
            pos = pygame.math.Vector2(X_LEFT, start_y + i * self.PUNISHMENT_SPEAR_DISTANCE)
            direction = pygame.math.Vector2(1, 0) # Строго вправо
            
            # Расчет таймингов:
            # 1. Начало появления: Базовая задержка + Очередь * Интервал
            appear_delay = self.PUNISHMENT_SPEAR_DELAY_MS + global_index * self.PUNISHMENT_SPEAR_STAGGER_MS
            
            # 2. Выстрел: Сразу после того, как оно появилось (через APPEAR_TIME)
            # Это совпадает с моментом начала появления следующего копья.
            launch_delay = appear_delay + APPEAR_TIME
            
            AngelSpearProjectile(
                pos=pos, 
                direction=direction, 
                P_target=self.fixed_target_pos, # (не используется при прямом полете, но нужен для инита)
                custom_travel_time_ms=self.FIXED_FLIGHT_TIME_MS, 
                mist_duration=0, 
                groups=all_sprites, 
                launch_delay_ms=launch_delay,
                appearance_delay_ms=appear_delay
            )
            global_index += 1

        # --- 2. ПРАВАЯ СТОРОНА (Летят ВЛЕВО) ---
        X_RIGHT = center_x + self.PUNISHMENT_SPEAR_SIDE_OFFSET
        
        for i in range(SPEARS_PER_SIDE):
            pos = pygame.math.Vector2(X_RIGHT, start_y + i * self.PUNISHMENT_SPEAR_DISTANCE)
            direction = pygame.math.Vector2(-1, 0) # Строго влево
            
            appear_delay = self.PUNISHMENT_SPEAR_DELAY_MS + global_index * self.PUNISHMENT_SPEAR_STAGGER_MS
            launch_delay = appear_delay + APPEAR_TIME
            
            AngelSpearProjectile(
                pos=pos, 
                direction=direction, 
                P_target=self.fixed_target_pos, 
                custom_travel_time_ms=self.FIXED_FLIGHT_TIME_MS, 
                mist_duration=0, 
                groups=all_sprites, 
                launch_delay_ms=launch_delay,
                appearance_delay_ms=appear_delay
            )
            global_index += 1

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
        spawned_positions = [] 

        for _ in range(count):
            for _ in range(15): 
                # --- ЗАМЕНИТЬ ГЕНЕРАЦИЮ X/Y НА ЭТО ---
                # Используем координаты относительно центра арены
                min_x = int(self.arena_center.x - 900)
                max_x = int(self.arena_center.x + 900)
                min_y = int(self.arena_center.y - 900)
                max_y = int(self.arena_center.y + 900)
                
                x = random.randint(min_x, max_x)
                y = random.randint(min_y, max_y)
                # ---------------------------------------
                
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
        """
        Начинает ПОДГОТОВКУ к рывку.
        Выбирает точку с учетом приоритетов:
        - 40%: Агрессивно к игроку (радиус 350)
        - 35%: Отступление/Кайт (дальше 600 от игрока)
        - 25%: Случайное патрулирование (старая логика)
        """
        self.set_state(self.STATE_PREPARE_DASH)
        self.dash_prep_progress = 0.0
        self.dash_start_pos = self.pos.copy()
        
        # Границы арены (центр +/- 900)
        min_x = self.arena_center.x - 900
        max_x = self.arena_center.x + 900
        min_y = self.arena_center.y - 900
        max_y = self.arena_center.y + 900

        # Точка по умолчанию (на случай если не найдем идеальную)
        target_pos = self.arena_center.copy() 
        
        # Бросаем кубик судьбы
        roll = random.random() # 0.0 ... 1.0
        
        if roll < 0.40:
            strategy = 'AGGRO' # Возле игрока
        elif roll < 0.75:      # 0.40 + 0.35 = 0.75
            strategy = 'KITE'  # Далеко от игрока
        else:
            strategy = 'RANDOM' # Как раньше

        # Пытаемся найти точку (15 попыток)
        for _ in range(15):
            candidate = pygame.math.Vector2()
            
            if strategy == 'AGGRO':
                # Случайная точка в радиусе 100-350 от игрока
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(50, 350) 
                offset = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * dist
                candidate = self.player.pos + offset
                
            elif strategy == 'KITE':
                # Случайная точка на арене
                rx = random.uniform(min_x, max_x)
                ry = random.uniform(min_y, max_y)
                candidate = pygame.math.Vector2(rx, ry)
                
            else: # RANDOM (Старая логика)
                # Кольцо вокруг центра арены
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(420, self.MOVEMENT_RADIUS) 
                offset = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * dist
                candidate = self.arena_center + offset

            # 1. Ограничиваем границами арены
            candidate.x = max(min_x, min(max_x, candidate.x))
            candidate.y = max(min_y, min(max_y, candidate.y))
            
            # 2. Проверки валидности
            valid = True
            
            # Проверка длины рывка (босс не должен прыгать на 1 метр)
            # Если точка слишком близко к БОССУ, ищем другую
            if (candidate - self.pos).length() < 250:
                valid = False
            
            # Специфичная проверка для KITE (должна быть далеко от ИГРОКА)
            if valid and strategy == 'KITE':
                dist_to_player = (candidate - self.player.pos).length()
                if dist_to_player < 600:
                    valid = False
            
            # Если точка прошла все проверки - берем её
            if valid:
                target_pos = candidate
                break
        
        self.target_pos = target_pos
        # Босс не двигается сразу, он ждет окончания таймера STATE_PREPARE_DASH (0.7 сек)

    def execute_dash(self):
        """
        Фактическое выполнение рывка.
        """
        self.set_state(self.STATE_PHASE_TWO_DASH)
        self.dash_prep_progress = 0.0
        self.dash_damage_dealt = False # Сбрасываем флаг урона перед рывком
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
        
        # Базовый радиус
        base_radius = 300 if self.is_phase_two else 190
        
        # Применяем множитель (будет 1.5 после рывка, 1.0 обычно)
        final_radius = base_radius * self.shield_scale_mult
        
        ShieldWaveVFX(wave_pos, max_radius=final_radius, damage=30, push_force=25, duration=30)
        self.shake_func(10 * self.shield_scale_mult) # Тряска тоже сильнее

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
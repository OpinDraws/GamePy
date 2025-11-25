import pygame
import math
import random 
from core.config import *
from vfx import Particle
from weapons import SlashProjectile 
import rendering
from skills import SkillManager

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, particle_groups, shake_func):
        super().__init__(groups)
        
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(0, 0)
        
        # --- ХИТБОКС ---
        self.hitbox_width = 24 
        self.hitbox_height = 50 # Сделаем чуть меньше, чтобы ноги не цеплялись
        self.hitbox_offset_y = -20 
        self.radius = self.hitbox_height // 2
        
        # --- ВИЗУАЛ ---
        self.surface_size = 260 
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.visual_center = pygame.math.Vector2(self.surface_size // 2, self.surface_size // 2)

        # Физика плаща
        self.cape_len = 8
        self.cape_seg_dist = 10
        self.cape_points = [pygame.math.Vector2(self.visual_center) for _ in range(self.cape_len)]

        # Физика движения
        self.acc = 0.8
        self.friction = 0.15
        self.max_speed = 6
        
        self.obstacle_sprites = obstacle_sprites # Стены для коллизий
        self.particle_groups = particle_groups
        self.shake_func = shake_func
        
        # Здоровье и состояния
        self.max_hp = 100
        self.hp = self.max_hp
        self.invulnerable = False
        self.invul_timer = 0
        self.invul_duration = 200 
        
        # Стрельба
        self.can_shoot = True
        self.shoot_timer = 0
        self.shoot_cooldown = 200 
        
        self.bullet_group_ref = None
        self.all_sprites_ref = None
        
        # Dash
        self.can_dash = True
        self.dash_timer = 0
        self.dash_cooldown = 1600
        self.is_dashing = False
        self.dash_duration = 200
        self.dash_start_time = 0
        self.dash_vector = pygame.math.Vector2(0,0)
        self.dash_speed = 18

        self.skill_manager = SkillManager(self)

        self.angle = 0
        self.walk_cycle = 0
        
    def get_hitbox_rect(self):
        """Возвращает Rect коллизии относительно текущей позиции self.pos"""
        return pygame.Rect(
            self.pos.x - self.hitbox_width // 2,
            self.pos.y + self.hitbox_offset_y - self.hitbox_height // 2,
            self.hitbox_width,
            self.hitbox_height
        )

    def get_mouse_angle(self):
        mx, my = pygame.mouse.get_pos()
        # Учитываем смещение камеры при расчете угла!
        # (self.rect уже содержит смещение камеры при отрисовке, но self.pos - это мировые координаты)
        # Но mouse_pos - экранные. 
        # В текущей архитектуре мышь экранная, а игрок мировой.
        # Разница координат должна учитывать камеру.
        # Пока оставим как есть (ломаться не должно, если камера центрирована на игроке).
        dx = mx - (self.rect.centerx)
        dy = my - (self.rect.centery)
        deg = math.degrees(math.atan2(dy, dx))
        if deg < 0: deg += 360
        return deg

    def physics(self, dt):
        current_time = pygame.time.get_ticks()
        
        if self.is_dashing:
            if current_time - self.dash_start_time > self.dash_duration:
                self.is_dashing = False
                self.vel *= 0.5 
            else:
                self.vel = self.dash_vector 
                # Эффект следа
                if random.random() < 0.5:
                    trail_pos = self.pos + pygame.math.Vector2(random.randint(-10,10), random.randint(-10,10))
                    Particle(trail_pos, self.particle_groups, color=(50, 0, 50), speed=0, decay=8, scale_speed=1)
        else:
            # Трение
            self.vel *= (1 - self.friction)
            if self.vel.length() > self.max_speed:
                self.vel.scale_to_length(self.max_speed)

        # --- РАЗДЕЛЬНОЕ ДВИЖЕНИЕ ПО ОСЯМ ---
        
        # 1. Движение по X
        self.pos.x += self.vel.x * dt * 60
        self.collision('horizontal')
        
        # 2. Движение по Y
        self.pos.y += self.vel.y * dt * 60
        self.collision('vertical')

        # Обновляем позицию спрайта (для камеры и отрисовки)
        self.rect.center = self.pos

    def collision(self, direction):
        """Обработка столкновений со стенами."""
        if not self.obstacle_sprites: return

        # Получаем актуальный хитбокс
        hitbox = self.get_hitbox_rect()
        
        # Находим все стены, с которыми мы пересеклись
        hits = [sprite for sprite in self.obstacle_sprites if hitbox.colliderect(sprite.rect)]
        
        if hits:
            if direction == 'horizontal':
                for sprite in hits:
                    # Если двигались вправо -> уперлись в левую стенку спрайта
                    if self.vel.x > 0:
                        hitbox.right = sprite.rect.left
                        self.vel.x = 0 # Останавливаем инерцию
                    # Если двигались влево -> уперлись в правую стенку
                    elif self.vel.x < 0:
                        hitbox.left = sprite.rect.right
                        self.vel.x = 0
                
                # Обновляем реальную позицию из скорректированного хитбокса
                self.pos.x = hitbox.centerx

            if direction == 'vertical':
                for sprite in hits:
                    # Двигались вниз
                    if self.vel.y > 0:
                        hitbox.bottom = sprite.rect.top
                        self.vel.y = 0
                    # Двигались вверх
                    elif self.vel.y < 0:
                        hitbox.top = sprite.rect.bottom
                        self.vel.y = 0
                
                # Обновляем реальную позицию
                self.pos.y = hitbox.centery - self.hitbox_offset_y

    # ... (Остальные методы: take_damage, die, update_invulnerability, update_cape_physics, animate_visuals, input, dash, shoot) ...
    # ОНИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ, просто скопируй их из старого файла или оставь как были
    
    def take_damage(self, amount):
        current_time = pygame.time.get_ticks()
        if not self.invulnerable and not self.is_dashing:
            self.hp -= amount
            self.invulnerable = True
            self.invul_timer = current_time
            self.shake_func(20)
            for _ in range(15):
                Particle(self.pos, self.particle_groups, color=(255, 0, 0), speed=5, decay=15)
            if self.hp <= 0:
                self.die()

    def die(self):
        print("Player Died!")
        self.kill()

    def update_invulnerability(self):
        if self.invulnerable:
            current_time = pygame.time.get_ticks()
            if current_time - self.invul_timer >= self.invul_duration:
                self.invulnerable = False

    def update_cape_physics(self):
        gravity = pygame.math.Vector2(0, 3)
        bounce_y = abs(math.sin(self.walk_cycle)) * 4 if self.vel.length() > 0.1 else 0
        anchor = self.visual_center + pygame.math.Vector2(0, -42 + bounce_y)
        self.cape_points[0] = anchor
        
        wind = pygame.math.Vector2(-self.vel.x * 2, -self.vel.y * 2) 
        for i in range(1, self.cape_len):
            prev = self.cape_points[i-1]
            curr = self.cape_points[i]
            target = prev + pygame.math.Vector2(0, self.cape_seg_dist)
            if self.vel.length() > 0.1: target += wind
            noise = math.sin(pygame.time.get_ticks() * 0.01 + i) * 2
            target.x += noise
            self.cape_points[i] = curr.lerp(target, 0.4) 

        for _ in range(3):
            for i in range(self.cape_len - 1):
                p1 = self.cape_points[i]
                p2 = self.cape_points[i+1]
                delta = p2 - p1
                dist = delta.length()
                if dist > self.cape_seg_dist:
                    correction = delta.normalize() * self.cape_seg_dist
                    self.cape_points[i+1] = p1 + correction

    def animate_visuals(self):
        self.image.fill((0, 0, 0, 0)) 
        speed = self.vel.length()
        if speed > 0.5: self.walk_cycle += 0.15 
        else: self.walk_cycle = 0 
        self.update_cape_physics()
        alpha_mult = 1.0
        if self.invulnerable:
            flash = (pygame.time.get_ticks() // 30) % 2 == 0
            if flash: alpha_mult = 0.5 
        rendering.draw_vampire_advanced(
            self.image,
            (int(self.visual_center.x), int(self.visual_center.y)),
            self.angle,
            self.walk_cycle,
            self.vel,
            self.cape_points,
            alpha_mult
        )

    def input(self):
        keys = pygame.key.get_pressed()
        self.skill_manager.handle_input(keys)
        
        if not self.is_dashing:
            direction = pygame.math.Vector2(0, 0)
            if keys[pygame.K_w]: direction.y = -1
            if keys[pygame.K_s]: direction.y = 1
            if keys[pygame.K_a]: direction.x = -1
            if keys[pygame.K_d]: direction.x = 1
            if direction.length() > 0: direction = direction.normalize()
            
            self.vel += direction * self.acc
            
            if not self.can_shoot:
                self.vel *= 0.8 
            
            if keys[pygame.K_SPACE] and self.can_dash: 
                self.dash(direction)
        
        if pygame.mouse.get_pressed()[0] and self.can_shoot: 
            self.shoot()

    def dash(self, direction):
        if direction.length() == 0: 
            rad = math.radians(self.angle)
            direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        self.is_dashing = True
        self.can_dash = False
        self.dash_timer = pygame.time.get_ticks()
        self.dash_start_time = pygame.time.get_ticks()
        self.dash_vector = direction * self.dash_speed
        self.vel = self.dash_vector 
        self.shake_func(8)
        for _ in range(20):
            Particle(self.pos, self.particle_groups, color=(20, 20, 30), speed=2, decay=5)

    def shoot(self):
        self.can_shoot = False
        self.shoot_timer = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        # ВАЖНО: Прицеливание мышью теперь работает от экранного центра (так как игрок всегда в центре)
        # Но позиция мыши абсолютная.
        # Простейший фикс: вектор от центра экрана (где игрок) к мыши.
        screen_center = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
        mouse_vec = pygame.math.Vector2(mouse_pos) - screen_center
        
        direction = pygame.math.Vector2(1,0)
        if mouse_vec.length() > 0:
            direction = mouse_vec.normalize()
        
        base_pos = self.pos
        shoulder_offset = pygame.math.Vector2(0, -50)
        hand_reach = 35
        hand_offset = direction * hand_reach
        spawn_pos = base_pos + shoulder_offset + hand_offset
        
        target_groups = [self.bullet_group_ref]
        if self.all_sprites_ref:
            target_groups.append(self.all_sprites_ref)
        elif len(self.groups()) > 0:
             target_groups.append(self.groups()[0])

        SlashProjectile(spawn_pos, direction, target_groups, self.particle_groups)
        self.pos -= direction * 2

    def update_custom(self, dt, enemies_group, bullet_group, all_sprites_group):
        self.bullet_group_ref = bullet_group
        self.all_sprites_ref = all_sprites_group
        
        self.input()
        self.update_invulnerability() 
        self.angle = self.get_mouse_angle()
        self.skill_manager.update(dt, enemies_group)
        self.animate_visuals()
        self.physics(dt)
        self.cooldowns()
        
        if self.vel.length() > 2 and random.random() < 0.2:
            trail_pos = self.pos + pygame.math.Vector2(random.randint(-5,5), 10)
            Particle(trail_pos, self.particle_groups, color=(10, 0, 10), speed=0, decay=10, scale_speed=1)

    def cooldowns(self):
        current_time = pygame.time.get_ticks()
        if not self.can_shoot and current_time - self.shoot_timer >= self.shoot_cooldown:
            self.can_shoot = True 
        if not self.can_dash and current_time - self.dash_timer >= self.dash_cooldown:
            self.can_dash = True
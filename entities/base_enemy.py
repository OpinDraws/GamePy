import pygame
from core.config import enemies, COLOR_MONSTER_BODY
from systems.vfx import Particle

class BaseEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, player, groups, particle_groups, shake_func, health):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.player = player
        self.particle_groups = particle_groups
        self.shake_func = shake_func
        
        self.health = health
        self.max_health = health
        
        # --- СИСТЕМА БАФФОВ ---
        self.is_buffed = False
        self.buff_timer = 0
        
        # Множители
        self.speed_mult = 1.0
        self.damage_mult = 1.0
        self.anim_mult = 1.0
        self.cooldown_mult = 1.0 # НОВЫЙ МНОЖИТЕЛЬ КУЛДАУНОВ
        
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=pos)

    # ОБНОВЛЕННЫЙ МЕТОД: добавлен cooldown_factor
    def apply_rage_buff(self, duration, speed_factor, damage_factor, cooldown_factor):
        """Применяет бафф ярости."""
        self.is_buffed = True
        self.buff_timer = duration
        
        self.speed_mult = speed_factor
        self.damage_mult = damage_factor
        self.anim_mult = speed_factor        # Анимация ускоряется как движение
        self.cooldown_mult = cooldown_factor # Кулдауны откатываются быстрее
        
        # Эффект получения баффа
        for _ in range(10):
            Particle(self.pos, self.particle_groups, color=(255, 50, 50), speed=5, decay=5)

    def update_buffs(self):
        if self.is_buffed:
            self.buff_timer -= 1
            if self.buff_timer % 10 == 0:
                Particle(self.pos, self.particle_groups, color=(255, 0, 0), speed=2, decay=10)
            if self.buff_timer <= 0:
                self.remove_buffs()

    def remove_buffs(self):
        self.is_buffed = False
        self.speed_mult = 1.0
        self.damage_mult = 1.0
        self.anim_mult = 1.0
        self.cooldown_mult = 1.0 # Сброс кулдауна

    def soft_collision(self):
        for other in enemies:
            if other != self:
                dist_vec = self.pos - other.pos
                dist = dist_vec.length()
                if 0 < dist < 70: 
                    push = dist_vec.normalize() * (2.0 / dist * 60)
                    self.pos += push

    def take_damage(self, amount):
        self.health -= amount
        for _ in range(5):
            Particle(self.pos, self.particle_groups, color=(100, 0, 100), speed=4, decay=10)
        if self.health <= 0:
            self.die()

    def die(self):
        self.shake_func(12)
        for _ in range(40):
            Particle(self.pos, self.particle_groups, color=COLOR_MONSTER_BODY, speed=6, decay=3)
        self.kill()
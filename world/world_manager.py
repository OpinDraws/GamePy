import pygame
from world.tile_map import Map, Tile
from core.config import all_sprites, enemies, particles, TILE_SIZE, WIDTH, HEIGHT
from entities.tentacle_enemy import TentacleEnemy

class TriggerZone(pygame.sprite.Sprite):
    # Класс оставлен, но в коде не используется, т.к. нет триггеров
    def __init__(self, pos, groups, target_room, target_spawn_pos):
        super().__init__(groups)
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=pos)
        self.target_room = target_room
        self.target_spawn_pos = target_spawn_pos

class WorldManager:
    def __init__(self, player, camera, shake_func, collision_func):
        self.player = player
        self.collision_func = collision_func
        self.camera = camera
        self.shake_func = shake_func
        self.current_room = None
        self.map_instance = None
        self.trigger_zones = pygame.sprite.Group()

        # --- ДАННЫЕ КОМНАТ (КАРТЫ) ---
        # ОСТАВЛЕНА ТОЛЬКО ОДНА КОМНАТА: BOSS ARENA
        self.rooms = {
            "boss_arena": {
                # Большая арена 40 x 15 тайлов
                "layout": [
                    "########################################",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "#......................................#",
                    "########################################"
                ],
                "enemies": [], # Врагов нет
                "triggers": [] # Триггеров нет
            }
        }
        
    def load_room(self, room_name, spawn_point):
        if room_name not in self.rooms:
            print(f"ERROR: Room '{room_name}' not found!")
            return

        print(f"Loading room: {room_name}")
        room_data = self.rooms[room_name]
        self.current_room = room_name

        # 1. Очистка старых объектов
        enemies.empty()
        self.trigger_zones.empty()
        all_sprites.remove([s for s in all_sprites if isinstance(s, Tile)]) 
        
        # 2. Создание новой карты (Map и Tile)
        self.map_instance = Map(room_data["layout"])
        
        # Триггер-зон больше нет, поэтому блок создания триггеров пуст.
        
        # 3. Настройка камеры и препятствий для игрока
        self.camera.width = self.map_instance.width
        self.camera.height = self.map_instance.height
        self.player.obstacle_sprites = self.map_instance.obstacles 

        # 4. Спавн врагов (список пуст)
        for e_pos in room_data["enemies"]:
            TentacleEnemy(e_pos, self.player, all_sprites, particles, self.shake_func) 
        
        # 5. Перемещение игрока
        self.player.pos = pygame.math.Vector2(spawn_point)
        self.player.rect.center = self.player.pos 
        self.camera.update(self.player.rect)

    def update(self, dt):
        """Проверка коллизий с триггер-зонами. (Будет пропущено)"""
        if not self.map_instance: return

        # Проверка, находится ли игрок в зоне перехода (триггеров нет)
        hit_zone = pygame.sprite.spritecollideany(self.player, self.trigger_zones, self.collision_func)
        
        if hit_zone:
            self.load_room(hit_zone.target_room, hit_zone.target_spawn_pos)

    def draw_map(self, screen, offset):
        """Отрисовка всех объектов карты (стены)."""
        if self.map_instance:
            for tile in self.map_instance.all_map_sprites:
                screen.blit(tile.image, tile.rect.topleft + offset)
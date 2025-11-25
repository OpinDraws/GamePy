import pygame
from world.tile_map import Map, Tile
from core.config import all_sprites, enemies, particles, TILE_SIZE, WIDTH, HEIGHT
from entities.tentacle_enemy import TentacleEnemy
# from scenes.game_scene import complex_collision_check

class TriggerZone(pygame.sprite.Sprite):
    """
    Невидимый спрайт, при столкновении с которым происходит переход.
    """
    def __init__(self, pos, groups, target_room, target_spawn_pos):
        super().__init__(groups)
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        # Для отладки можно нарисовать полупрозрачный желтый квадрат:
        # pygame.draw.rect(self.image, (255, 255, 0, 50), (0, 0, TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.target_room = target_room
        self.target_spawn_pos = target_spawn_pos

class WorldManager:
    def __init__(self, player, camera, shake_func, collision_func): # ДОБАВЛЕНО
        self.player = player
        self.collision_func = collision_func # СОХРАНЯЕМ ФУНКЦИЮ
        self.camera = camera
        self.shake_func = shake_func
        self.current_room = None
        self.map_instance = None
        self.trigger_zones = pygame.sprite.Group()

        # --- ДАННЫЕ КОМНАТ (КАРТЫ) ---
        # > и < — это символы триггеров
        self.rooms = {
            "start_room": {
                "layout": [
                    "############################################################",
                    "#..........................................................#",
                    "#..........................................................#",
                    "#....................#.#...................................#",
                    "#..........................................................#",
                    "#..........................................................#",
                    "#..........................................................#",
                    "#..........................................................#",
                    "#.........................................................>#", # Выход в next_room
                    "############################################################"
                ],
                "enemies": [(3 * TILE_SIZE, 8 * TILE_SIZE), (10 * TILE_SIZE, 8 * TILE_SIZE)],
                "triggers": [
                    {"char": ">", "target": "next_room", "spawn_point": (TILE_SIZE * 2, TILE_SIZE * 8)}
                ]
            },
            "next_room": {
                "layout": [
                    "############################################################",
                    "#<.........................................................#", # Выход в start_room
                    "#..........................................................#",
                    "#..........................................................#",
                    "#..........................................................#",
                    "#..........................................................#",
                    "#..........................................................#",
                    "#..........................................................#",
                    "#..........................................................#",
                    "############################################################"
                ],
                "enemies": [],
                "triggers": [
                    {"char": "<", "target": "start_room", "spawn_point": (TILE_SIZE * 57, TILE_SIZE * 8)}
                ]
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
        all_sprites.remove([s for s in all_sprites if isinstance(s, Tile)]) # Удаляем старые стены
        
        # 2. Создание новой карты и триггер-зон
        self.map_instance = Map(room_data["layout"])
        
        # Создаем триггер-зоны на основе данных карты
        for row, tiles in enumerate(room_data["layout"]):
            for col, tile_char in enumerate(tiles):
                trigger_data = next((t for t in room_data["triggers"] if t["char"] == tile_char), None)
                if trigger_data:
                    pos = (col * TILE_SIZE, row * TILE_SIZE)
                    TriggerZone(
                        pos, 
                        self.trigger_zones, 
                        trigger_data["target"], 
                        trigger_data["spawn_point"]
                    )

        # 3. Настройка камеры и препятствий для игрока
        self.camera.width = self.map_instance.width
        self.camera.height = self.map_instance.height
        self.player.obstacle_sprites = self.map_instance.obstacles # Обновляем группу препятствий игрока

        # 4. Спавн врагов
        for e_pos in room_data["enemies"]:
            # Враги должны быть добавлены в all_sprites и enemies
            # Используем TentacleEnemy, созданный на Этапе 7
            TentacleEnemy(e_pos, self.player, all_sprites, particles, self.shake_func) 
        
        # 5. Перемещение игрока
        self.player.pos = pygame.math.Vector2(spawn_point)
        self.player.rect.center = self.player.pos 
        self.camera.update(self.player.rect)

    def update(self, dt):
        """Проверка коллизий с триггер-зонами."""
        if not self.map_instance: return

        # Проверка, находится ли игрок в зоне перехода
        hit_zone = pygame.sprite.spritecollideany(self.player, self.trigger_zones, complex_collision_check)
        
        if hit_zone:
            # Если зона найдена, загружаем новую комнату и спавним игрока в целевой точке
            self.load_room(hit_zone.target_room, hit_zone.target_spawn_pos)

    def draw_map(self, screen, offset):
        """Отрисовка всех объектов карты (стены)."""
        if self.map_instance:
            for tile in self.map_instance.all_map_sprites:
                screen.blit(tile.image, tile.rect.topleft + offset)
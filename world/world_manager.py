import pygame
from world.tile_map import Map, Tile
from core.config import all_sprites, enemies, particles, TILE_SIZE, WIDTH, HEIGHT
from entities.tentacle_enemy import TentacleEnemy
from entities.gate import Gate

class TriggerZone(pygame.sprite.Sprite):
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
        
        self.gates = pygame.sprite.Group()
        self.trigger_zones = pygame.sprite.Group()

        # Генерируем карту
        arena_layout = self._generate_boss_level_layout()

        self.rooms = {
            "boss_arena": {
                "layout": arena_layout,
                "enemies": [], 
                "triggers": [] 
            }
        }

    def _generate_boss_level_layout(self):
        """
        Структура карты (Сверху вниз).
        ВСЯ КАРТА: 50 тайлов шириной (2000 пикселей).
        """
        WIDTH_TILES = 50
        
        # --- 1. АРЕНА БОССА (ВЕРХ) ---
        # Делаем её КВАДРАТНОЙ (50x50 тайлов = 2000x2000 пикселей)
        # Центр будет ровно в (1000, 1000)
        BOSS_ROOM_H = 50 
        
        # Коридор и старт
        CORRIDOR_H = 15
        START_ROOM_H = 25
        CORRIDOR_W = 6          
        
        layout = []
        
        # Строим Арену
        layout.append("#" * WIDTH_TILES)
        for _ in range(BOSS_ROOM_H - 2):
            layout.append("#" + "." * (WIDTH_TILES - 2) + "#")
            
        # Строим Ворота (Выход с арены)
        wall_len = (WIDTH_TILES - CORRIDOR_W) // 2
        gate_row = "#" * wall_len + "=" * CORRIDOR_W + "#" * wall_len
        while len(gate_row) < WIDTH_TILES: gate_row += "#"
        layout.append(gate_row)
        
        # Строим Коридор
        empty_len = wall_len
        corridor_inner = "#" + "." * (CORRIDOR_W - 2) + "#"
        corridor_row = " " * empty_len + corridor_inner + " " * empty_len
        while len(corridor_row) < WIDTH_TILES: corridor_row += " "
            
        for _ in range(CORRIDOR_H - 1):
            layout.append(corridor_row)
            
        # Вход в коридор
        entry_row = "#" * wall_len + "." * CORRIDOR_W + "#" * wall_len
        while len(entry_row) < WIDTH_TILES: entry_row += "#"
        layout.append(entry_row)
        
        # Стартовая комната (Низ)
        for _ in range(START_ROOM_H - 2):
            layout.append("#" + "." * (WIDTH_TILES - 2) + "#")
        layout.append("#" * WIDTH_TILES)
        
        return layout
        
    def load_room(self, room_name, spawn_point):
        if room_name not in self.rooms:
            print(f"ERROR: Room '{room_name}' not found!")
            return

        print(f"Loading room: {room_name}")
        room_data = self.rooms[room_name]
        self.current_room = room_name

        enemies.empty()
        self.trigger_zones.empty()
        self.gates.empty()
        
        sprites_to_remove = [s for s in all_sprites if isinstance(s, Tile) or isinstance(s, Gate)]
        for s in sprites_to_remove:
            s.kill()
        
        self.map_instance = Map(room_data["layout"])
        
        for row_idx, row_str in enumerate(room_data["layout"]):
            for col_idx, char in enumerate(row_str):
                pos = (col_idx * TILE_SIZE, row_idx * TILE_SIZE)
                if char == '=':
                    Gate(pos, [self.gates, self.map_instance.obstacles, self.map_instance.all_map_sprites])

        self.camera.width = self.map_instance.width
        self.camera.height = self.map_instance.height
        self.player.obstacle_sprites = self.map_instance.obstacles 

        for e_pos in room_data["enemies"]:
            TentacleEnemy(e_pos, self.player, all_sprites, particles, self.shake_func) 
        
        self.player.pos = pygame.math.Vector2(spawn_point)
        self.player.rect.center = self.player.pos 
        self.camera.update(self.player.rect)

    def update(self, dt):
        if not self.map_instance: return

    def draw_map(self, screen, offset):
        if self.map_instance:
            for tile in self.map_instance.all_map_sprites:
                screen.blit(tile.image, tile.rect.topleft + offset)
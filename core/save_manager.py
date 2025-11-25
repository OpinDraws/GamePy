import json
import os
from core.config import BASE_DIR

# Путь к файлу сохранения
SAVE_FILE = os.path.join(BASE_DIR, 'save_game.json')

def get_default_save_data():
    """Возвращает начальное состояние новой игры."""
    return {
        "hp": 100,
        "max_hp": 100,
        "current_room": "boss_arena",
        "spawn_pos": [500, 500], # Используем список, так как JSON не хранит кортежи
        "dead_bosses": [],
        "unlocked_skills": ["flurry"]
    }

class SaveManager:
    @staticmethod
    def save_game(player_data, world_data):
        """
        Объединяет данные игрока и мира, и сохраняет в файл.
        """
        # Объединяем словари (Python 3.5+)
        full_data = {**player_data, **world_data}
        
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(full_data, f, indent=4)
            print("Игра сохранена")
        except Exception as e:
            print(f"Ошибка сохранения игры: {e}")

    @staticmethod
    def load_game():
        """
        Загружает данные из файла. Возвращает словарь или None.
        """
        if not os.path.exists(SAVE_FILE):
            return None
            
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
            print("Игра загружена")
            return data
        except Exception as e:
            print(f"Ошибка загрузки сохранения: {e}")
            return None
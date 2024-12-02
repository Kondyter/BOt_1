import random
from typing import Tuple, Dict, Any
from flask import Flask, Response, request, jsonify

app = Flask(__name__)

DB: Dict[int, Any] = {}
CONTEXT = {
    'round': 0,
    'map': None,
    'size': None,
    'init_balance': 0,
    'agent_id': 0
}

# Константи
DIRECTIONS = [[-1, 0], [0, 1], [1, 0], [0, -1]]

# Функція для вибору споруди на основі типу території
def get_power_structure(terrain_type: str) -> str:
    return {
        'OCEAN': 'WINDMILL',
        'DESERT': 'SOLAR_PANELS',
        'MOUNTAIN': 'GEOTHERMAL',
        'RIVER': 'DAM',
        'PLAINS': 'WINDMILL'
    }.get(terrain_type)

# Функція для отримання типу території
def get_terrain(x: int, y: int) -> dict:
    if 0 <= x < CONTEXT['size'] and 0 <= y < CONTEXT['size']:
        return CONTEXT['map'][x][y]
    return {}

# Обробка дій для фабрики
def handle_factory_action(bot: dict, current_round: int, balance: int) -> dict:
    if current_round == 1:
        return {"type": "BUILD_BOT", "params": {"d_loc": [0, 1]}}
    elif current_round == 2 or (current_round > 5 and balance >= 150):
        return {"type": "ASSEMBLE_POWER_PLANT", "params": {"power_type": "WINDMILL"}}
 #   elif current_round == 20 and balance > 600:
 #       return {"type": "ASSEMBLE_POWER_PLANT", "params": {"power_type": "GEOTHERMAL"}} # відкрити, коли будуть відповідні умови
#   elif current_round > 25 and balance > 1200:
#        return {"type": "ASSEMBLE_POWER_PLANT", "params": {"power_type": "DAM"}} # відкрити, коли будуть відповідні умови
    elif current_round == 12 and balance >= 150:
        return {"type": "BUILD_BOT", "params": {"d_loc": [1, -1]}}
    elif current_round == 15 and balance >= 150:
        return {"type": "BUILD_BOT", "params": {"d_loc": [-1, 1]}}
    return {"type": "NONE", "params": {}}

# Обробка дій для інженерного бота
def handle_engineer_action(bot: dict, balance: int) -> dict:
    x, y = bot['location']
    terrain = get_terrain(x, y)
    terrain_type = terrain.get('type', None)

    # Якщо інженер знайшов існуючу структуру, виконує RECONFIGURE
    if terrain_type in ['WINDMILL', 'SOLAR_PANELS', 'GEOTHERMAL', 'DAM']:# напевно варто додати переівірку на колір команди, щоб не перелаштовувати свої
        return {
            "type": "RECONFIGURE",
            "params": {
                "d_loc": random.choice(DIRECTIONS)
            }
        }

    # Якщо місцевість підходить для будівництва
    if terrain_type in ['OCEAN', 'DESERT', 'MOUNTAIN', 'RIVER', 'PLAINS']:
        power_type = get_power_structure(terrain_type)
        if balance >= 50:
            return {
                "type": "DEPLOY",
                "params": {
                    "power_type": power_type,
                    "d_loc": random.choice(DIRECTIONS)
                }
            }
    return {
        "type": "MOVE",
        "params": {
            "d_loc": random.choice(DIRECTIONS)
        }
    }

# Сервіси Flask
@app.get('/health')
def health() -> Response:
    return Response(status=200)

@app.post('/init')
def init() -> Response:
    size = request.json['map_size']
    CONTEXT['map'] = [[None] * size for _ in range(size)]
    CONTEXT['size'] = size
    CONTEXT['init_balance'] = request.json['init_balance']
    return Response(status=200)

@app.post('/round')
def update_round() -> Response:
    CONTEXT['round'] = request.json['round']
    return Response(status=200)

@app.post('/agent/<int:bot_id>')
def create_bot(bot_id: int) -> Response:
    DB[bot_id] = request.json
    return Response(status=200)

@app.get('/agent/<int:bot_id>/action')
def get_bot_action(bot_id: int) -> Tuple[dict, int]:
    bot = DB.get(bot_id)
    if not bot:
        return {"error": "Bot not found"}, 404

    bot_type = bot.get('type')
    current_round = CONTEXT.get('round', 0)
    balance = CONTEXT.get('init_balance', 0)

    if bot_type == 'FACTORY':
        action = handle_factory_action(bot, current_round, balance)
    elif bot_type == 'ENGINEER_BOT':
        action = handle_engineer_action(bot, balance)
    else:
        action = {"type": "NONE", "params": {}}

    return jsonify(action), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

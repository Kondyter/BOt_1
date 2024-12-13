import random
from typing import Tuple, Dict, Any

from flask import Flask, Response, request, jsonify

app = Flask(__name__)

DB: Dict[int, Any] = {}

CONTEXT: Dict[str, Any] = {
    'map': None,
    'size': None,
    'agent_id': 0,
    'count_bot': 0,
    'warehouse': {
         'WINDMILL': 0,
         'SOLAR_PANELS': 0,
         'GEOTHERMAL': 0,
         'DAM': 0,},
    'current_round' : 0,
    'balance' : 0,
    'round_treker':0

}

Rum: Dict[str, int] = {
        'round': 0,
        'balance': 0
}

bot_type = None
# Константи

DIRECTIONS = [[-1, 0], [0, 1], [1, 0], [0, -1]]
StrResponse = Tuple[str, int]

@app.get('/health')
def health() -> Response:
    return Response(status=200)


@app.route('/init', methods=['POST'])
def init() -> Response:
    
    size = request.json['map_size']
    CONTEXT['map'] = [[None] * size for _ in range(size)]
    CONTEXT['size'] = size

    global DB
    DB = {}
    return Response(status=200)


@app.route('/round', methods=['POST'])
def round() -> Response:
    round_data = request.json
    Rum['round'] = round_data['round']  # Оновлюємо номер раунду
    Rum['balance'] = round_data['balance']  # Оновлюємо баланс
    return Response(status=200)


@app.post('/agent/<int:bot_id>')
def create_bot(bot_id: int) -> Response:
    DB[bot_id] = request.json

    return Response(status=200)


@app.get('/agent/<int:bot_id>/action')
def get_bot_action(bot_id: int) -> Tuple[dict, int]:
    bot = DB.get(bot_id)
    # if not bot:
    #     return jsonify({"error": "Бот не знайдений"}), 404

    visible_map = CONTEXT['map']
    # if not visible_map:
    #     return jsonify({"error": "Карта не ініціалізована"}), 400

    terrain_type = find_bot_location(bot_id, visible_map)
    # if not terrain_type:
    #     return jsonify({"error": "Неможливо визначити тип території"}), 400

    current_round = Rum['round']
    balance = Rum['balance']


    if bot['type'] == 'FACTORY':
        if current_round == 0:
            return {'type': 'BUILD_BOT', 'params': {'d_loc': [random.randint(-1, 1), random.randint(-1, 1)]}}
        elif current_round == 1:
            return {'type': 'ASSEMBLE_POWER_PLANT', 'params': {'power_type': 'WINDMILL'}}
        elif current_round in [3, 4, 10, 17, 21, 28, 35, 40, 43, 48, 55, 58, 65, 80, 95, 100, 110, 120, 130]:
            return {'type': 'BUILD_BOT', 'params': {'d_loc': [random.randint(-1, 1), random.randint(-1, 1)]}}
        elif current_round <= 90:
            return {'type': 'ASSEMBLE_POWER_PLANT', 'params': {'power_type': 'WINDMILL'}}
        elif terrain_type == 'OCEAN':
            return {'type': 'ASSEMBLE_POWER_PLANT', 'params': {'power_type': 'WINDMILL'}}
        elif terrain_type == 'DESERT':
            return {'type': 'ASSEMBLE_POWER_PLANT', 'params': {'power_type': 'SOLAR_PANELS'}}
        elif terrain_type == 'MOUNTAIN':
            return {'type': 'ASSEMBLE_POWER_PLANT', 'params': {'power_type': 'GEOTHERMAL'}}
        elif terrain_type == 'RIVER':
            return {'type': 'ASSEMBLE_POWER_PLANT', 'params': {'power_type': 'DAM'}}

    elif bot['type'] == 'ENGINEER_BOT':
        if current_round < 95:
            action = random.choice([
                {'type': 'DEPLOY', 'params': {'power_type': 'WINDMILL', 'd_loc': [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])] }},
                {'type': 'MOVE', 'params': {'d_loc': [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])] }}
            ])
        elif current_round >= 100 and current_round % 10 == 0:  # Кожен 10-й раунд після 130
            return {'type': 'EXPLORE', 'params': {}}
        elif current_round >= 100 and terrain_type in ['OCEAN', 'PLAINS']:
            return {'type': 'DEPLOY', 'params': {'power_type': 'WINDMILL', 'd_loc': [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])]}}
        elif current_round >= 100 and terrain_type == 'DESERT':
            return {'type': 'DEPLOY', 'params': {'power_type': 'SOLAR_PANELS', 'd_loc': [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])]}}
        elif current_round >= 100 and terrain_type == 'RIVER':
            return {'type': 'DEPLOY', 'params': {'power_type': 'DAM', 'd_loc': [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])]}}
        elif current_round >= 100 and terrain_type == 'MOUNTAIN':
            return {'type': 'DEPLOY', 'params': {'power_type': 'GEOTHERMAL', 'd_loc': [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])]}}
        else:
            return {'type': 'MOVE', 'params': {'d_loc': [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])] }}

    return jsonify(action), 200


@app.route('/agent/<int:bot_id>', methods=['POST', 'PATCH', 'DELETE'])
def update_agent(bot_id: int) -> StrResponse:
    if request.method == 'POST':
        DB[bot_id] = request.json
    elif request.method == 'PATCH':
        DB[bot_id].update(request.json)
    elif request.method == 'DELETE':
        if bot_id in DB:
            del DB[bot_id]
    return '', 200


# Функція для отримання типу території
def get_terrain(x: int, y: int) -> dict:
    if CONTEXT['map'] and 0 <= x < CONTEXT['size'] and 0 <= y < CONTEXT['size']:
        return CONTEXT['map'][x][y] or {}
    return {}


def find_bot_location(bot_id: int, visible_map: list) -> str:

    for x, row in enumerate(visible_map):
        for y, cell in enumerate(row):
            if cell and cell.get("agent") and cell["agent"].get("id") == bot_id:
                return cell["type"]
    return None



@app.route('/agent/<int:bot_id>/wiev', methods=['POST']) # Переписав структуру
def explore(bot_id: int) -> Response:
    nem_map = request.json['map']
    if CONTEXT['map']:
        for x in range(CONTEXT['size']):
            for y in range(CONTEXT['size']):
                CONTEXT['map'][x][y] = nem_map[x][y] or CONTEXT['map'][x][y]
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

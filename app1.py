import random
from flask import Flask, request, jsonify
from typing import Tuple

app = Flask(__name__)

DB = {}

CONTEXT = {
    'round': 0,
    'map': None,
    'size': None,
    'factory_warehouse': {},
    'energy_balance': 0  # Додаємо початковий баланс енергії
}


StrResponse = Tuple[str, int]


@app.route('/health')
def health() -> StrResponse:
    return '', 200


@app.route('/init', methods=['POST'])
def init() -> StrResponse:
    size = request.json['map_size']
    CONTEXT['map'] = [[None] * size for _ in range(size)]
    CONTEXT['size'] = size

    global DB
    DB = {}

    # Склад з генерацією
    CONTEXT['factory_warehouse'] = {}

    return '', 200


@app.route('/round', methods=['POST'])
def round_route() -> StrResponse:
    CONTEXT['round'] = request.json['round']
    return '', 200


# Agents API

@app.route('/agent/<int:agent_id>/action', methods=['POST'])
def get_action(agent_id: int):
    agent = DB.get(agent_id)
    if agent is None:
        return jsonify({'error': 'Agent not found'}), 404

    x, y = agent['location']
    vision_radius = 5

    # Досліджуємо карту
    visible_area = {
        (x + dx, y + dy): CONTEXT['map'][x + dx][y + dy]
        for dx in range(-vision_radius, vision_radius + 1)
        for dy in range(-vision_radius, vision_radius + 1)
        if 0 <= x + dx < CONTEXT['size'] and 0 <= y + dy < CONTEXT['size']
    }

    # Логіка для фабрики
    if agent['type'] == 'FACTORY':
        # Підраховуємо кількість вітряків та сонячних станцій на складі
        warehouse = CONTEXT['factory_warehouse'].get(agent_id, {'WINDMILL': 0, 'SOLAR_PANELS': 0})

        # Якщо баланс менше 100 енергії і є встановлені джерела генерації
        if CONTEXT['energy_balance'] < 200 and (warehouse['WINDMILL'] > 0 or warehouse['SOLAR_PANELS'] > 0):
            # Якщо баланс низький, накопичуємо енергію та розвідуємо територію
            return jsonify({
                'type': 'MOVE',
                'params': {
                    'd_loc': (random.randint(-1, 1), random.randint(-1, 1))
                }
            })

        # Для перших 12 раундів не накопичуємо ресурси, а будуємо вітряки та сонячні панелі на океані та пустелі
        if CONTEXT['round'] <= 12:
            # Пошук океану для вітряків
            for (nx, ny), terrain in visible_area.items():
                if terrain and terrain['type'] == 'OCEAN' and abs(nx - x) + abs(ny - y) == 1:
                    return jsonify({
                        'type': 'DEPLOY',
                        'params': {
                            'power_type': 'WINDMILL',
                            'd_loc': [nx - x, ny - y]
                        }
                    })
            
            # Пошук пустелі для сонячних панелей
            for (nx, ny), terrain in visible_area.items():
                if terrain and terrain['type'] == 'DESERT' and abs(nx - x) + abs(ny - y) == 1:
                    return jsonify({
                        'type': 'DEPLOY',
                        'params': {
                            'power_type': 'SOLAR_PANELS',
                            'd_loc': [nx - x, ny - y]
                        }
                    })

        # Підраховуємо кількість вітряків та сонячних станцій 
        if warehouse['WINDMILL'] < 1:#ВИДАЛИТИ ПЕРВІРКУ < 1
            return jsonify({
                'type': 'ASSEMBLE_POWER_PLANT',
                'params': {
                    'power_type': 'WINDMILL'
                }
            })

        if warehouse['SOLAR_PANELS'] < 1:#ВИДАЛИТИ ПЕРВІРКУ < 1
            return jsonify({
                'type': 'ASSEMBLE_POWER_PLANT',
                'params': {
                    'power_type': 'SOLAR_PANELS'
                }
            })

        # Замовлення геотермальної станції або дамби, коли є відповідна локація
        if any(terrain == 'MOUNTAINS' for (nx, ny), terrain in visible_area.items()):
            return jsonify({
                'type': 'ASSEMBLE_POWER_PLANT',
                'params': {
                    'power_type': 'GEOTHERMAL'
                }
            })
        
        if any(terrain == 'RIVER' for (nx, ny), terrain in visible_area.items()):
            return jsonify({
                'type': 'ASSEMBLE_POWER_PLANT',
                'params': {
                    'power_type': 'DAM'
                }
            })

        return jsonify({'type': 'NONE'})

    # Логіка для інженера
    if agent['type'] == 'ENGINEER_BOT':
        # Перевіряємо стратегічні об'єкти
        for (nx, ny), obj in visible_area.items():
            if obj and obj['type'] in ['DAM', 'GEOTHERMAL'] and obj.get('owner') != agent['owner']:
                if abs(nx - x) + abs(ny - y) == 1:
                    return jsonify({'type': 'CAPTURE', 'params': {'target': [nx, ny]}})
                else:
                    return jsonify({'type': 'MOVE', 'params': {'d_loc': [nx - x, ny - y]}})

        # Якщо знаходимо річку, будуємо дамбу
        if CONTEXT['map'][x][y] == 'RIVER':
            return jsonify({'type': 'BUILD', 'params': {'structure': 'DAM'}})

        # Пошук океану, гір, пустелі
        terrain_priority = ['OCEAN', 'MOUNTAINS', 'DESERT']
        for priority_terrain in terrain_priority:
            for (nx, ny), terrain in visible_area.items():
                if terrain and terrain['type'] == priority_terrain:
                    if abs(nx - x) + abs(ny - y) == 1:
                        return jsonify({
                            'type': 'DEPLOY',
                            'params': {
                                'power_type': terrain_to_structure(priority_terrain),
                                'd_loc': [nx - x, ny - y]
                            }
                        })
                    else:
                        return jsonify({'type': 'MOVE', 'params': {'d_loc': [nx - x, ny - y]}})

        # Якщо все інше виконано, досліджуємо карту
        return jsonify({
            'type': 'MOVE',
            'params': {
                'd_loc': (random.randint(-1, 1), random.randint(-1, 1))
            }
        })

    return jsonify({'type': 'NONE'})


@app.route('/agent/<int:agent_id>', methods=['DELETE', 'POST', 'PATCH'])
def update_agent(agent_id: int) -> StrResponse:
    if request.method == 'POST':
        DB[agent_id] = request.json
    elif request.method == 'PATCH':
        if agent_id in DB:
            DB[agent_id].update(request.json)
        else:
            return jsonify({'error': 'Agent not found'}), 404
    elif request.method == 'DELETE': # Можливо зайвий блок
        DB.pop(agent_id, None)

    return '', 200


@app.route('/agent/<int:agent_id>/view', methods=['POST'])
def explore(agent_id: int) -> StrResponse:
    new_map = request.json['map']
    if len(new_map) != CONTEXT['size']:
        return jsonify({'error': 'Map size mismatch'}), 400
    for x in range(CONTEXT['size']):
        for y in range(CONTEXT['size']):
            CONTEXT['map'][x][y] = new_map[x][y] or CONTEXT['map'][x][y]

    return '', 200


def terrain_to_structure(terrain_type: str) -> str:
    
    return {
        'OCEAN': 'WINDMILL',
        'MOUNTAINS': 'GEOTHERMAL',
        'DESERT': 'SOLAR_PANELS',
        'RIVER': 'DAM',
        'PLAINS': 'WINDMILL'
    }.get(terrain_type)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
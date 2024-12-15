import random
from flask import Flask, request, jsonify
from typing import Tuple

app = Flask(__name__)

DB = {}

CONTEXT = {
    'round': 0,
    'map': None,
    'size': None,
}

# Bots API
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

    return '', 200


@app.route('/round', methods=['POST'])
def round_route() -> StrResponse:
    CONTEXT['round'] = request.json['round']
    return '', 200


# Agents API


@app.route('/agent/<int:agent_id>/action', methods=['GET'])
def get_action(agent_id: int):
    agent = DB.get(agent_id)
    if agent is None:
        return jsonify({'error': 'Agent not found'}), 404

    if agent['type'] == 'FACTORY':
        if sum(1 for agent in DB.values() if agent['type'] == 'ENGINEER_BOT') < 2:
            return jsonify({
                'type': 'BUILD_BOT',
                'params': {
                    'd_loc': random.choice([[-1, 1], [0, 1], [1, 0], [0, -1]])
                }
            })
        elif sum(agent['warehouse'].values()) < 1:
            return jsonify({
                'type': 'ASSEMBLE_POWER_PLANT',
                'params': {
                    'power_type': 'WINDMILL'
                }
            })
        else:
            return jsonify({'type': 'NONE'})

    if agent['type'] == 'ENGINEER_BOT':
        x, y = agent['location']
        if CONTEXT['map'][x][y] is None:
            return jsonify({
                'type': "MOVE",
                "params": {
                            "d_loc": random.choice([[-1, 1], [0, 1], [1, 0], [0, -1]])
                            }
            })
        elif CONTEXT['map'][x][y]['type'] == 'OCEAN':
            return jsonify({
                'type': 'DEPLOY',
                'params': {
                    'power_type': 'WINDMILL',
                    'd_loc': random.choice([[-1, 1], [0, 1], [1, 0], [0, -1]])
                }
            })
        elif CONTEXT['map'][x][y]['type'] == 'PLAINS' and random.random() < 0.1:
            return jsonify({
                'type': 'DEPLOY',
                'params': {
                    'power_type': 'WINDMILL',
                    'd_loc': random.choice([[-1, 1], [0, 1], [1, 0], [0, -1]])
                }
            })
        else:
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
    elif request.method == 'DELETE':
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
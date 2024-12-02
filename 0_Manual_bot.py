
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
#    'location': [1, 0],
    'agent_id': 0
}


# Objects:
### OCEAN
Wind = {
    'type': 'DEPLOY',
    'params': {
        'power_type': 'WINDMILL',
        'd_loc': random.choice([[-1, 0], [0, 1], [1, 0], [0, -1]])
    }
}
### DESERT
Solar = {
    'type': 'DEPLOY',
    'params': {
        'power_type': 'SOLAR_PANELS',
        'd_loc': random.choice([[-1, 0], [0, 1], [1, 0], [0, -1]])
    }
}

### MOUNTAIN
GEO = {
    'type': 'DEPLOY',
    'params': {
        'power_type': 'GEOTHERMAL',
        'd_loc': random.choice([[-1, 0], [0, 1], [1, 0], [0, -1]])
    }
}


### RIVER
DAMp_weis_to_die = {
    'type': 'DEPLOY',
    'params': {
        'power_type': 'DAM',
        'd_loc': random.choice([[-1, 0], [0, 1], [1, 0], [0, -1]])
    }
}
# Bot action
#x, y = agent['location']

univers_ac = {
  "type": "NONE",
  "params": {}
}

bot_Building = {
  "type": "DEPLOY",
  "params": {
    "power_type": "WINDMILL",
    "d_loc": random.choice([[-1, 0], [0, 1], [1, 0], [0, -1]])
  }
}

bot_Move = {
  "type": "MOVE",
  "params": {
    "d_loc": random.choice([[-1, 0], [0, 1], [1, 0], [0, -1]])
  }
}

bot_reconfig = {
  "type": "RECONFIGURE",
  "params": {
    "d_loc": [-1, 1]
  }
}

bot_die = {
  "type": "NONE",
  "params": {}
}

bot_exp = {
  "type": "EXPLORE",
  "params": {}
}

# Factory Action

Fac_bot = {
  "type": "BUILD_BOT",
  "params": {
    "d_loc": [random.randint(-1, 1), random.randint(-1, 1)]
  }
}

Fac_Ass_Sol = {
  "type": "ASSEMBLE_POWER_PLANT",
  "params": {
    "power_type": 'SOLAR_PANELS'
  }
}

Fac_Ass_Wind = {
  "type": "ASSEMBLE_POWER_PLANT",
  "params": {
    "power_type": 'WINDMILL'
  }
}


def terrain_to_structure(terrain_type: str, tp: str) -> str:
    
    return {
        'OCEAN': 'WINDMILL',
        'MOUNTAINS': 'GEOTHERMAL',
        'DESERT': 'SOLAR_PANELS',
        'RIVER': 'DAM',
        'PLAINS': 'WINDMILL'
    }.get(terrain_type, tp)



balance = CONTEXT['init_balance']
###

@app.get('/health')
def health() -> Response:
    return Response(status=200)


@app.route('/init', methods=['POST'])
def init() -> Response:
    size = request.json['map_size']
    CONTEXT['map'] = [[None] * size for _ in range(size)]
    CONTEXT['size'] = size


@app.post('/round')
def update_round() -> Response:
    CONTEXT['round'] = request.json['round']
    return '', 200


@app.post('/agent/<int:bot_id>')
def create_bot(bot_id: int) -> Response:
    DB[bot_id] = request.json

    return Response(status=200)


@app.get('/agent/<int:bot_id>/action')
def get_bot_action(bot_id: int) -> Tuple[dict, int]:
    bot = DB.get(bot_id)
    if not bot:
        return {"error": "Bot not found"}, 404
    
    action = univers_ac

    bot_type = bot.get('type')
    current_round = CONTEXT.get('round', 0)
    balance = CONTEXT.get('init_balance', 0)

    if bot_type == 'FACTORY' and current_round == 1:
        action = Fac_bot
    elif bot_type == 'FACTORY' and current_round == 2:
        action = Fac_Ass_Wind
    elif bot_type == 'FACTORY' and current_round > 5:
        if balance >= 150:
            action = Fac_Ass_Wind
    elif bot_type == 'FACTORY' and current_round >= 12 and current_round <= 15:
        if balance >= 150:
            action = Fac_bot   
    elif bot_type == 'ENGINEER_BOT' and current_round <= 3:
        action = bot_Building
    elif bot_type == 'ENGINEER_BOT' and current_round > 5:
        if balance >= 50:
            action = bot_Building
        else:
            action = bot_Move

    return action, 200

### Для оптимізації
def tera(ter: str):
    agent = DB['agent_id']
    if agent['type'] == 'ENGINEER_BOT':
        x, y = agent['location']
        if CONTEXT['map'][x][y]['type'] == 'OCEAN':
            return 'WINDMILL'
        elif CONTEXT['map'][x][y]['type'] == 'DESERT':
            return 'SOLAR_PANELS'
        elif CONTEXT['map'][x][y]['type'] == 'MOUNTAIN':
            return 'GEOTHERMAL'
        elif CONTEXT['map'][x][y]['type'] == 'RIVER':
            return 'DAM'
        elif CONTEXT['map'][x][y]['type'] == 'PLAINS':
            return 'WINDMILL'
        else:
            None


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


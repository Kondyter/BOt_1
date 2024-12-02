import random
from typing import Tuple, Dict, Any

from flask import Flask, Response, request

app = Flask(__name__)

BOTS_DB: Dict[int, Any] = {}


@app.get('/health')
def health() -> Response:
    return Response(status=200)


@app.post('/agent/<int:bot_id>')
def create_bot(bot_id: int) -> Response:
    BOTS_DB[bot_id] = request.json

    return Response(status=200)


@app.get('/agent/<int:bot_id>/action')
def get_bot_action(bot_id: int) -> Tuple[dict, int]:
    bot = BOTS_DB[bot_id]

    if bot['type'] == 'FACTORY':
        action = random.choice([
            {
                'type': 'ASSEMBLE_POWER_PLANT',
                'params': {
                    'power_type': 'WINDMILL'
                }
            },
            {
                'type': 'BUILD_BOT',
                'params': {
                    'd_loc': [random.randint(-1, 1), random.randint(-1, 1)]
                }
            }
        ])
    elif bot['type'] == 'ENGINEER_BOT':
        action = random.choice([
            {
                'type': 'MOVE',
                'params': {
                    'd_loc': [random.randint(-1, 1), random.randint(-1, 1)]
                }
            },
            {
                'type': 'DEPLOY',
                'params': {
                    "power_type": "WINDMILL",
                    'd_loc': [random.randint(-1, 1), random.randint(-1, 1)]
                }
            }
        ])
    else:
        action = {
            'type': 'NONE',
            'params': {}
        }

    return action, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
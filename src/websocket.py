import asyncio
import functools
import websockets
import json
import threading

_loop = asyncio.new_event_loop()
_thread = threading.Thread(target=_loop.run_forever)


def post_event(websocket, event: dict):
    print(f'Event: {event}')
    if not _thread.is_alive():
        _thread.start()
    future = asyncio.run_coroutine_threadsafe(
        websocket.send(json.dumps(event)), _loop)
    return future.result()

async def status_handler(af_timer, websocket):
    api_mappings = af_timer.generate_api_mappings()
    handler = functools.partial(post_event, websocket)
    af_timer.add_event_handler(handler)

    async for data in websocket:
        message = json.loads(data)
        request = message.get('request', '')
        response = {}

        if request == 'get_tones':
            response = {
                'tones': list(api_mappings['tone'].keys()),
            }
            await websocket.send(json.dumps(response))
        elif request == 'turn_on':
            duration = message.get('duration', None)
            api_mappings['on'](duration)
        elif request == 'turn_off':
            api_mappings['off']()
        elif request == 'set_tone':
            tone = message.get('tone', None)
            duration = message.get('duration', None)
            if tone not in api_mappings['tone']:
                await websocket.send(
                        json.dumps({'error': f'Invalid tone: {tone}'}))
            api_mappings['tone'][tone](duration)

    af_timer.remove_event_handler(handler)


async def run_websocket(af_timer):
    async with websockets.serve(
            functools.partial(status_handler, af_timer),
            '0.0.0.0', 12346):
        print('WebSocket server started on 0.0.0.0:12346')
        await asyncio.Future()

from aiohttp import web
import socketio

from main import log, group_call, state, app, get_id, id_to_name
from controller import Commands


commands = Commands(client=None)


socket = socketio.AsyncServer(logger=False, cors_allowed_origins="*")
web_app = web.Application()
socket.attach(web_app)


@group_call.on_network_status_changed
async def network_changed_handler(_, is_connected):
    log.debug("Send joinned signal")
    await socket.emit("joinned", is_connected)


@state.on_changed(["member_io"])
async def member_io_handler(client, peer, enter, changed):
    log.debug("Send member_io signal")
    user = (await id_to_name(client, [get_id(peer)]))[0]
    await socket.emit("member_io", {
        "name": user,
        "enter": enter
    })


@state.on_changed(["raise_hand_rating"])
async def raise_hand_handler(client, peer, old, new, changed):
    log.debug("Send raise_hand signal")
    user = (await id_to_name(client, [get_id(peer)]))[0]
    await socket.emit("raise_hand", {
        "name": user,
        "raise": new is not None
    })


@state.on_changed(["muted"])
async def mute_handler(client, peer, old, new, changed):
    log.debug("Send mute signal")
    user = (await id_to_name(client, [get_id(peer)]))[0]
    await socket.emit("muted", {
        "name": user,
        "muted": new
    })


@socket.on("join")
async def join_handler(sid, data):
    await commands.command_join(data)

@socket.on("mute")
async def mute_handler(sid, data):
    await commands.command_mute(data)


def main():
    with app:
        commands.client = app
        web.run_app(web_app)


if __name__ == '__main__':
    main()

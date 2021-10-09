from aiohttp import web
import socketio

from main import log, group_call, state, app


socket = socketio.AsyncServer(logger=False, cors_allowed_origins="*")
web_app = web.Application()
socket.attach(web_app)


@group_call.on_network_status_changed
async def network_changed_handler(_, is_connected):
    log.debug("Send joinned signal")
    await socket.emit("joinned", is_connected)


@state.on_changed(["member_io"])
async def member_io_handler(client, peer, enter, changed):
    log.info("Send member_io signal")
    user = await client.get_users(peer.user_id)
    await socket.emit("member_io", {
        "username": user.first_name,
        "enter": enter
    })


@socket.on("join")
async def join_handler(sid, data):
    state.chat_id = data
    await group_call.start(state.chat_id)


def main():
    with app:
        web.run_app(web_app)


if __name__ == '__main__':
    main()

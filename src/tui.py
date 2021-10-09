from rich.align import Align
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel

from textual import events
from textual.app import App
from textual.layouts.grid import GridLayout
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Header, Footer, Placeholder, ScrollView

from main import log, group_call, state, app


class Mic(Widget):
    def render(self) -> RenderableType:
        return Panel(
            Align.center("Mic", vertical="middle"),
            style="green"
        )


class TuiApp(App):

    members = Reactive([])

    async def on_load(self, event: events.Load) -> None:
        await self.bind("ctrl+a", "quit", "Quit")
        await self.bind("ctrl+q", "quit", "Quit")

        state.on_changed(["member_io"])(self.update_user)

    async def update_user(self, client, peer, enter, changed):
        user = await client.get_users(peer.user_id)

        if enter:
            self.members.append(user.username)
        else:
            self.members.remove(user.username)

    async def watch_members(self, members):
        self.body.update(Markdown("\n".join(members), hyperlinks=True))

    async def on_mount(self, event: events.Mount) -> None:
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")
        await self.view.dock(Placeholder(), edge="left", size=30, name="sidebar")

        self.body = ScrollView(gutter=1)

        # Dock the body in the remaining space
        await self.view.dock(self.body, edge="right")


if __name__ == "__main__":
    with app:
        TuiApp.run(title="Telegroup_call", log="textual.log")

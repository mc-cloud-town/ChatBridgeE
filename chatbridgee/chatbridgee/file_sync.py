from pathlib import Path

from mcdreforged.api.all import CommandSource, Literal, RColor, GreedyText

from .plugin import META, BasePlugin, tr


def display_help(source: CommandSource):
    source.reply(tr("file_help_message", version=META.version, prefix="!!cbe"))


class FileSyncPlugin(BasePlugin):
    def setup(self) -> None:
        if not self.config.file_sync_enabled:
            return

        self.sio.on("file_sync", self.on_file_sync)
        self.server.register_help_message(
            self.config.file_sync_command_prefix,
            tr("file_help_summary"),
        )
        self.server.register_command(
            Literal(self.config.file_sync_command_prefix)
            .runs(display_help)
            .then(
                Literal("sync")
                .runs(self.on_command_send)
                .then(GreedyText("cmt").runs(self.on_command_send))
            )
        )

    def on_file_sync(
        self,
        server_name: str,
        root: bool,
        file_path: str,
        data: bytes,
    ) -> None:
        self.from_server(
            server_name,
            f"Files are synchronizing... [檔案同步中...] ({file_path})",
            color=RColor.yellow,
        )

        path = (Path() if root else Path(self.config.file_sync_path)) / file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(data)

        self.from_server(
            server_name,
            f"Files are synchronized. [檔案同步完成] ({file_path})",
            color=RColor.yellow,
        )

    def on_command_send(self, source: CommandSource = None, ctx: dict = {}) -> None:
        config = self.config
        if (filename := str(ctx.get("filename", None))) is None:
            self.say(tr("no_args").format(arg="filename"), color=RColor.red)
            return

        path = Path(config.file_sync_path) / f"{filename}{config.file_sync_extension}"
        if not path.is_file():
            self.say("檔案未找到", color=RColor.red)
            return

        with Path(path).open("rb") as f:
            self.sio.emit("file_sync", path, f.read())

        source.reply("檔案傳送完成")

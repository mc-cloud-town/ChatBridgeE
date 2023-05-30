from pathlib import Path

from mcdreforged.api.all import CommandSource, GreedyText, Literal, RColor, RText

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
                .then(GreedyText("filename").runs(self.on_command_send))
            )
            .then(
                Literal("list")
                .runs(self.on_command_list)
                .then(GreedyText("match").runs(self.on_command_list))
            )
        )

    def on_file_sync(
        self,
        server_name: str,
        root: bool,
        file_path: str,
        data: bytes,
    ) -> None:
        if not self.config.file_sync_enabled:
            print("chatbridgee 收到檔案同步請求，但檔案同步功能未啟用")
            return

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
            source.reply(RText(tr("no_args").format(arg="filename"), color=RColor.red))
            return

        path = Path(config.file_sync_path) / f"{filename}{config.file_sync_extension}"
        if not path.is_file():
            source.reply(RText("檔案未找到", color=RColor.red))
            return

        with Path(path).open("rb") as f:
            self.sio.emit("file_sync", path, f.read())

        source.reply("檔案傳送完成")

    def on_command_list(self, source: CommandSource = None, ctx: dict = {}) -> None:
        config = self.config
        path = Path(config.file_sync_path)
        if not path.is_dir():
            source.reply(
                RText(
                    "The archive directory was not found - [檔案目錄未找到]",
                    color=RColor.red,
                )
            )
            return

        files = set(
            str(f.relative_to(path)).removesuffix(config.file_sync_extension)
            for f in path.rglob(f"*{config.file_sync_extension}")
        )

        if not files:
            source.reply(
                RText(
                    "There are no archives in the archive directory - [檔案目錄中沒有檔案]",
                    color=RColor.red,
                )
            )
            return

        source.reply(
            "A list of files - [檔案列表]: \n"
            + "\n".join([f"{i+1}. {file}" for i, file in enumerate(files)])
        )

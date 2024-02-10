from pathlib import Path
from typing import NamedTuple

from mcdreforged.api.all import CommandSource, GreedyText, Literal, RColor, RText, RTextList, RAction

from .plugin import META, BasePlugin, tr
from .utils import FileEncode, format_size_number

PER_PAGE_SIZE = 10


def display_help(prefix: str, source: CommandSource):
    source.reply(tr("file_help_message", version=META.version, prefix=prefix))


class FileSyncPlugin(BasePlugin):
    def setup(self) -> None:
        if not self.config.file_sync_enabled:
            return

        self.log.info(f"file sync path: {Path(self.config.file_sync_path).absolute()}")
        self.sio.on("file_sync", self.on_file_sync)
        self.server.register_help_message(
            self.config.file_sync_command_prefix,
            tr("file_help_summary"),
        )
        self.server.register_command(
            Literal(self.config.file_sync_command_prefix)
            .runs(lambda x: display_help(self.config.file_sync_command_prefix, x))
            .then(
                Literal("sync")
                .runs(self.on_command_send)
                .then(GreedyText("filename").runs(self.on_command_send))
            )
            .then(
                Literal("list")
                .runs(self.on_command_list)
                .then(GreedyText("index").runs(self.on_command_list))
            )
        )

    def on_file_sync(self, raw_data: bytes) -> None:
        data = FileEncode.decode(raw_data)
        root = False  # TODO add root option from flag
        file_path, server_name = data.path, data.server_name

        if not self.config.file_sync_enabled:
            self.log.info("chatbridgee 收到檔案同步請求，但檔案同步功能未啟用")
            return

        path = (Path() if root else Path(self.config.file_sync_path)) / file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(data.data)

        self.from_server(
            server_name,
            f"Files are synchronized. [檔案同步完成] ({file_path})",
            color=RColor.gold,
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

        self.sio.emit("file_sync", FileEncode(path, path.read_bytes()).encode())

        source.reply("檔案傳送完成")

    class FileInfo(NamedTuple):
        name: str
        size: int

        @classmethod
        def from_path(cls, path: Path, file_sync_extension: str) -> "FileSyncPlugin.FileInfo":
            return cls(
                path.relative_to(path.parent).as_posix().removesuffix(file_sync_extension),
                path.stat().st_size,
            )

    def get_dir_files(self, path: Path) -> list[FileInfo]:
        return [
            self.FileInfo.from_path(file_path, self.config.file_sync_extension)
            for file_path in path.rglob(f"*{self.config.file_sync_extension}")
        ]

    def on_command_list(self, source: CommandSource = None, ctx: dict = {}) -> None:
        config = self.config
        path, index = Path(config.file_sync_path), ctx.get("index", 1)
        if not path.is_dir():
            err_msg = RText(
                "The archive directory was not found - [檔案目錄未找到]",
                color=RColor.red,
            )
            source.reply(err_msg)
            return

        try:
            index = int(index)
            if index < 1:
                raise ValueError
        except ValueError:
            err_msg = RText(
                "The index must be an integer - [索引必須為正整數]",
                color=RColor.red,
            )
            source.reply(err_msg)
            return

        files = self.get_dir_files(path)
        if not files:
            err_msg = RText(
                "There is no such archive in the archive catalog - [檔案目錄中沒有這樣的檔案]",
                color=RColor.red,
            )
            source.reply(err_msg)
            return

        files_len = len(files)
        start = (index - 1) * PER_PAGE_SIZE
        if files_len < start:
            err_msg = RText(
                "The index is out of range - [索引超出範圍]",
                color=RColor.red,
            )
            source.reply(err_msg)
            return
        end = start + PER_PAGE_SIZE

        text = RTextList(RText("A list of files - [檔案列表]: \n", color=RColor.gray))
        for i, (file_name, size) in enumerate(files[start:end]):
            component1 = RTextList(RText("- ", color=RColor.gray))
            component1.append(RText(f"[{start+i+1:02d}] ", color=RColor.gold))
            component1.append(RText(f"{file_name}\n", color=RColor.green))
            component1.c(
                RAction.suggest_command,
                f"{self.config.file_sync_command_prefix} sync {file_name}",
            )
            component1.h(RText(f"點擊傳送檔案 ({format_size_number(size)})", color=RColor.gold))
            text.append(component1)

        max_page = (files_len - 1) // PER_PAGE_SIZE + 1
        component2 = RTextList(RText("----", color=RColor.yellow))
        if index > 1:
            component3 = RTextList(RText(" <<<", color=RColor.gold))
            component3.c(
                RAction.run_command,
                f"{self.config.file_sync_command_prefix} list {index - 1}",
            )
            component3.h(RText("上一頁", color=RColor.gold))
            component2.append(component3)
        else:
            component2.append(RText("---", color=RColor.yellow))

        component2.append(RText(f" {index:02d}/{index:02d}/{max_page:02d} ", color=RColor.gold))

        if index < max_page:
            component3 = RTextList(RText(">>> ", color=RColor.gold))
            component3.c(
                RAction.run_command,
                f"{self.config.file_sync_command_prefix} list {index + 1}",
            )
            component3.h(RText("下一頁", color=RColor.gold))
            component2.append(component3)
        else:
            component2.append(RText("---", color=RColor.yellow))

        component2.append(RText("----", color=RColor.yellow))
        text.append(component2)

        source.reply(text)

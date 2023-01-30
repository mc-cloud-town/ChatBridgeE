import copy
import logging
import re
from datetime import datetime, timedelta
from logging import Formatter, Logger, LogRecord
from logging.handlers import BaseRotatingHandler
from pathlib import Path
from typing import Optional, Union

from rich.logging import RichHandler
from rich.text import Text

__all__ = ("init_logging",)

log = logging.getLogger("chat-bridgee")
StrPath = Union[Path, str]


class LogTimeRotatingFileHandler(BaseRotatingHandler):
    """
    from logging mode Modify
    """

    def __init__(
        self,
        filename: str,
        directory: Optional[StrPath] = None,
        markup: bool = False,
        expired_interval: timedelta = timedelta(days=8),
        maxBytes: int = 1e6,
        backupCount: int = 5,
        encoding: str = "utf-8",
    ) -> None:
        directory = Path(directory or Path("logs"))
        directory.mkdir(parents=True, exist_ok=True)

        filepath = directory / f"{filename}.log"

        super().__init__(
            filepath,
            mode="a",
            encoding=encoding,
            delay=False,
        )

        self.filename = filename
        self.directory = directory
        self.markup = markup
        self.interval_time = timedelta(days=1)
        self.expired_interval = expired_interval
        self.maxBytes = maxBytes
        self.backupCount = backupCount

        self.rolloverAt = self.computeRollover()

    def computeRollover(self) -> datetime:
        return datetime.today() - self.interval_time

    def format(self, record: LogRecord):
        if self.markup:
            try:
                record = copy.deepcopy(record)
                record.msg = Text.from_markup(record.msg)
            except Exception as e:  # fix: aiohttp throw errors
                log.debug(e)

        return (self.formatter or Formatter()).format(record)

    def shouldRollover(self, record: LogRecord) -> bool:
        if self.stream is None:
            self.stream = self._open()
        if self.rolloverAt >= datetime.today():
            return True

        if self.maxBytes > 0:
            self.stream.seek(0, 2)
            if self.stream.tell() + len(f"{record.msg}\n") >= self.maxBytes:
                return True

        return False

    def delete_expired_logs(self) -> None:
        file_time_re = re.compile(
            rf"{self.filename}\-"
            r"(?P<time>\d{4}\-\d{2}\-\d{2})"
            r"(\.(?P<part>\d))?\.log"
        )
        end_time = datetime.today() - self.expired_interval

        for file in self.directory.iterdir():
            if (match := file_time_re.match(file.name)) and datetime.strptime(
                match.groupdict()["time"], "%Y-%m-%d"
            ) < end_time:
                log.info(f"Deleting old log file: {file.name}")
                file.unlink(missing_ok=True)

    def get_file_name(
        self,
        filename: Optional[Union[str, object]] = None,
        *,
        base_file: bool = True,
        time: bool = True,
        time_str: Optional[str] = None,
    ) -> Path:
        filenames: list[str] = []

        if base_file:
            filenames.append(str(self.filename))
        if time and time_str is not None:
            filenames.append(
                datetime.now().strftime("%Y-%m-%d") if time_str is None else time_str
            )
        if filename:
            filenames.append(str(filename))

        return self.directory / f"{'.'.join(filenames)}.log"

    def doRollover(self) -> bool:
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.rolloverAt >= datetime.today():
            for i in range(self.backupCount, 0, -1):
                if (old_file := self.get_file_name(i, time=False)).exists():
                    old_file.rename(
                        self.get_file_name(
                            i, time_str=self.rolloverAt.strftime("%Y-%m-%d")
                        )
                    )
            self.rolloverAt = self.computeRollover()
            return self.delete_expired_logs()

        if self.backupCount > 0:
            self.get_file_name(self.backupCount, time=False).unlink(missing_ok=True)
            for i in range(self.backupCount - 1, 0, -1):
                if (old_file := self.get_file_name(i, time=False)).exists():
                    old_file.rename(self.get_file_name(i + 1, time=False))
            (base_file := self.get_file_name(time=False)).rename(
                base_file.with_suffix(".1.log")
            )

        self.stream = self._open()


def init_logging(
    level: int = logging.DEBUG,
    directory: Optional[StrPath] = None,
) -> Logger:
    warnings_logger = logging.getLogger("py.warnings")

    log.setLevel(level)
    warnings_logger.setLevel(logging.WARNING)

    file_formatter = logging.Formatter(
        "[{asctime}] [{levelname}:{name}]: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )

    file_handler = LogTimeRotatingFileHandler(
        log.name, markup=True, directory=directory
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    log.addHandler(file_handler)
    log.addHandler(
        RichHandler(
            level=logging.INFO,
            rich_tracebacks=True,
            log_time_format="[%X]",
            tracebacks_show_locals=True,
        )
    )

    return log

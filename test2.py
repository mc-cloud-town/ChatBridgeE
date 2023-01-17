from aiohttp.web_runner import GracefulExit

from server import Server, Config, init_logging

init_logging()

ser = Server()

ser.load_plugin("plugins", recursive=True)
# ser.load_plugin("plugins.test")


config = Config("config")
print(config.get("stop_plugins"))

try:
    ser.start()
except GracefulExit:
    ...

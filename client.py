from utils.client import BaseClient


client = BaseClient()


@client.on("connect")
def connect():
    client.send("test")


# asyncio.run(client.main)
client.start()

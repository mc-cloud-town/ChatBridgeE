import click

from server.core import ChatBridgeServer, Address

address = Address("localhost", 9999)


@click.command()
@click.option("--discord", default=False, is_flag=True)
def main(discord):
    if discord:
        from server.core import ChatBridgeClient

        ChatBridgeClient("test", address).run()
        return
    ChatBridgeServer("test", address).start()


if __name__ == "__main__":
    main()

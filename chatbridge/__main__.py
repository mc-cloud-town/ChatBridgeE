# from chatbridge.utils.cli.start import main

if __name__ == "__main__":
    # main()
    from chatbridge.core.server import ChatBridgeServer, Address

    ChatBridgeServer("test", Address("localhost", 9999)).start()

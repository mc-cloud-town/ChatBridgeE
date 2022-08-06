# from chatbridge.utils.cli.start import main

if __name__ == "__main__":
    # main()
    from server.core import ChatBridgeServer, Address

    ChatBridgeServer("test", Address("localhost", 9999)).start()

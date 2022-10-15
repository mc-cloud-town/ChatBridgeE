from chatbridgee.utils.client import event


# client = BaseClient()


# @client.on("connect")
# def connect():
#     client.send("test")


# # asyncio.run(client.main)
# client.start()
@event
def test():
    print("awa")


@event("awa")
def test2():
    print("awa")


test
test2

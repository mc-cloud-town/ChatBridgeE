import asyncio
from asyncio import Future


async def main():
    my_future = Future()
    print(my_future.done())  # False

    my_future.set_result("Bright")

    print(my_future.done())  # True

    print(my_future.result())


asyncio.run(main())

#! /usr/bin/env python
import pickle

import websockets

from keycumber import AddressPacket, ReturnPacket

OPENING_TEXT = """
Welcome to the Keycumber repl
Type 'help' for more information
""".strip()

HELP = """
Usage:
    <command> [<args>]

Commands:
    help:
        Print this help message
    exit:
        Exit the repl
    set <key> <value>:
        Set a key to a value
    get <key>:
        Get the value of a key
    delete <key>:
        Delete a key
""".strip()


async def main() -> None:
    print(OPENING_TEXT)
    async with websockets.connect("ws://localhost:8765") as websocket:
        while True:
            command = input("> ")

            packet = None

            if command == "help":
                print(HELP)
            elif command == "exit":
                break
            elif command.startswith("set "):
                _, key, value = command.split(" ", maxsplit=2)
                packet = AddressPacket("set", key, value)
            elif command.startswith("get "):
                _, key = command.split(" ", maxsplit=1)
                packet = AddressPacket("get", key, None)
            elif command.startswith("delete "):
                _, key = command.split(" ", maxsplit=1)
                packet = AddressPacket("delete", key, None)
            else:
                print("Unknown command\nType help for more information")

            # Send the packet
            if packet is not None:
                await websocket.send(pickle.dumps(packet))

                answer: ReturnPacket = pickle.loads(await websocket.recv())
                print(f"< {answer.status.upper()} {answer.value or ''}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

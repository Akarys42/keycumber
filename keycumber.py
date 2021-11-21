#! /usr/bin/env python
import asyncio
import dataclasses
import pickle
import sys
from typing import Optional

import websockets

WSProtocol = websockets.WebSocketServerProtocol

# Set DEBUG if the -d or --debug flag is passed to the script
DEBUG = any(arg in ("-d", "--debug") for arg in sys.argv)


@dataclasses.dataclass
class AddressPacket:
    """Single interaction from the client to the server."""

    action: str  # "get", "set" or "delete"
    key: str
    value: Optional[str]


@dataclasses.dataclass
class ReturnPacket:
    """Value or ack from the server to the client."""

    status: str  # "ok", "error" or "not_found"
    value: Optional[str]


class Keycumber:
    def __init__(self):
        self.content = {}
        self.next_id = 0

    async def start(self) -> None:
        print("Starting server on port 8765...")
        async with websockets.serve(self.handle_new_session, "localhost", 8765):
            await asyncio.Future()  # Never return

    async def handle_new_session(self, websocket: WSProtocol) -> None:
        # Assign a unique id to the client
        client_id = self.next_id
        self.next_id += 1

        print(f"New session started with client {client_id}.")

        while True:
            try:
                message = await websocket.recv()
            except websockets.ConnectionClosed:
                print(f"Session ended with client {client_id}.")
                break
            if DEBUG:
                print(f"Received: {message}")

            # Parse the message into a packet
            packet: AddressPacket = pickle.loads(
                message
            )  # ! Unpickling from an untrusted source !
            print(f"< {packet}")

            if packet.action == "get":
                # First check if the key exists
                if packet.key in self.content:
                    # If it does, send the value back
                    return_packet = ReturnPacket("ok", self.content[packet.key])
                else:
                    # If it doesn't, send an error back
                    return_packet = ReturnPacket("not_found", None)
            elif packet.action == "set":
                self.content[packet.key] = packet.value

                return_packet = ReturnPacket("ok", None)
            elif packet.action == "delete":
                if packet.key in self.content:
                    del self.content[packet.key]

                    return_packet = ReturnPacket("ok", None)
                else:
                    return_packet = ReturnPacket("not_found", None)
            else:
                # If the action is not recognized, send an error back
                return_packet = ReturnPacket("error", None)

            # Log the return packet
            print(f"> {return_packet}")

            # Serialize the packet and send it back
            await websocket.send(pickle.dumps(return_packet))

    def drop_all(self) -> None:
        # ! This is a dangerous operation !
        self.content = {}


if __name__ == "__main__":
    server = Keycumber()
    asyncio.run(server.start())

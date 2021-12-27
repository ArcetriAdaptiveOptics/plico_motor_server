import asyncio


class NewFocus8742ServerProtocol(asyncio.Protocol):

    eol_read = b"\r"
    eol_write = b"\r\n"

    def __init__(self):
        self._position = {}
        self._position[0] = 0
        self._position[1] = 0
        self._position[2] = 0
        self._position[3] = 0
        self._position[4] = 0

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self.transport.write(b'123456')

    def data_received(self, data):
        message = data.decode()[:-1]
        print('Data received: {!r}'.format(message))
        axl = 1
        axis = int(message[0:axl])
        if message[axl:] == 'TP?':
            ret_message = str(self._position[axis])
            print('Position - send: {!r}'.format(ret_message))
            self.transport.write(ret_message.encode() + self.eol_write)
        elif message[axl: axl + 2] == 'PR':
            arg = int(message[axl + 2:])
            self._position[axis] += arg
            print('set relative - got: {!r}'.format(arg))
        else:
            ret_message = message
            print('unknown - send: {!r}'.format(ret_message))
            self.transport.write(ret_message.encode() + self.eol_write)


async def main(ipaddr='localhost', port=30023):
    loop = asyncio.get_running_loop()

    server = await loop.create_server(
        lambda: NewFocus8742ServerProtocol(), ipaddr, port)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

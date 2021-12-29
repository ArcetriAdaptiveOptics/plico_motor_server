#!/usr/bin/env python
import sys
import asyncio
from plico.utils.logger import Logger
import logging


class NewFocus8742ServerProtocol(asyncio.Protocol):

    eol_read = b"\r"
    eol_write = b"\r\n"
    RUNNING_MESSAGE = "fakenewfocus8742_is_running."

    def __init__(self):
        self._logger = Logger.of('NewFocus8742ServerProtocol')
        self._logger.debug(self.RUNNING_MESSAGE)
        self._position = {}

    def _create_axis_if_needed(self, axis):
        if axis not in self._position.keys():
            self._position[axis] = 0

    def _set_position(self, axis, value):
        self._create_axis_if_needed(axis)
        self._position[axis] = value

    def _get_position(self, axis):
        self._create_axis_if_needed(axis)
        return self._position[axis]

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self._logger.notice('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()[:-1]
        for msg in message.split('\n'):
            self._handle_message(msg)

    def _handle_message(self, message):
        self._logger.notice('Data received: {!r}'.format(message))
        axl = 1
        axis = int(message[0:axl])
        if message[axl:] == 'TP?' or message[axl:] == 'PA?':
            ret_message = str(self._get_position(axis))
            self._logger.notice('Position - send: {!r}'.format(ret_message))
            self.transport.write(ret_message.encode() + self.eol_write)
        elif message[axl: axl + 2] == 'PR':
            arg = int(message[axl + 2:])
            self._set_position(axis, self._get_position(axis) + arg)
            self._logger.notice('set relative - got: {!r}'.format(arg))
        else:
            ret_message = message
            self._logger.warn('unknown - send: {!r}'.format(ret_message))
            self.transport.write(ret_message.encode() + self.eol_write)


async def main(ipaddr='localhost', port=30023):
    log_format = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    logger = Logger.of('FakeNewFocus8742')

    loop = asyncio.get_running_loop()

    server = await loop.create_server(
        lambda: NewFocus8742ServerProtocol(), ipaddr, port)

    # DONT REMOVE - USED IN INTEGRATION TEST
    logger.notice(NewFocus8742ServerProtocol.RUNNING_MESSAGE)
    sys.stdout.flush()

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

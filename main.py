#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import asyncio
import serial_asyncio
from async_serial import Output

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = serial_asyncio.create_serial_connection(loop, Output, "/dev/ttyAMA0", baudrate=9600)
    _transport, protocol = loop.run_until_complete(coro)
    tasks = [asyncio.ensure_future(Output.query_sensor_timer(_transport))]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

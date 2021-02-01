#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import asyncio
import struct
import time
import json
from config import apr_list


def get_cmd(address, cmd: list):
    addr = [address % 256 % 256, int(address / 256)]
    query_data = [0xfe, 0x0, 0x24, 0x5f]
    query_data.extend(addr)
    query_data.extend(cmd)
    query_data[1] = len(query_data) - 4
    y = 0
    for x in query_data[1:]:
        y = y ^ x
    query_data.append(y)
    return query_data


class Output(asyncio.Protocol):
    def __init__(self):
        super().__init__()
        self.transport = None
        self._last_received = 0
        self._cache = list()  # queue for send
        self._data = list()  # queue received
        self._buffer = list()

    def connection_made(self, transport):
        self.transport = transport
        print('port opened')
        transport.serial.rts = False

    def data_received(self, data):
        self._data.extend(data)
        k = 0
        for j in range(0, len(self._data) - 1):
            if j < k:
                continue
            k = j
            if self._data[j] != 0xFE:
                continue
            if len(self._data) - j >= self._data[j + 1] + 5:
                if self._data[j + 2] == 0x44 and self._data[j + 3] == 0x5F:
                    z = 0
                    for x in self._data[j + 1:j + self._data[j + 1] + 4]:
                        z = z ^ x
                    if z == self._data[j + self._data[j + 1] + 4]:
                        k = j + self._data[j + 1] + 5
                        _cmd = self._data[j:k]
                        # print('recv: ', [hex(i) for i in _cmd])
                        _addr = _cmd[4] + _cmd[5] * 256
                        if _addr in apr_list:
                            self.process_callback(_cmd)
            else:
                break
        self._data = self._data[k:]

    def connection_lost(self, exc):
        print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        # print(self.transport.get_write_buffer_size())
        pass

    def resume_writing(self):
        # print(self.transport.get_write_buffer_size())
        print('resume writing')
        pass

    @staticmethod
    async def query_sensor_timer(transport):
        cmd = [0x01, 0x03, 0x00, 0x00, 0x00, 0x06]
        while True:
            # 初始化时已获取到最新状态
            for apr in apr_list:
                transport.write(get_cmd(apr, cmd))
                await asyncio.sleep(1)
            await asyncio.sleep(5 * 60)

    @staticmethod
    def process_callback(cmd):
        dev = struct.unpack('<H', bytes(cmd[4:6]))[0]
        print([hex(i) for i in cmd])
        if cmd[6:8] != [0x03, 0x2c]:
            return
        t, rh, pm25, co2, hcho, voc = struct.unpack('>hHHHHH', bytes(cmd[8:20]))
        t = round(t / 10, 1)
        rh = round(rh / 10, 1)
        data = {
            't': str(t),
            'rh': str(rh),
            'pm2p5': str(pm25),
            'co2': str(co2),
            'hcho': str(hcho),
            'voc': str(voc),
        }
        with open('data_0201.log', 'a') as f:
            f.write(json.dumps({str(datetime.fromtimestamp(time.time())): _data}))
            f.write('\n')

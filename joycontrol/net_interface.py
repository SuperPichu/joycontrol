import inspect
import logging
import asyncio

from aioconsole import ainput
from threading import Thread
from time import sleep
from joycontrol.controller_state import ControllerState, button_push
from queue import Queue
import socket
logger = logging.getLogger(__name__)
queue = Queue(100)

# class Server(socketserver.TCPServer):
#     allow_reuse_address = True

# class Handler(socketserver.StreamRequestHandler):
#     def handle(self):
#         while True:
#             self.data = self.rfile.readline().strip()
#             queue.put(self.data.decode())
#             #self.wfile.write(self.data)

# def serverThread():
#     with Server(('0.0.0.0', 8888), Handler) as server:
#         server.serve_forever()

def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return int(rightMin + (valueScaled * rightSpan))

class NetController:

    def __init__(self, controller_state: ControllerState):
        self.controller_state = controller_state
    
    async def run(self):
        global queue
        # t = Thread(target=serverThread, daemon=True)
        # t.start()
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.setblocking(False)
        serversocket.bind(('0.0.0.0', 8888))
        serversocket.listen(5)
        while True:
            try:
                (clientsocket, address) = serversocket.accept()
                break
            except BlockingIOError:
                await asyncio.sleep(5)
                continue
        clientsocket.setblocking(False)
        while True:
            tmp = 0
            try:
                tmp = clientsocket.recv(64,socket.MSG_PEEK).decode().find('\r\n') + 2
            except BlockingIOError:
                continue
            if tmp > 0:
                cmd = clientsocket.recv(tmp).decode().replace('\r\n','')
                #print(cmd)
                #print(args)
                if (len(cmd) != 0 and cmd[0] != ' ' ):
                    print(f'Got: {cmd}')
                    cmd,*args = cmd.split(' ')
                    if cmd == 'press':
                        if args[0][0] == 'D':
                            args[0] = args[0][1:]
                        self.controller_state.button_state.set_button(args[0].lower())
                    elif  cmd == 'release':
                        if args[0][0] == 'D':
                            args[0] = args[0][1:]
                        self.controller_state.button_state.set_button(args[0].lower(),False)
                    elif cmd == 'click':
                        await button_push(self.controller_state,args[0].lower())
                    elif cmd == 'setStick':
                        stick = args[0]
                        direction = args[1]
                        if stick == 'RIGHT':
                            if direction == 'UP':
                                self.controller_state.r_stick_state.set_up()
                            elif direction == 'DOWN':
                                self.controller_state.r_stick_state.set_down()
                            elif direction == 'LEFT':
                                self.controller_state.r_stick_state.set_left()
                            elif direction == 'RIGHT':
                                self.controller_state.r_stick_state.set_right()
                            elif direction == 'ZX':
                                self.controller_state.r_stick_state.set_h(2048)
                            elif direction == 'ZY':
                                self.controller_state.r_stick_state.set_v(2048)
                        elif stick == 'LEFT':
                            if direction == 'UP':
                                self.controller_state.l_stick_state.set_up()
                            elif direction == 'DOWN':
                                self.controller_state.l_stick_state.set_down()
                            elif direction == 'LEFT':
                                self.controller_state.l_stick_state.set_left()
                            elif direction == 'RIGHT':
                                self.controller_state.l_stick_state.set_right()
                            elif direction == 'ZX':
                                self.controller_state.l_stick_state.set_h(2048)
                            elif direction == 'ZY':
                                self.controller_state.l_stick_state.set_v(2048)
                    await self.controller_state.send()
            await asyncio.sleep(1/60)
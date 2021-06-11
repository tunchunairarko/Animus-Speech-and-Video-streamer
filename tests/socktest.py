import eventlet

import socketio

import time
import random
sio = socketio.Client()
eventlet.monkey_patch()

@sio.event
def connect():
    print('connected to server')


@sio.event
def disconnect():
    print('disconnected from server') 

sio.connect('http://peppersock.isensetune.com:9543')

def main():
    if(sio.connected):
        try:
            while(True):
                sio.emit("PEPPERSONAR",random.randrange(20,30))
                time.sleep(1)
        except KeyboardInterrupt:
            sio.disconnect()
if __name__=="__main__":
    main()

import socketio
print(socketio.__version__)
sio = socketio.Client()
sio.connect('https://hwu-telepresence-room.herokuapp.com')
# if(sio.connected):
#     print("*****************YES*****************")
# else:
#     print("*****************NO*******************")

@sio.event
def connect():
    print('connected to server')
    sr = sio.sockets.adapter.rooms["9dd0ee98-d035-4e20-a95b-65c117b95a59"] 

@sio.event
def disconnect():
    print('disconnected from server')

def main():
    print("destroy")

if __name__=='__main__':
    main()   


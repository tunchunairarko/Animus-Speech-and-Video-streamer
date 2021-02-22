from flask import Flask, render_template, Response, request, abort, jsonify
import cv2
from flask_cors import CORS
import os
import animus_client as animus
import animus_utils as utils
import sys
import logging
import numpy as np
import random
import time
import threading
import socketio
stopFlag = False
from dotenv import load_dotenv
load_dotenv()

sio = socketio.Client()
sio.connect('http://localhost:5000')
if(sio.connected):
    print("*****************YES*****************")
else:
    print("*****************NO*******************")    

app = Flask (__name__)
CORS(app)

class AnimusRobot:
    def __init__(self):
        self.log = utils.create_logger("MyAnimusApp", logging.INFO)
        self.myrobot = {}
        self.videoImgSrc=''
        self.getRobot()
        self.openModalities()
        # self.getVideofeed()
        self.thread=threading.Thread(target=self.gen_frames)
        
    # def getVideofeed(self):
    #     image_list, err = self.myrobot.get_modality("vision", True)
    #     print(len(image_list))
    #     if err.success:
    #         # sio.emit('pythondata', str(image_list[0].image))                      # send to server
    #         ret, buffer = cv2.imencode('.jpg', image_list[0].image)
    #         frame = buffer.tobytes()

    #         self.videoImgSrc=b'--frame\r\n Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        # while True:
        #     image_list, err = self.myrobot.get_modality("vision", True)
        #     print(len(image_list))
        #     if err.success:
        #         # sio.emit('pythondata', str(image_list[0].image))                      # send to server
        #         ret, buffer = cv2.imencode('.jpg', image_list[0].image)
        #         frame = buffer.tobytes()

        #         self.videoImgSrc=b'--frame\r\n Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'

                
    def openModalities(self):
        open_success = self.myrobot.open_modality("vision")
        if not open_success:
            self.log.error("Could not open robot vision modality")
            # sys.exit(-1)

        open_success = self.myrobot.open_modality("motor")
        if not open_success:
            self.log.error("Could not open robot motor modality")
            # sys.exit(-1)
    def getRobot(self):
        for i in range(10):
            
            self.log.info(animus.version())
            print(animus.version())
            audio_params = utils.AudioParams(
                        Backends=["notinternal"],
                        SampleRate=16000,
                        Channels=1,
                        SizeInFrames=True,
                        TransmitRate=30
                    )

            setup_result = animus.setup(audio_params, "PythonAnimusBasics", True)
            if not setup_result.success:
                time.sleep(5)
                continue

            login_result = animus.login_user("ms414@hw.ac.uk", "C3):]RR[Rs$Y", False)
            if login_result.success:
                self.log.info("Logged in")
            else:
                time.sleep(5)
                continue

            get_robots_result = animus.get_robots(True, True, False)
            print(get_robots_result)
            if not get_robots_result.localSearchError.success:
                self.log.error(get_robots_result.localSearchError.description)

            if not get_robots_result.remoteSearchError.success:
                self.log.error(get_robots_result.remoteSearchError.description)

            if len(get_robots_result.robots) == 0:
                self.log.info("No Robots found")
                animus.close_client_interface()
                time.sleep(5)
                continue

            chosen_robot_details = get_robots_result.robots[0]

            self.myrobot = animus.Robot(chosen_robot_details)
            connected_result = self.myrobot.connect()
            if not connected_result.success:
                print("Could not connect with robot {}".format(self.myrobot.robot_details.robot_id))
                animus.close_client_interface()
                time.sleep(5)
                continue
            else:
                break

            
    def gen_frames(self):  # generate frame by frame from camera
        while True:
            image_list, err = self.myrobot.get_modality("vision", True)
            print(len(image_list))
            if err.success:
                # sio.emit('pythondata', str(image_list[0].image))                      # send to server
                ret, buffer = cv2.imencode('.jpg', image_list[0].image)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            # frame = buffer.tobytes()

            # self.videoImgSrc=b'--frame\r\n Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
            # yield(self.videoImgSrc)
                
    def closeRobot(self):
        self.myrobot.disconnect()
        animus.close_client_interface()


Robot=AnimusRobot()
@app.route('/',methods=['POST','GET'])
def index():
    """Video streaming home page."""
    if(request.method=='POST'):
        data=request.get_json()
        print(data)
        if(data['email']==os.getenv('EMAIL') and data['password']==os.getenv('PASSWORD')):
            return render_template('index.html'), 200
        else:
            abort(401, description="Unauthorized")
            # app.route('/stop')
            # return render_template('stop.html')
    else:
        # Robot.camera.release()
        # abort(401, description="Unauthorized")
        return render_template('index.html'), 200

@app.errorhandler(401)
def resource_not_found(e):
    return jsonify(error=str(e)), 401


@app.route('/stop')
def stop():
    Robot.closeRobot()
    return render_template('stop.html')

@app.route('/start')
def start():
    Robot.getRobot()
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # if(Robot.thread.is_alive()==False):
    #     Robot.thread.start()
    
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(Robot.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@sio.event
def connect():
    print('connected to server')


@sio.event
def disconnect():
    print('disconnected from server')

@sio.on('FROMNODEAPI')
def frontenddata(data):
    key=str(data)
    print(key)
    motorDict = utils.get_motor_dict()
    list_of_motions = [motorDict.copy()]
    if(key=='up'):
        motorDict["head_up_down"] = 4 * utils.HEAD_UP
        motorDict["body_forward"] = 0.0
        motorDict["body_sideways"] = 0.0
        motorDict["body_rotate"] = 0.0
        list_of_motions.append(motorDict.copy())
    elif(key=='down'):
        motorDict["head_up_down"] = 4 * utils.HEAD_DOWN
        motorDict["body_forward"] = 0.0
        motorDict["body_sideways"] = 0.0
        motorDict["body_rotate"] = 0.0
        list_of_motions.append(motorDict.copy())
    elif(key=='left'):
        motorDict["head_left_right"] = 5 * utils.HEAD_LEFT
        motorDict["body_forward"] = 0.0
        motorDict["body_sideways"] = 0.0
        motorDict["body_rotate"] = 0.0
        list_of_motions.append(motorDict.copy())
    elif(key=='right'):
        motorDict["head_left_right"] = 5 * utils.HEAD_RIGHT
        motorDict["body_forward"] = 0.0
        motorDict["body_sideways"] = 0.0
        motorDict["body_rotate"] = 0.0
        list_of_motions.append(motorDict.copy())
    for motion_counter in range(len(list_of_motions)):
        ret = Robot.myrobot.set_modality("motor", list(list_of_motions[motion_counter].values()))
    # time.sleep(2)
    
    # motorDict["head_left_right"] = var * utils.HEAD_RIGHT
        
    # list_of_motions.append(motorDict.copy())
    # for motion_counter in range(len(list_of_motions)):
    #     ret = Robot.myrobot.set_modality("motor", list(list_of_motions[motion_counter].values()))
    #     time.sleep(0.1)
    # var=var+3
    
    # motorDict = utils.get_motor_dict()
    # list_of_motions = [motorDict.copy()]
    # motorDict[key]=value
    # list_of_motions.append(motorDict.copy())
    # for motion_counter in len(range(list_of_motions)):
    #     ret = Robot.myrobot.set_modality("motor", list(list_of_motions[motion_counter].values()))

if __name__ == '__main__':
    # print(os.getenv('EMAIL'))
    app.run(debug=False,host=os.getenv('HOST'),port=os.getenv('PORT'))
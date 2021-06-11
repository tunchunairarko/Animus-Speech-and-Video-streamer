from flask import Flask, render_template, Response, request, abort, jsonify
import cv2
from flask_cors import CORS
import os
import animus_client as animus
import animus_utils as utils
import sys
import logging
import numpy as np
import datetime
import time
import threading
import socketio
import math
stopFlag = False
from dotenv import load_dotenv
load_dotenv()

sio = socketio.Client()
sio.connect('http://localhost:9000')
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
        self.utils = utils
        self.prevTime = 0
        self.prev_motor_dict = utils.get_motor_dict()
        self.head_motion_counter = {
            'head_up_down': 0,  # -head_angle_threshold,head_angle_threshold
            'head_left_right': 0,  # -head_angle_threshold,head_angle_threshold
            'head_roll': 0
        }
        self.head_angle_incrementer = 5
        self.head_angle_threshold = 90
        self.body_rotation_speed=0.5
        # self.getVideofeed()
        self.thread=threading.Thread(target=self.gen_frames)

                
    def openModalities(self):
        open_success = self.myrobot.open_modality("vision")
        if not open_success:
            self.log.error("Could not open robot vision modality")
            # sys.exit(-1)

        open_success = self.myrobot.open_modality("motor")
        if not open_success:
            self.log.error("Could not open robot motor modality")
            # sys.exit(-1)
        open_success = self.myrobot.open_modality("speech")
        if not open_success:
            self.log.error("Could not open robot speech modality")
            # sys.exit(-1)
        open_success = self.myrobot.open_modality("emotion")
        if not open_success:
            self.log.error("Could not open robot speech modality")
            # sys.exit(-1)
    def getRobot(self):
        for i in range(10):
            
            self.log.info(animus.version())
            # print(animus.version())
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
            # print(get_robots_result)
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
    
    def apply_mask(self,matrix, mask, fill_value):
        masked = np.ma.array(matrix, mask=mask, fill_value=fill_value)
        return masked.filled()

    def apply_threshold(self,matrix, low_value, high_value):
        low_mask = matrix < low_value
        matrix = self.apply_mask(matrix, low_mask, low_value)

        high_mask = matrix > high_value
        matrix = self.apply_mask(matrix, high_mask, high_value)

        return matrix

    def color_balance(self,img, percent):
        assert img.shape[2] == 3
        assert percent > 0 and percent < 100

        half_percent = percent / 200.0

        channels = cv2.split(img)

        out_channels = []
        for channel in channels:
            assert len(channel.shape) == 2
            # find the low and high precentile values (based on the input percentile)
            height, width = channel.shape
            vec_size = width * height
            flat = channel.reshape(vec_size)

            assert len(flat.shape) == 1

            flat = np.sort(flat)

            n_cols = flat.shape[0]

            low_val  = flat[math.floor(n_cols * half_percent)]
            high_val = flat[math.ceil( n_cols * (1.0 - half_percent))]

            # print "Lowval: ", low_val
            # print "Highval: ", high_val

            # saturate below the low percentile and above the high percentile
            thresholded = self.apply_threshold(channel, low_val, high_val)
            # scale the channel
            normalized = cv2.normalize(thresholded, thresholded.copy(), 0, 255, cv2.NORM_MINMAX)
            out_channels.append(normalized)

        return cv2.merge(out_channels)
            
    def gen_frames(self):  # generate frame by frame from camera
        if(self.prevTime==0):
            self.prevTime=datetime.datetime.now()
        while True:
            try:
                image_list, err = self.myrobot.get_modality("vision", True)
            except:
                continue
            # image_list, err = self.myrobot.get_modality("vision", True)
            # print(len(image_list))
            if err.success:
                # sio.emit('pythondata', str(image_list[0].image))                      # send to server
                clear_img=self.color_balance(image_list[0].image,1)
                clear_img=image_list[0].image

                ret, buffer = cv2.imencode('.jpg', clear_img)
                curTime=datetime.datetime.now()
                sio.emit("ANIMUSFPS",str(curTime-self.prevTime))
                self.prevTime=curTime
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
        # print(data)
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

def resetRobotHead():
    Robot.prev_motor_dict["head_up_down"]=0
    Robot.head_motion_counter['head_up_down']=0
    Robot.head_motion_counter['head_left_right']=0
    Robot.prev_motor_dict["head_left_right"]=0
    Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))

    # if(Robot.prev_motor_dict['head_up_down']>0):
    #     for i in range(abs(Robot.head_motion_counter['head_up_down'])):
    #         Robot.head_motion_counter['head_up_down'] = Robot.head_motion_counter['head_up_down'] - 1
    #         Robot.prev_motor_dict["head_up_down"] = Robot.head_motion_counter['head_up_down'] * Robot.utils.HEAD_UP
    #         ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))
    #         time.sleep(0.02)
    #     # Robot.prev_motor_dict['head_up_down']=0
    # elif(Robot.prev_motor_dict['head_up_down']<0):
    #     for i in range(abs(Robot.head_motion_counter['head_up_down'])):
    #         Robot.head_motion_counter['head_up_down'] = Robot.head_motion_counter['head_up_down'] + 1
    #         Robot.prev_motor_dict["head_up_down"] = Robot.head_motion_counter['head_up_down'] * Robot.utils.HEAD_UP
    #         ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))
    #         time.sleep(0.02)
    # if(Robot.prev_motor_dict['head_left_right']>0):
    #     for i in range(abs(Robot.head_motion_counter['head_left_right'])):
    #         Robot.head_motion_counter['head_left_right'] = Robot.head_motion_counter['head_left_right'] - 1
    #         Robot.prev_motor_dict["head_left_right"] = Robot.head_motion_counter['head_left_right'] * Robot.utils.HEAD_RIGHT
    #         ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))
    #         time.sleep(0.02)
    #     # Robot.prev_motor_dict['head_up_down']=0
    # elif(Robot.prev_motor_dict['head_left_right']<0):
    #     for i in range(abs(Robot.head_motion_counter['head_left_right'])):
    #         Robot.head_motion_counter['head_left_right'] = Robot.head_motion_counter['head_left_right'] + 1
    #         Robot.prev_motor_dict["head_left_right"] = Robot.head_motion_counter['head_left_right'] * Robot.utils.HEAD_RIGHT
    #         ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))
    #         time.sleep(0.02)

@sio.on('FROMNODEAPI')
def frontenddata(data):
    if not (Robot.myrobot == None):
        key = str(data)
        print(key)
        # list_of_motions=[]
        # motorDict = Robot.utils.get_motor_dict()
        # list_of_motions = [motorDict.copy()]
        if(key == 'head_up'):
            if not (Robot.head_motion_counter['head_up_down'] == Robot.head_angle_threshold):
                for i in range(Robot.head_angle_incrementer):
                    Robot.head_motion_counter['head_up_down'] = Robot.head_motion_counter['head_up_down'] + 1
                    Robot.prev_motor_dict["head_up_down"] = Robot.head_motion_counter['head_up_down'] * Robot.utils.HEAD_UP
                    ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))
                    time.sleep(0.05)
        elif(key == 'head_down'):
            if not (Robot.head_motion_counter['head_up_down'] == -1*Robot.head_angle_threshold):
                for i in range(Robot.head_angle_incrementer):
                    Robot.head_motion_counter['head_up_down'] = Robot.head_motion_counter['head_up_down'] - 1
                    Robot.prev_motor_dict["head_up_down"] = Robot.head_motion_counter['head_up_down'] * Robot.utils.HEAD_UP
                    ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))
                    time.sleep(0.05)
        
        elif(key == 'head_left'):
            if not (Robot.head_motion_counter['head_left_right'] == -1*Robot.head_angle_threshold):
                for i in range(Robot.head_angle_incrementer):
                    Robot.head_motion_counter['head_left_right'] = Robot.head_motion_counter['head_left_right'] - 1
                    Robot.prev_motor_dict["head_left_right"] = Robot.head_motion_counter['head_left_right'] * Robot.utils.HEAD_RIGHT
                    ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))
                    time.sleep(0.05)

        elif(key == 'head_right'):
            if not (Robot.head_motion_counter['head_left_right'] == Robot.head_angle_threshold):
                for i in range(Robot.head_angle_incrementer):
                    Robot.head_motion_counter['head_left_right'] = Robot.head_motion_counter['head_left_right'] + 1
                    Robot.prev_motor_dict["head_left_right"] = Robot.head_motion_counter['head_left_right'] * Robot.utils.HEAD_RIGHT
                    ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))
                    time.sleep(0.05)

        elif(key == 'rotate_left'):
            resetRobotHead()
            Robot.prev_motor_dict["body_rotate"] = Robot.body_rotation_speed
            ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))

        elif(key == 'rotate_right'):
            resetRobotHead()
            Robot.prev_motor_dict["body_rotate"] = -Robot.body_rotation_speed
            ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))

        elif(key == 'nullmotion'):
            Robot.prev_motor_dict["body_forward"] = 0.0
            Robot.prev_motor_dict["body_sideways"] = 0.0
            Robot.prev_motor_dict["body_rotate"] = 0.0
            ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))

        elif(key == 'forward'):
            resetRobotHead()
            
            Robot.prev_motor_dict["body_forward"] = 1.0
            ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))

        elif(key == 'left'):
            resetRobotHead()
            Robot.prev_motor_dict["body_sideways"] = -1.0
            ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))

        elif(key == 'right'):
            resetRobotHead()
            Robot.prev_motor_dict["body_sideways"] = 1.0
            ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))

        # ret = Robot.myrobot.set_modality("motor", list(Robot.prev_motor_dict.values()))

        # for motion_counter in range(len(list_of_motions)):
        #     ret = Robot.myrobot.set_modality("motor", list(list_of_motions[motion_counter].values()))
@sio.on('FROMNODESPEECHAPI')
def frontendspeechdata(data):
    if not (Robot.myrobot == None):
        speech = str(data)
        print(speech)
        if not(speech.lower().find("oh,")==-1):
            Robot.myrobot.set_modality("emotion", "surprised")
        elif(speech.lower().find("reading?")==-1):
            Robot.myrobot.set_modality("emotion", "neutral")
        elif(speech.lower().find("thank you for your patience")==-1):
            Robot.myrobot.set_modality("emotion", "happy")
        ret = Robot.myrobot.set_modality(
            "speech", speech)
        #pychace

        # for motion_counter in range(len(list_of_motions)):
        #     ret = Robot.myrobot.set_modality("motor", list(list_of_motions[motion_counter].values()))

if __name__ == '__main__':
    # print(os.getenv('EMAIL'))
    app.run(debug=False,host=os.getenv('HOST'),port=os.getenv('PORT'))
from dotenv import load_dotenv
from flask import Flask, render_template, Response, request, jsonify,send_file
from animus_wrapper.animus_robot_client import AnimusRobot
from flask_cors import CORS
import os
from animus_wrapper.animus_twin_robot import AnimusTwinRobot
import sys
import eventlet

import socketio
eventlet.monkey_patch()

stopFlag = False
load_dotenv()

sio = socketio.Client()
sio.connect('http://127.0.0.1:9000')
if(sio.connected):
    print("*****************YES*****************")
else:
    print("*****************NO*******************")

app = Flask(__name__)
CORS(app)



Robot = AnimusRobot()
TwinRobot= AnimusTwinRobot()
WorkingRobot = Robot



@app.route('/', methods=['POST', 'GET'])
def index():
    """Video streaming home page."""
    return render_template('index.html'), 200
    # if(request.method == 'POST'):
    #     data = request.get_json()
    #     # print(data)
    #     if(data['email'] == os.getenv('EMAIL') and data['password'] == os.getenv('PASSWORD')):
    #         return render_template('index.html'), 200
    #     else:
    #         abort(401, description="Unauthorized")
    #         # app.route('/stop')
    #         # return render_template('stop.html')
    # else:
    #     # Robot.camera.release()
    #     # abort(401, description="Unauthorized")
    #     return render_template('index.html'), 200


@app.errorhandler(401)
def resource_not_found(e):
    return jsonify(error=str(e)), 401

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=str(e)), 500


# @app.route('/stop')
# def stop():
#     Robot.closeRobot()
#     return render_template('stop.html')

@app.route('/get_robots',methods=['POST'])
def get_robots():
    print(request.json)
    # data=jsonify(request.json())
    # print(data)
    email = request.json['email']
    password = request.json['password']
    mode = request.json['mode']
    if(mode=='live'):
        WorkingRobot=Robot
    else:
        WorkingRobot=TwinRobot
    robotsRetrieved=WorkingRobot.getAllRobots(email,password)
    if not (WorkingRobot.allRobots==None):
        return Response(robotsRetrieved),200
    else:
        return Response({"error":"Connectivity error/Robots not found"}),500

@app.route('/start_robot', methods=['POST'])
def start():
    
    data = jsonify(request.json)
    email = data['email']
    password = data['password']
    robot_id=data['robot_id']
    mode = data['mode']
    if(mode=="live"):
        WorkingRobot.startRobotActivity(email, password,robot_id)
        return render_template('index.html')
    else:
        pass
        #TwinRobot.startRobotActivity(email,password)
        #return render_template(index.html)


@app.route('/video_feed')
def video_feed():
    if(WorkingRobot.stop_thread or WorkingRobot.myrobot==None):
        return send_file('assets/offline-background.gif', mimetype='image/gif')

    return Response(WorkingRobot.gen_frames(WorkingRobot.stop_thread), mimetype='multipart/x-mixed-replace; boundary=frame')


@sio.event
def connect():
    print('connected to server')


@sio.event
def disconnect():
    print('disconnected from server')


@sio.on('FROMNODEAPI')
def frontenddata(data):
    if not (WorkingRobot.myrobot == None):
        key = str(data)
        print(key)
        # list_of_motions=[]
        # motorDict = Robot.utils.get_motor_dict()
        # list_of_motions = [motorDict.copy()]
        if(key == 'head_up'):
            if not (WorkingRobot.head_motion_counter['head_up_down'] == WorkingRobot.head_angle_threshold):
                WorkingRobot.head_motion_counter['head_up_down'] = WorkingRobot.head_motion_counter['head_up_down'] + \
                    Robot.head_angle_incrementer
                WorkingRobot.prev_motor_dict["head_up_down"] = WorkingRobot.head_motion_counter['head_up_down'] * WorkingRobot.utils.HEAD_UP

        elif(key == 'head_down'):
            if not (WorkingRobot.head_motion_counter['head_up_down'] == -1*WorkingRobot.head_angle_threshold):
                WorkingRobot.head_motion_counter['head_up_down'] = WorkingRobot.head_motion_counter['head_up_down'] - \
                    WorkingRobot.head_angle_incrementer
                WorkingRobot.prev_motor_dict["head_up_down"] = WorkingRobot.head_motion_counter['head_up_down'] * WorkingRobot.utils.HEAD_UP

        elif(key == 'head_left'):
            if not (WorkingRobot.head_motion_counter['head_left_right'] == -1*WorkingRobot.head_angle_threshold):
                WorkingRobot.head_motion_counter['head_left_right'] = WorkingRobot.head_motion_counter['head_left_right'] - \
                    WorkingRobot.head_angle_incrementer
                WorkingRobot.prev_motor_dict["head_left_right"] = WorkingRobot.head_motion_counter['head_left_right'] * WorkingRobot.utils.HEAD_RIGHT

        elif(key == 'head_right'):
            if not (WorkingRobot.head_motion_counter['head_left_right'] == WorkingRobot.head_angle_threshold):
                WorkingRobot.head_motion_counter['head_left_right'] = WorkingRobot.head_motion_counter['head_left_right'] + \
                    WorkingRobot.head_angle_incrementer
                WorkingRobot.prev_motor_dict["head_left_right"] = WorkingRobot.head_motion_counter['head_left_right'] * WorkingRobot.utils.HEAD_RIGHT

        elif(key == 'rotate_left'):
            WorkingRobot.prev_motor_dict["body_rotate"] = 60.0

        elif(key == 'rotate_right'):
            WorkingRobot.prev_motor_dict["body_rotate"] = -60.0

        elif(key == 'nullmotion'):
            WorkingRobot.prev_motor_dict["body_forward"] = 0.0
            WorkingRobot.prev_motor_dict["body_sideways"] = 0.0
            WorkingRobot.prev_motor_dict["body_rotate"] = 0.0

        elif(key == 'forward'):
            WorkingRobot.prev_motor_dict["body_forward"] = 1.0

        elif(key == 'left'):
            WorkingRobot.prev_motor_dict["body_sideways"] = -1.0

        elif(key == 'right'):
            WorkingRobot.prev_motor_dict["body_sideways"] = 1.0

        ret = WorkingRobot.myrobot.set_modality(
            "motor", list(WorkingRobot.prev_motor_dict.values()))

        # for motion_counter in range(len(list_of_motions)):
        #     ret = Robot.myrobot.set_modality("motor", list(list_of_motions[motion_counter].values()))


if __name__ == '__main__':
    # print(os.getenv('EMAIL'))
    app.run(debug=False, host=os.getenv('HOST'), port=os.getenv('PORT'))

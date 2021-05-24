import animus_client as animus
import animus_utils as utils
import random
import time
import threading
import logging
import numpy as np
import cv2
from dotenv import load_dotenv
import animus_wrapper.proto_converters
import json

class AnimusRobot:
    def __init__(self):
        
        self.log = utils.create_logger("MyAnimusApp", logging.INFO)
        self.allRobots=None
        self.myrobot = None
        self.animus=animus
        self.videoImgSrc = ''
        self.utils = utils
        self.prev_motor_dict = {}
        self.head_motion_counter = {
            'head_up_down': 0,  # -head_angle_threshold,head_angle_threshold
            'head_left_right': 0,  # -head_angle_threshold,head_angle_threshold
            'head_roll': 0
        }
        self.head_angle_incrementer = 1.5
        self.head_angle_threshold = 75

        self.thread = None
        self.stop_thread = True

        # self.startRobotActivity("ms414@hw.ac.uk","C3):]RR[Rs$Y")
        # self.getRobot()
        # self.openModalities()
        # # self.getVideofeed()
        # self.thread=threading.Thread(target=self.gen_frames)
        # self.thread.start()
    def getAllRobots(self,email,password):
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

            setup_result = animus.setup(
                audio_params, "PythonAnimusBasics", True)
            if not setup_result.success:
                time.sleep(5)
                continue

            login_result = animus.login_user(email, password, False)
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
            if not len(get_robots_result.robots) ==0:
                self.allRobots=get_robots_result
                robotsRetrieved=animus_wrapper.proto_converters.proto_obj_to_dict(get_robots_result)
                robotsRetrieved=json.dumps(robotsRetrieved)
                return robotsRetrieved
            else:
                return None
            

    def startRobotActivity(self, email, password, robot_id):
        self.stop_thread = False

        self.myrobot=self.getRobot(email, password, robot_id)
        if(self.myrobot==None):
            pass
        else:
            self.openModalities()
            # self.getVideofeed()
            self.thread = threading.Thread(
                target=self.gen_frames, args=(lambda: self.stop_thread, ))
            self.thread.start()
            self.prev_motor_dict = utils.get_motor_dict()

    def openModalities(self):
        open_success = self.myrobot.open_modality("vision")
        if not open_success:
            self.log.error("Could not open robot vision modality")
            # sys.exit(-1)

        open_success = self.myrobot.open_modality("motor")
        if not open_success:
            self.log.error("Could not open robot motor modality")
            # sys.exit(-1)

    def getRobot(self, email, password, robot_id):
        chosenRobot=None
        if(self.allRobots==None):
            self.getAllRobots(email,password)
            if(self.allRobots==None):
                return "No robots found"
        
        for i in range(len(self.allRobots)):
            if(self.allRobots[i].robot_details.robot_id==robot_id):
                chosen_robot_details = self.allRobots.robots[id]

                tempRobot = animus.Robot(chosen_robot_details)
                connected_result = self.myrobot.connect()
                if not connected_result.success:
                    # print("Could not connect with robot {}".format(
                    #     self.myrobot.robot_details.robot_id))

                    animus.close_client_interface()
                    break
                else:
                    chosenRobot=tempRobot
        if (chosenRobot==None):
            return "Robot conn error"
        else:      
            return chosenRobot

    def gen_frames(self, stop):  # generate frame by frame from camera
        while True:
            if(stop):
                break
            try:
                image_list, err = self.myrobot.get_modality("vision", True)
            except:
                continue
            if err.success:

                ret, buffer = cv2.imencode('.jpg', image_list[0].image)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

    def closeRobot(self):
        self.myrobot.disconnect()
        animus.close_client_interface()




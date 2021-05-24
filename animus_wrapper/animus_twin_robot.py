import animus_client as animus
from dotenv import load_dotenv
import animus_utils as utils
import random
import time
import threading
import logging
import numpy as np
import cv2
import os
load_dotenv()

def create_logger(name, level):
    logger = logging.getLogger(name)
    if not len(logger.handlers):
        formatter = logging.Formatter('[ %(levelname)-5s - {:10} ] %(asctime)s - %(message)s'.format(name))
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)

        logger.addHandler(ch)
        logger.setLevel(level)

    return logger
class AnimusTwinRobot:
    def __init__(self):
        self.log = create_logger("MyAnimusApp", logging.INFO)
        self.myrobot = None
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

    def startRobotActivity(self, email, password):
        self.stop_thread = False

        self.getRobot(email, password)
        self.openModalities()
        
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
    def getAllRobots(self, email, password):
        for i in range(10):

            self.log.info("V 1.0")
            print("V1.0")
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
            if(email==os.getenv('EMAIL') and password==os.getenv('PASSWORD')):
                self.log.info("Logged in")

            
            login_result = animus.login_user(email, password, False)
            if login_result.success:
                self.log.info("Logged in")
            else:
                time.sleep(5)
                continue

            get_robots_result = animus.get_robots(True, True, False)
    def getRobot(self, email, password):
        for i in range(10):

            self.log.info("V 1.0")
            print("V1.0")
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
            if(email==os.getenv('EMAIL') and password==os.getenv('PASSWORD')):
                self.log.info("Logged in")

            
            login_result = animus.login_user(email, password, False)
            if login_result.success:
                self.log.info("Logged in")
            else:
                time.sleep(5)
                continue

            get_robots_result = animus.get_robots(True, True, False)
            # # print(get_robots_result)
            # if not get_robots_result.localSearchError.success:
            #     self.log.error(get_robots_result.localSearchError.description)

            # if not get_robots_result.remoteSearchError.success:
            #     self.log.error(get_robots_result.remoteSearchError.description)

            # if len(get_robots_result.robots) == 0:
            #     self.log.info("No Robots found")
            #     animus.close_client_interface()
            #     time.sleep(5)
            #     continue

            # chosen_robot_details = get_robots_result.robots[0]

            # self.myrobot = animus.Robot(chosen_robot_details)
            # connected_result = self.myrobot.connect()
            # if not connected_result.success:
            #     print("Could not connect with robot {}".format(
            #         self.myrobot.robot_details.robot_id))
            #     animus.close_client_interface()
            #     time.sleep(5)
            #     continue
            # else:
            #     break

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




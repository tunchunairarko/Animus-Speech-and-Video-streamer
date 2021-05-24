#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2020, Cyberselves Universal Ltd.
# All Rights Reserved


import animus_client as animus
import animus_utils as utils
import sys
import logging
import numpy as np
import random
import cv2
import time
import socketio
import proto_converters
import json
import animus_utils as utils
stopFlag = False
sio = socketio.Client()

log = utils.create_logger("MyAnimusApp", logging.INFO)
log.info(animus.version())
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
    sys.exit(-1)

login_result = animus.login_user("ms414@hw.ac.uk", "C3):]RR[Rs$Y", False)
if login_result.success:
    log.info("Logged in")
else:
    sys.exit(-1)

get_robots_result = animus.get_robots(True, True, False)
data=proto_converters.proto_obj_to_dict(get_robots_result)
# data=proto_converters.dict_to_proto_obj(data)
print(data)
# data=json.dumps(data)
# with open("dummy_robots.json","w+") as writefile:
#     json.dump(data,writefile)
# print(get_robots_result.robots[0].robot_id)
# print(get_robots_result.robots[0].make)
# print(get_robots_result.robots[0].model)
# print(get_robots_result.robots[0].name)
# print(get_robots_result.robots[0].robot_id)
# print(get_robots_result.robots[0].robot_id)
# print(get_robots_result.robots[0].robot_state.location.ip)
# print(get_robots_result.robots[0].robot_state.location.city)
# print(get_robots_result.robots[0].robot_state.location.region)





if not get_robots_result.localSearchError.success:
    log.error(get_robots_result.localSearchError.description)

if not get_robots_result.remoteSearchError.success:
    log.error(get_robots_result.remoteSearchError.description)

if len(get_robots_result.robots) == 0:
    log.info("No Robots found")
    animus.close_client_interface()
    sys.exit(-1)

chosen_robot_details = get_robots_result.robots[0]

myrobot = animus.Robot(chosen_robot_details)
connected_result = myrobot.connect()
if not connected_result.success:
    print("Could not connect with robot {}".format(myrobot.robot_details.robot_id))
    animus.close_client_interface()
    sys.exit(-1)


# # -------------Auditory - Voice Loop------------------------
# #
# # # ----------------Motor Visual Loop------------------------------------
# open_success = myrobot.open_modality("vision")
# if not open_success:
#     log.error("Could not open robot vision modality")
#     sys.exit(-1)

# open_success = myrobot.open_modality("motor")
# if not open_success:
#     log.error("Could not open robot motor modality")
#     sys.exit(-1)

open_success = myrobot.open_modality("emotion")
if not open_success:
    log.error("Could not open robot emotion modality")
    sys.exit(-1)

print(utils.emotions_list)
# myrobot.set_modality("emotion", random.choice(utils.emotions_list))

# motorDict = utils.get_motor_dict()
# list_of_motions = [motorDict.copy()]

# motorDict["head_left_right"] = 2 * utils.HEAD_RIGHT
# motorDict["head_up_down"] = 2 * utils.HEAD_UP
# motorDict["head_roll"] = 0.0
# motorDict["body_forward"] = 0.0
# motorDict["body_sideways"] = 0.0
# motorDict["body_rotate"] = 1.0
# list_of_motions.append(motorDict.copy())

# motorDict["head_left_right"] = 2 * utils.HEAD_LEFT
# list_of_motions.append(motorDict.copy())

# motorDict["head_up_down"] = 2 * utils.HEAD_DOWN
# list_of_motions.append(motorDict.copy())

# counter = 0
# motion_counter = 0


# cv2.namedWindow("RobotView")
# # sio.connect('http://localhost:5000')
# try:
#     while True:
#         try:
#             image_list, err = myrobot.get_modality("vision", True)
#         except:
#             continue
#         if err.success:
#             # sio.emit('pythondata', str(image_list[0].image))                      # send to server
#             cv2.imshow("RobotView", image_list[0].image)
#             j = cv2.waitKey(1)
#             if j == 27:
#                 break

#             counter += 1

#             if counter > 100:
#                 counter = 0
#                 if motion_counter >= len(list_of_motions):
#                     motion_counter = 0
#                 ret = myrobot.set_modality("motor", list(list_of_motions[motion_counter].values()))
#                 motion_counter += 1

# except KeyboardInterrupt:
#     cv2.destroyAllWindows()
#     log.info("Closing down")
#     stopFlag = True
# except SystemExit:
#     cv2.destroyAllWindows()
#     log.info("Closing down")
#     stopFlag = True

# cv2.destroyAllWindows()
# if stopFlag:
#     myrobot.disconnect()
#     animus.close_client_interface()
#     sys.exit(-1)

# # ---------------------------Emotive speech--------------------------
# # open_success = myrobot.open_modality("speech")
# # if not open_success:
# #     log.error("Could not open robot speech modality")
# #     sys.exit(-1)
# #
# # open_success = myrobot.open_modality("emotion")
# # if not open_success:
# #     log.error("Could not open robot emotion modality")
# #     sys.exit(-1)
# #
# # log.info(utils.emotions_list)
# #
# # # Uncomment to send things for the robot to say
# # try:
# #     while True:
# #         msg = input("Robot say: ")
# #         myrobot.set_modality("speech", msg)
# #         myrobot.set_modality("emotion", random.choice(utils.emotions_list))
# # except KeyboardInterrupt:
# #     log.info("Closing down")
# # except SystemExit:
# #     log.info("Closing down")


# myrobot.disconnect()
# animus.close_client_interface()
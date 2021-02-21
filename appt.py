from flask import Flask, render_template, Response, request, abort, jsonify
import cv2
from flask_restful import Resource, Api
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask (__name__)
api = Api(app)

class AnimusRobot:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)

    def gen_frames(self):  # generate frame by frame from camera
        while True:
            # Capture frame-by-frame
            success, frame = self.camera.read()  # read the camera frame
            if not success:
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result



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
            Robot.camera.release()
            abort(401, description="Unauthorized")
            # app.route('/stop')
            # return render_template('stop.html')
    else:
        Robot.camera.release()
        abort(401, description="Unauthorized")

@app.errorhandler(401)
def resource_not_found(e):
    return jsonify(error=str(e)), 401


@app.route('/stop')
def stop():
    Robot.camera.release()
    return render_template('stop.html')

@app.route('/start')
def start():
    Robot.camera = cv2.VideoCapture(0)
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(Robot.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    # print(os.getenv('EMAIL'))
    app.run(debug=True,host=os.getenv('HOST'),port=os.getenv('PORT'))
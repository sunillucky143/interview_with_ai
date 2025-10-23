from flask import Flask, render_template
from flask_socketio import SocketIO
import base64
import cv2
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def hello_world():  # put application's code here
    return render_template('video_capture.html')
@socketio.on('video_frame')
def handle_frame(data):
    header, encoded = data.split(',', 1)
    img_bytes = base64.b64decode(encoded)
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    print(frame.shape)



if __name__ == '__main__':
    app.run()

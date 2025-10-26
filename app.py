from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import base64
import cv2
import numpy as np
import json
import ssl
import os
from ai_proctoring import OptimizedProctoring

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Initialize the optimized proctoring system
proctoring_module = OptimizedProctoring()


@app.route('/')
def hello_world():
    """Main route for the proctoring system"""
    return render_template('video_capture.html')

@app.route('/check_camera')
def check_camera():
    """Check if camera is available and accessible"""
    try:
        # Try to access camera
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                return {'status': 'success', 'message': 'Camera is accessible'}
            else:
                return {'status': 'error', 'message': 'Camera opened but cannot read frames'}
        else:
            return {'status': 'error', 'message': 'Camera is not accessible'}
    except Exception as e:
        return {'status': 'error', 'message': f'Camera error: {str(e)}'}
@socketio.on('video_frame')
def handle_frame(data):
    """Handle incoming video frames from the frontend"""
    try:
        # Decode the frame from the frontend
        header, encoded = data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            emit('proctoring_error', {'error': 'Failed to decode frame'})
            return

        # Process the frame with the optimized proctoring system
        processed_frame = proctoring_module.process_frame(frame)
        
        # Extract proctoring status and alerts
        status_info = proctoring_module.get_proctoring_status()
        
        # Encode the processed frame back to base64 for display
        _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Send comprehensive status back to client
        emit('proctoring_status', {
            'status': status_info['status'],
            'alerts': status_info['alerts'],
            'eye_direction': status_info['eye_direction'],
            'head_pose': status_info['head_pose'],
            'fps': status_info['fps'],
            'processed_frame': f"data:image/jpeg;base64,{frame_base64}"
        })
        
    except Exception as e:
        print(f"Error processing frame: {e}")
        emit('proctoring_error', {'error': str(e)})



def create_ssl_context():
    """Create SSL context for HTTPS support"""
    try:
        # Try to create self-signed certificate
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        # For development, we'll use a simple approach
        return None  # Will use HTTP for now, but structure is ready for HTTPS
    except Exception as e:
        print(f"SSL context creation failed: {e}")
        return None

if __name__ == '__main__':
    # Check if we should use HTTPS
    use_https = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
    
    if use_https:
        ssl_context = create_ssl_context()
        if ssl_context:
            print("Starting server with HTTPS...")
            socketio.run(app, debug=True, host='0.0.0.0', port=5000, ssl_context=ssl_context)
        else:
            print("HTTPS not available, falling back to HTTP...")
            socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        print("Starting server with HTTP...")
        print("Note: For camera access from other devices, consider using HTTPS")
        print("To enable HTTPS, set environment variable: USE_HTTPS=true")
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)

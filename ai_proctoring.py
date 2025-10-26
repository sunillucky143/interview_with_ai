import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import time
import gc
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProctoringConfig:
    """Configuration class for proctoring parameters"""
    # Detection thresholds
    MAX_HEAD_TURN_ANGLE = 35
    EYE_FIXATION_FRAMES = 10  # Reduced from 20 to make it more sensitive
    EYE_SMOOTHING = 5
    EYE_TOLERANCE = 0.05
    MAX_NUM_FACES = 2
    
    # Performance settings
    FRAME_SKIP = 1
    FACE_DETECTION_INTERVAL = 15
    MEMORY_CLEANUP_INTERVAL = 200
    
    # Camera settings
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    FPS_TARGET = 30

class OptimizedProctoring:
    """Optimized proctoring system with memory and performance improvements"""
    
    def __init__(self):
        self.config = ProctoringConfig()
        
        # Initialize MediaPipe components once
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize face detection and mesh once
        self.face_detector = self.mp_face_detection.FaceDetection(
            min_detection_confidence=0.6
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            refine_landmarks=True,
            max_num_faces=self.config.MAX_NUM_FACES,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Pre-allocate arrays for better performance
        self.eye_landmarks = {
            'LEFT_IRIS': np.array([474, 475, 476, 477], dtype=np.int32),
            'RIGHT_IRIS': np.array([469, 470, 471, 472], dtype=np.int32),
            'LEFT_EYE': np.array([33, 133], dtype=np.int32),
            'RIGHT_EYE': np.array([362, 263], dtype=np.int32)
        }
        
        # Pre-allocate model points for head pose
        self.model_points = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -330.0, -65.0),
            (-225.0, 170.0, -135.0),
            (225.0, 170.0, -135.0),
            (-150.0, -150.0, -125.0),
            (150.0, -150.0, -125.0)
        ], dtype=np.float64)
        
        # Pre-allocate camera matrix
        self.camera_matrix = None
        self.dist_coeffs = np.zeros((4, 1), dtype=np.float64)
        
        # Deques for smoothing
        self.eye_dir_history = deque(maxlen=self.config.EYE_SMOOTHING)
        self.eye_fixation_history = deque(maxlen=self.config.EYE_FIXATION_FRAMES)
        
        # State management to reduce flickering
        self.last_eye_direction = "Center"
        self.last_head_pose_status = "Head facing front"
        self.last_alert = None
        self.stable_frames = 0
        self.min_stable_frames = 3
        self.multiple_faces_detected = False
        
        # Performance tracking
        self.frame_count = 0
        self.last_face_check = 0
        self.last_cleanup = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # Pre-allocate frame processing arrays
        self.rgb_frame = None
        
        logger.info("Proctoring system initialized successfully")

    def setup_camera_matrix(self, width: int, height: int) -> None:
        """Setup camera matrix once for head pose calculation"""
        if self.camera_matrix is None:
            focal_length = width
            center = (width / 2, height / 2)
            self.camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)

    def get_iris_direction_optimized(self, landmarks, w: int, h: int) -> str:
        """Optimized iris direction calculation with pre-allocated arrays"""
        try:
            # Use pre-allocated indices
            left_iris_indices = self.eye_landmarks['LEFT_IRIS']
            right_iris_indices = self.eye_landmarks['RIGHT_IRIS']
            left_eye_indices = self.eye_landmarks['LEFT_EYE']
            right_eye_indices = self.eye_landmarks['RIGHT_EYE']
            
            # Calculate centers more efficiently
            left_center = np.mean([(landmarks[i].x * w, landmarks[i].y * h) 
                                 for i in left_iris_indices], axis=0)
            right_center = np.mean([(landmarks[i].x * w, landmarks[i].y * h) 
                                  for i in right_iris_indices], axis=0)
            
            # Calculate eye corners
            left_corner = np.array([landmarks[left_eye_indices[0]].x * w, 
                                  landmarks[left_eye_indices[0]].y * h])
            right_corner = np.array([landmarks[left_eye_indices[1]].x * w, 
                                   landmarks[left_eye_indices[1]].y * h])
            
            # Avoid division by zero
            eye_width = right_corner[0] - left_corner[0]
            if abs(eye_width) < 1e-6:
                return "Center"
            
            horizontal_left = (left_center[0] - left_corner[0]) / eye_width
            
            # Right eye calculation
            left_corner = np.array([landmarks[right_eye_indices[0]].x * w, 
                                  landmarks[right_eye_indices[0]].y * h])
            right_corner = np.array([landmarks[right_eye_indices[1]].x * w, 
                                   landmarks[right_eye_indices[1]].y * h])
            
            eye_width = right_corner[0] - left_corner[0]
            if abs(eye_width) < 1e-6:
                return "Center"
            
            horizontal_right = (right_center[0] - left_corner[0]) / eye_width
            gaze = (horizontal_left + horizontal_right) / 2
            
            if gaze < 0.35 - self.config.EYE_TOLERANCE:
                return "Left"
            elif gaze > 0.65 + self.config.EYE_TOLERANCE:
                return "Right"
            else:
                return "Center"
        except Exception as e:
            logger.warning(f"Error in iris direction calculation: {e}")
            return "Center"

    def analyze_eye_fixation_optimized(self) -> Optional[str]:
        """Optimized eye fixation analysis - checks for consecutive same direction"""
        if len(self.eye_fixation_history) < self.config.EYE_FIXATION_FRAMES:
            return None
        
        # Check for consecutive same direction (not just most common)
        history_list = list(self.eye_fixation_history)
        current_direction = history_list[-1]
        
        # If current direction is Center, no fixation issue
        if current_direction == "Center":
            return None
        
        # Count consecutive occurrences of current direction from the end
        consecutive_count = 0
        for direction in reversed(history_list):
            if direction == current_direction:
                consecutive_count += 1
            else:
                break
        
        # Flag if same direction for too long
        if consecutive_count >= self.config.EYE_FIXATION_FRAMES:
            return f"⚠️ Eyes fixed {current_direction} too long ({consecutive_count} frames)"
        
        return None

    def get_smoothed_eye_direction(self) -> str:
        """Get smoothed eye direction using weighted average to reduce flickering"""
        if len(self.eye_dir_history) == 0:
            return "Center"
        
        # Use weighted average where recent values have more weight
        directions = list(self.eye_dir_history)
        weights = np.linspace(0.5, 1.0, len(directions))
        
        # Count weighted occurrences
        direction_weights = {"Left": 0, "Right": 0, "Center": 0}
        for direction, weight in zip(directions, weights):
            direction_weights[direction] += weight
        
        return max(direction_weights, key=direction_weights.get)

    def detect_multiple_faces_optimized(self, frame: np.ndarray) -> bool:
        """Optimized multiple face detection with reduced processing"""
        try:
            # Use smaller frame for face detection to improve performance
            small_frame = cv2.resize(frame, (320, 240))
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            results = self.face_detector.process(rgb_small)
            return results.detections and len(results.detections) > 1
        except Exception as e:
            logger.warning(f"Error in face detection: {e}")
            return False

    def get_head_pose_optimized(self, face_landmarks, img_w: int, img_h: int) -> Optional[np.ndarray]:
        """Optimized head pose calculation with pre-allocated arrays"""
        try:
            # Setup camera matrix if not done
            self.setup_camera_matrix(img_w, img_h)
            
            # Pre-defined landmark indices for head pose
            pose_indices = [1, 152, 263, 33, 287, 57]
            image_points = np.array([
                (face_landmarks[i].x * img_w, face_landmarks[i].y * img_h)
                for i in pose_indices
            ], dtype=np.float64)
            
            success, rotation_vector, _ = cv2.solvePnP(
                self.model_points, image_points, self.camera_matrix, self.dist_coeffs
            )
            
            if not success:
                return None
                
            rotation_mat, _ = cv2.Rodrigues(rotation_vector)
            proj_mat = np.hstack((rotation_mat, np.zeros((3, 1))))
            _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_mat)
            return euler_angles.flatten()
        except Exception as e:
            logger.warning(f"Error in head pose calculation: {e}")
            return None

    def cleanup_memory(self) -> None:
        """Clean up memory and force garbage collection"""
        try:
            gc.collect()
            logger.info("Memory cleanup performed")
        except Exception as e:
            logger.warning(f"Error during memory cleanup: {e}")

    def calculate_fps(self) -> float:
        """Calculate and display FPS"""
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.fps_start_time >= 1.0:
            fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time
            return fps
        return 0

    def get_proctoring_status(self) -> dict:
        """Get current proctoring status and alerts"""
        status = "Normal"
        alerts = []
        
        # Check for multiple faces
        if hasattr(self, 'multiple_faces_detected') and self.multiple_faces_detected:
            status = "Cheating Detected"
            alerts.append("Multiple faces detected")
        
        # Check for head pose issues
        if "turned away" in self.last_head_pose_status:
            status = "Warning"
            alerts.append("Head turned away from screen")
        
        # Check for eye fixation
        eye_alert = self.analyze_eye_fixation_optimized()
        if eye_alert:
            status = "Warning"
            alerts.append(eye_alert)
        
        # Get current eye direction
        eye_direction = self.last_eye_direction if hasattr(self, 'last_eye_direction') else "Center"
        
        # Get current FPS
        current_fps = self.calculate_fps()
        
        return {
            'status': status,
            'alerts': alerts,
            'eye_direction': eye_direction,
            'head_pose': self.last_head_pose_status,
            'fps': current_fps
        }

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Main frame processing with optimizations and flickering reduction"""
        self.frame_count += 1
        h, w = frame.shape[:2]
        
        # Check for multiple faces less frequently
        if self.frame_count - self.last_face_check >= self.config.FACE_DETECTION_INTERVAL:
            self.multiple_faces_detected = self.detect_multiple_faces_optimized(frame)
            if self.multiple_faces_detected:
                cv2.putText(frame, "⚠️ Multiple Faces Detected!", (30, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.putText(frame, "🚨 CHEATING FLAGGED!", (30, 100), 
                           cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 2)
                return frame
            self.last_face_check = self.frame_count
        
        # Convert to RGB only once
        if self.rgb_frame is None or self.rgb_frame.shape != frame.shape:
            self.rgb_frame = np.zeros_like(frame)
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, dst=self.rgb_frame)
        
        # Process face mesh
        results = self.face_mesh.process(self.rgb_frame)
        
        if results.multi_face_landmarks:
            # Process only the first face for performance
            face_landmarks = results.multi_face_landmarks[0]
            
            # Always draw landmarks for smooth visual experience
            self.mp_drawing.draw_landmarks(
                frame, face_landmarks, self.mp_face_mesh.FACEMESH_CONTOURS,
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
            )
            
            # Head pose calculation with stability
            head_pose = self.get_head_pose_optimized(face_landmarks.landmark, w, h)
            if head_pose is not None:
                yaw, pitch, _ = head_pose
                if abs(yaw) > self.config.MAX_HEAD_TURN_ANGLE or abs(pitch) > self.config.MAX_HEAD_TURN_ANGLE:
                    new_status = "⚠️ Head turned away"
                else:
                    new_status = "Head facing front"
                
                # Only update if status is stable for multiple frames
                if new_status == self.last_head_pose_status:
                    self.stable_frames += 1
                else:
                    self.stable_frames = 0
                    self.last_head_pose_status = new_status
                
                # Display status with stability check
                if self.stable_frames >= self.min_stable_frames:
                    color = (0, 0, 255) if "turned away" in new_status else (0, 255, 0)
                    cv2.putText(frame, new_status, (30, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                else:
                    # Keep showing last stable status
                    color = (0, 0, 255) if "turned away" in self.last_head_pose_status else (0, 255, 0)
                    cv2.putText(frame, self.last_head_pose_status, (30, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Eye direction analysis with improved smoothing
            eye_dir = self.get_iris_direction_optimized(face_landmarks.landmark, w, h)
            self.eye_dir_history.append(eye_dir)
            
            # Add raw eye direction to fixation history for accurate detection
            self.eye_fixation_history.append(eye_dir)
            
            # Smooth direction calculation with stability
            if len(self.eye_dir_history) > 0:
                # Use weighted average for smoother transitions
                smooth_dir = self.get_smoothed_eye_direction()
                
                # Only update display if direction is stable
                if smooth_dir == self.last_eye_direction:
                    self.stable_frames += 1
                else:
                    self.stable_frames = 0
                    self.last_eye_direction = smooth_dir
                
                cv2.putText(frame, f"Eye Dir: {smooth_dir}", (30, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                
                # Show fixation count for debugging
                if len(self.eye_fixation_history) > 0:
                    history_list = list(self.eye_fixation_history)
                    current_direction = history_list[-1]
                    if current_direction != "Center":
                        consecutive_count = 0
                        for direction in reversed(history_list):
                            if direction == current_direction:
                                consecutive_count += 1
                            else:
                                break
                        cv2.putText(frame, f"Fixation: {consecutive_count}/{self.config.EYE_FIXATION_FRAMES}", 
                                   (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Check for eye fixation with stability
                alert = self.analyze_eye_fixation_optimized()
                if alert and alert != self.last_alert:
                    self.last_alert = alert
                    cv2.putText(frame, alert, (30, 150),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                elif self.last_alert and alert is None:
                    self.last_alert = None
        else:
            cv2.putText(frame, "No face detected", (30, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            # Reset states when no face detected
            self.last_eye_direction = "Center"
            self.last_head_pose_status = "Head facing front"
            self.last_alert = None
            self.stable_frames = 0
        
        # Display FPS
        fps = self.calculate_fps()
        if fps > 0:
            cv2.putText(frame, f"FPS: {fps:.1f}", (w - 120, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Memory cleanup
        if self.frame_count - self.last_cleanup >= self.config.MEMORY_CLEANUP_INTERVAL:
            self.cleanup_memory()
            self.last_cleanup = self.frame_count
        
        return frame

    def run(self) -> None:
        """Main execution loop with optimizations"""
        try:
            # Initialize camera with optimized settings
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, self.config.FPS_TARGET)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not cap.isOpened():
                logger.error("Failed to open camera")
                return
            
            logger.info("Starting proctoring system...")
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    break
                
                # Flip frame horizontally
                frame = cv2.flip(frame, 1)
                
                # Process frame
                processed_frame = self.process_frame(frame)
                
                # Display frame
                cv2.imshow("Proctoring Monitor", processed_frame)
                
                # Check for exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            # Cleanup
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()
            self.cleanup_memory()
            logger.info("Proctoring system stopped")

def main():
    """Main function"""
    try:
        proctoring = OptimizedProctoring()
        proctoring.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
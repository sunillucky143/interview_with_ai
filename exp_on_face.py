"""
head_eye_tracker.py
Real-time head & eye tracking using MediaPipe Face Mesh.
Detects eyes and estimates head pose (yaw, pitch, roll).
"""

import cv2
import mediapipe as mp
import numpy as np
import argparse
import math
from pathlib import Path

mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh

# 3D model reference points for head pose (based on facial landmarks)
FACE_3D_POINTS = np.array([
    [0.0, 0.0, 0.0],        # Nose tip
    [0.0, -330.0, -65.0],   # Chin
    [-225.0, 170.0, -135.0],# Left eye left corner
    [225.0, 170.0, -135.0], # Right eye right corner
    [-150.0, -150.0, -125.0],# Left mouth corner
    [150.0, -150.0, -125.0]  # Right mouth corner
], dtype=np.float64)

# Corresponding landmark indices in MediaPipe
FACE_LANDMARK_IDS = [1, 152, 33, 263, 61, 291]

def estimate_head_pose(image_points, w, h):
    """Estimate yaw, pitch, roll from 2D landmarks using solvePnP."""
    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")

    dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion
    success, rotation_vec, translation_vec = cv2.solvePnP(
        FACE_3D_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

    if not success:
        return None, None, None

    # Convert rotation vector to rotation matrix
    rmat, _ = cv2.Rodrigues(rotation_vec)
    proj_matrix = np.hstack((rmat, translation_vec))
    euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6]
    pitch, yaw, roll = [float(a) for a in euler_angles]
    return pitch, yaw, roll

def main(input_source=0, output=None):
    cap = cv2.VideoCapture(input_source)
    if not cap.isOpened():
        print("Error: Cannot open webcam/video.")
        return

    if output:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(output, fourcc, 25.0,
                                     (int(cap.get(3)), int(cap.get(4))))
    else:
        out_writer = None

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,  # Better accuracy for eyes and lips
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as face_mesh:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)  # mirror view
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = face_mesh.process(rgb)

            if result.multi_face_landmarks:
                for face_landmarks in result.multi_face_landmarks:
                    # Draw face mesh overlay
                    mp_drawing.draw_landmarks(
                        frame,
                        face_landmarks,
                        mp_face_mesh.FACEMESH_CONTOURS,
                        mp_drawing.DrawingSpec(color=(0,255,255), thickness=1, circle_radius=1),
                        mp_drawing.DrawingSpec(color=(0,128,255), thickness=1)
                    )

                    # Extract key landmarks for head pose
                    image_points = []
                    for idx in FACE_LANDMARK_IDS:
                        lm = face_landmarks.landmark[idx]
                        x, y = int(lm.x * w), int(lm.y * h)
                        image_points.append((x, y))
                    image_points = np.array(image_points, dtype=np.float64)

                    pitch, yaw, roll = estimate_head_pose(image_points, w, h)
                    if pitch is not None:
                        cv2.putText(frame, f"Pitch: {pitch:.1f}", (20, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                        cv2.putText(frame, f"Yaw:   {yaw:.1f}", (20, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                        cv2.putText(frame, f"Roll:  {roll:.1f}", (20, 80),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                    # Draw eye landmarks (for visual clarity)
                    left_eye_ids = list(range(474, 478))
                    right_eye_ids = list(range(469, 473))
                    for eye_id in left_eye_ids + right_eye_ids:
                        pt = face_landmarks.landmark[eye_id]
                        cx, cy = int(pt.x * w), int(pt.y * h)
                        cv2.circle(frame, (cx, cy), 2, (255, 0, 0), -1)

            cv2.imshow("AI Head & Eye Tracker", frame)
            if out_writer:
                out_writer.write(frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                break

    cap.release()
    if out_writer:
        out_writer.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-time head & eye tracker using MediaPipe.")
    parser.add_argument("--input", "-i", type=str, default=None, help="Video file path or webcam (default webcam).")
    parser.add_argument("--output", "-o", type=str, default=None, help="Save output video file (optional).")
    args = parser.parse_args()

    src = 0 if args.input is None else args.input
    main(src, args.output)

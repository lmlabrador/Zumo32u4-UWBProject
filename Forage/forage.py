import cv2
import numpy as np
from picamera import PiCamera
from picamera.array import PiRGBArray
import time
import math
from Zumo import Zumo
from uwb_reader import UWBReader

# =============== CONFIGURATION ===============
RESOLUTION = (320, 240)
GOAL_POSITION = (3.4, 1.5)
UWB_PORT = "/dev/ttyUWB"
SHOW_VIDEO = True
DEBUG_PRINTS = True

# ============= TUNED PARAMETERS =============
K0 = 150        # Empty area turn rate (positive = right, negative = left)
K1 = -100       # Puck detection turn rate (inward push)
K2 = -150      # Robot avoidance strength (unused but kept)
K3 = 200        # Goal attraction strength
BASE_SPEED = 300
TURN_GAIN =100
MAX_TURN_RATE = 100000000
SEARCH_TURN =300

# ============= VISION PARAMETERS =============
PUCK_HSV = {
    "lower": np.array([100, 70, 50]),
    "upper": np.array([140, 255, 255])
}
MIN_PUCK_AREA = int(RESOLUTION[0] * RESOLUTION[1] * 0.005)
ERODE_ITER = 10
DILATE_ITER = 1
POSITION_HISTORY_LENGTH = 5

# ============= ROI =============
ROI_TOP_WIDTH = 0.4     
ROI_BOTTOM_WIDTH = 0.4   
ROI_HEIGHT = 0.9         

class ForagingController:
    def __init__(self):
        self.zumo = Zumo()
        self.uwb = UWBReader(port=UWB_PORT)
        self.camera = PiCamera()
        self.camera.resolution = RESOLUTION
        self.raw_capture = PiRGBArray(self.camera, size=RESOLUTION)
        
        # horizontalal ROI Coordinates
        self.roi_top_start_x = int(RESOLUTION[0] * (0.5 - ROI_TOP_WIDTH/2))
        self.roi_top_end_x = int(RESOLUTION[0] * (0.5 + ROI_TOP_WIDTH/2))
        self.roi_bottom_start_x = int(RESOLUTION[0] * (0.5 - ROI_BOTTOM_WIDTH/2))
        self.roi_bottom_end_x = int(RESOLUTION[0] * (0.5 + ROI_BOTTOM_WIDTH/2))
        self.roi_start_y = int(RESOLUTION[1] * (1 - ROI_HEIGHT))
        self.roi_end_y = RESOLUTION[1] - 1
        
        # ROI Mask (horizontal shape)
        self.roi_mask = np.zeros((RESOLUTION[1], RESOLUTION[0]), dtype=np.uint8)
        pts = np.array([
            [self.roi_top_start_x, self.roi_start_y],
            [self.roi_top_end_x, self.roi_start_y],
            [self.roi_bottom_end_x, self.roi_end_y],
            [self.roi_bottom_start_x, self.roi_end_y]
        ])
        cv2.fillPoly(self.roi_mask, [pts], 255)
        
        # State variables (unchanged from original)
        self.previous_distance = 0
        self.delta_d_filtered = 0
        self.position_history = []
        self.frame_count = 0
        self.start_time = time.time()
        self.last_puck_pos = (0, 0)
        self.last_phi = 0
        self.detect_time = 0
        self.control_time = 0
        self.last_metrics_time = time.time()

    def initialize_system(self):
        print("[SYSTEM] Initializing foraging controller...")
        print(f"[CONFIG] Goal position: {GOAL_POSITION}m | Base speed: {BASE_SPEED}")
        print(f"[PARAMS] K0={K0}, K1={K1}, K2={K2}, K3={K3}")
        
        if not self.uwb.start():
            raise RuntimeError("[ERROR] UWB initialization failed")
        
        time.sleep(2)
        print("[SYSTEM] Hardware ready")

    def smooth_position(self, position):
        """Unchanged from original"""
        self.position_history.append(position)
        if len(self.position_history) > POSITION_HISTORY_LENGTH:
            self.position_history.pop(0)
        return (sum(p[0] for p in self.position_history)/len(self.position_history),
                sum(p[1] for p in self.position_history)/len(self.position_history))

    def detect_puck(self, frame):
        """Modified for horizontalal ROI"""
        detect_start = time.time()
        
        # Apply horizontalal mask
        masked_frame = cv2.bitwise_and(frame, frame, mask=self.roi_mask)
        roi = masked_frame[self.roi_start_y:self.roi_end_y, 
                        min(self.roi_bottom_start_x, self.roi_top_start_x):
                        max(self.roi_bottom_end_x, self.roi_top_end_x)]
        
        # Rest of detection remains identical
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, PUCK_HSV["lower"], PUCK_HSV["upper"])
        mask = cv2.erode(mask, None, iterations=ERODE_ITER)
        mask = cv2.dilate(mask, None, iterations=DILATE_ITER)
        
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        has_puck, puck_angle, puck_pos = False, 0, (0, 0)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > MIN_PUCK_AREA:
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    puck_pos = (cx, cy)
                    roi_center_x = (self.roi_top_end_x - self.roi_top_start_x) // 2
                    puck_angle = math.atan2(cx - roi_center_x, roi_center_x)
                    has_puck = True
        
        self.detect_time += time.time() - detect_start
        return has_puck, puck_angle, puck_pos

    def calculate_goal_attraction(self, current_distance):
        """Unchanged from original"""
        delta_d = current_distance - self.previous_distance
        self.delta_d_filtered = 0.8 * self.delta_d_filtered + 0.2 * delta_d
        self.previous_distance = current_distance
        phi = K3 * self.delta_d_filtered
        self.last_phi = phi
        if DEBUG_PRINTS:
            print(f"[PHI] Δd: {delta_d:.3f} | φ: {math.degrees(phi):.1f}°")
        return phi

    def control_motors(self, has_puck, puck_angle, current_distance):
        """Unchanged from original (with your K-values)"""
        control_start = time.time()
        
        if has_puck:
            goal_phi = self.calculate_goal_attraction(current_distance)
            turn = K1 * puck_angle + goal_phi
            if DEBUG_PRINTS:
                print(f"[PUCK] Approaching at {math.degrees(puck_angle):.1f}°")
        else:
            turn = K0
            if DEBUG_PRINTS:
                print("[SEARCH] Circling")
        
        turn = np.clip(turn, -MAX_TURN_RATE, MAX_TURN_RATE)
        left = BASE_SPEED + turn
        right = BASE_SPEED - turn
        
        left = np.clip(left, -255, 255)
        right = np.clip(right, -255, 255)
        
        self.control_time += time.time() - control_start
        return int(left), int(right)

    def draw_debug_info(self, image, has_puck, puck_pos, puck_angle, left, right, fps, uwb_pos, current_distance):
        """Added horizontal visualization"""
        debug_img = image.copy()
        
        # Draw horizontalal ROI
        cv2.polylines(debug_img, [np.array([
            [self.roi_top_start_x, self.roi_start_y],
            [self.roi_top_end_x, self.roi_start_y],
            [self.roi_bottom_end_x, self.roi_end_y],
            [self.roi_bottom_start_x, self.roi_end_y]
        ])], True, (0, 255, 255), 1)
        
        # debug drawings
        if has_puck:
            puck_x = self.roi_top_start_x + puck_pos[0]
            puck_y = self.roi_start_y + puck_pos[1]
            cv2.circle(debug_img, (puck_x, puck_y), 10, (0, 255, 0), 2)
            
        font = cv2.FONT_HERSHEY_SIMPLEX
        y_pos = 20
        for text in [
            f"FPS: {fps:.1f}",
            f"Motors: L={left} R={right}",
            f"UWB: ({uwb_pos[0]:.1f}, {uwb_pos[1]:.1f})",
            f"Dist: {current_distance:.2f}m",
            f"Puck Angle: {math.degrees(puck_angle):.1f}°" if has_puck else "No puck"
        ]:
            cv2.putText(debug_img, text, (10, y_pos), font, 0.5, (255, 255, 255), 1)
            y_pos += 20
        
        return debug_img

    def run(self):
        """Main loop with horizontalal ROI processing"""
        self.initialize_system()
        
        try:
            for frame in self.camera.capture_continuous(
                self.raw_capture, format="bgr", use_video_port=True):
                
                self.frame_count += 1
                image = frame.array
                
                # UWB positioning 
                raw_pos = self.uwb.get_latest_position()
                if None in raw_pos:
                    uwb_pos = (0, 0)
                    current_distance = 0
                else:
                    uwb_pos = self.smooth_position(raw_pos)
                    current_distance = math.hypot(GOAL_POSITION[0] - uwb_pos[0], 
                                                GOAL_POSITION[1] - uwb_pos[1])
                
                # Detect in horizontalal ROI
                has_puck, puck_angle, puck_pos = self.detect_puck(image)
                
                
                left, right = self.control_motors(has_puck, puck_angle, current_distance)
                self.zumo.send_speeds(left, right)
                
            
                if SHOW_VIDEO:
                    fps = self.frame_count / (time.time() - self.start_time)
                    debug_img = self.draw_debug_info(
                        image, has_puck, puck_pos, puck_angle,
                        left, right, fps, uwb_pos, current_distance
                    )
                    cv2.imshow("Foraging Controller", debug_img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                self.raw_capture.truncate(0)

        except KeyboardInterrupt:
            print("\n[SYSTEM] Shutting down...")
        finally:
            self.zumo.send_speeds(0, 0)
            self.uwb.stop()
            self.camera.close()
            if SHOW_VIDEO:
                cv2.destroyAllWindows()
            

            total_time = time.time() - self.start_time
            print("\n=== FINAL REPORT ===")
            print(f"Frames: {self.frame_count} | FPS: {self.frame_count/total_time:.1f}")
            print(f"Avg detect: {(self.detect_time/self.frame_count)*1000:.1f}ms")
            print(f"Avg control: {(self.control_time/self.frame_count)*1000:.1f}ms")

if __name__ == "__main__":
    controller = ForagingController()
    controller.run()

import cv2
import numpy as np

def simulate_track_masking():
    # [Current Y, Target Bottom X, Base Width, Base Height, Speed]
    obs_adjacent = [200, 0, 200, 250, 3]  # Passing Train 
    obs_hazard = [200, 400, 120, 120, 4]    # Stalled Truck 

    # 1. The Full Visual Track (Sensor Range - 5km)
    track_corners = np.array([[(150, 600), (350, 200), (450, 200), (650, 600)]], dtype=np.int32)
    
    # 2. The DANGER ZONE (Active Braking ROI - 2km) - Starts lower on the screen!
    roi_corners = np.array([[(150, 600), (275, 350), (525, 350), (650, 600)]], dtype=np.int32)

    print("Simulation running. Press 'q' to close the window.")

    while True:
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        
        # Draw Horizon and Full Track (Faint grey)
        cv2.line(frame, (0, 200), (800, 200), (100, 100, 100), 2)
        cv2.fillPoly(frame, track_corners, (40, 40, 40)) 

        # HUD Text
        cv2.putText(frame, "Aegis Edge Vision - Live Simulation", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, "Sensor Visual Range (5km) vs. Auto-Brake Zone (2km)", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        # Draw the Active Danger Zone (Green Mask)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, roi_corners, 255)
        overlay = frame.copy()
        cv2.fillPoly(overlay, roi_corners, (0, 100, 0))
        frame = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)
        
        # Draw a bright line marking the start of the brakes
        cv2.line(frame, (275, 350), (525, 350), (0, 255, 0), 2)
        cv2.putText(frame, "BRAKING ZONE THRESHOLD", (535, 355), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Move obstacles closer to camera
        obs_adjacent[0] += obs_adjacent[4]  
        if obs_adjacent[0] > 600: obs_adjacent[0] = 200

        obs_hazard[0] += obs_hazard[4]
        if obs_hazard[0] > 600: obs_hazard[0] = 200

        # --- PERSPECTIVE MATH (Makes objects grow as they approach) ---
        def process_perspective(obs_y, target_x, base_w, base_h):
            # Calculate how close it is (0.0 at horizon, 1.0 at screen bottom)
            progress = max(0.03, (obs_y - 200) / 400.0)
            
            w = int(base_w * progress)
            h = int(base_h * progress)
            
            # Radiate out from the center vanishing point (400, 200)
            current_center_x = 400 + (target_x - 400) * progress
            x = int(current_center_x - (w / 2))
            
            # Draw UP from the footprint coordinate
            y = int(obs_y - h) 
            return x, y, w, h, obs_y, int(current_center_x)

        obstacles = [
            {"data": process_perspective(*obs_adjacent[:4]), "name": "Passing Train"},
            {"data": process_perspective(*obs_hazard[:4]), "name": "Stalled Truck"}
        ]

        # --- LOGIC ---
        for obs in obstacles:
            x, y, w, h, foot_y, foot_x = obs["data"]
            if foot_y >= 600: foot_y = 599

            # Check if footprint is inside the Green Zone array
            is_in_corridor = mask[foot_y, foot_x] == 255
            
            if is_in_corridor:
                color = (0, 0, 255) # Red
                status = "DANGER: BRAKES TRIGGERED"
            else:

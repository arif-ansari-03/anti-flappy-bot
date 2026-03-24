import cv2
import numpy as np

import keyboard
import pydirectinput
import time

# print(pydirectinput.PAUSE)
# pydirectinput.PAUSE = 0.2
# pydirectinput.FAILSAFE = False

# Load Background for subtraction

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

# Constants
GROUND_Y = 580 // 2  
SKY_Y = 70 // 2
PIPE_WIDTH = 135 // 2

# JS Ellipse Dimensions: 71x51 (Radii are half: 35.5, 25.5)
BIRD_RADIUS_X = 35 // 2 
BIRD_RADIUS_Y = 25 // 2 

# Constants from your JS file
BIRD_W, BIRD_H = 71 // 2 , 51 // 2 

# Pre-allocate arrays and kernels outside the loop for performance
h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
bird_kernel = np.ones((5, 5), np.uint8)
BEAK_LOWER = np.array([0, 150, 150])
BEAK_UPPER = np.array([10, 255, 255])

y_prev = 585 // 2

last_flap_time = time.time()
while True:
    for _ in range(2):  # drop old frames
        cap.grab()
    ret, frame = cap.read()

    if not ret: break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

       
    # 2. FIND BLACK LINES
    # We look for very low brightness in the frame
    _, black_mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
    
    # 3. HORIZONTAL LINE KERNEL
    horizontal_lines = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, h_kernel)

    # 4. HIGHLIGHT PIPE EDGES
    # Find contours of these horizontal lines
    cnts, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    x_min = 10000
    valid_rects = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        # Track the leftmost edge (closest pipe)
        # Filter: Must be above ground and roughly match pipe width characteristics
        if y < GROUND_Y and y > SKY_Y and w > 30:
            valid_rects.append((x, y, w, h))
            x_min = min(x_min, x)

    y_list = []
    for (x, y, w, h) in valid_rects:
        if abs(x - x_min) <= 2: # Tolerance for the closest edge
            y_list.append((y, x))
            # Highlight the detected edge in Magenta
            # cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
            # cv2.putText(frame, f"Edge Y:{y}, X:{x}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (255, 0, 255), 1)

    y_list.sort() # Sort by y value (top to bottom)

    y_base = 290
    if len(y_list) == 2: # these are edges of the bottom pipe as top pipe is not visible
        y_base = y_list[0][0]

    elif len(y_list) == 3: # maybe 2 edges of bottom or top and 1 of the other
        if y_list[1][0]-y_list[0][0] <= 30:
            y_base = y_list[2][0] # 2 edges of top pipe and 1 edge of bottom pipe
        else: 
            y_base = y_list[1][0] # 2 edges of bottom pipe and 1 edge of top pipe

    elif len(y_list) == 4:
        y_base = y_list[2][0] 



    # --- (Your existing Bird Detection code goes here) ---
    bird_mask = cv2.inRange(hsv, BEAK_LOWER, BEAK_UPPER)

    bird_cnts, _ = cv2.findContours(bird_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bird_center = None

    if bird_cnts:
        # THE FIX: Always pick the largest yellow patch found
        largest_yellow_patch = max(bird_cnts, key=cv2.contourArea)
        
        if len(largest_yellow_patch) > 0:
            x, y, w, h = cv2.boundingRect(largest_yellow_patch)
            bx = x + w // 2
            by = y + h // 2
            bx -= 5
            by -= 5
            bird_center = (bx, by)
            
            # Draw the ellipse around the CENTER of the largest yellow patch
            # Color: BGR (43, 234, 251) matches your #FBEA2B hex
            # cv2.ellipse(frame, bird_center, (BIRD_RADIUS_X, BIRD_RADIUS_Y), 0, 0, 360, (43, 234, 251), 2)

            # display all differences of by and y values with closest x values
            # cv2.putText(frame, f"Closest Pipe Edges (y): {y_list}, x_min: {x_min}", (25, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            # for y, x in y_list:
            #     cv2.putText(frame, f"by-y: {by-y}", (25, 50 + 15*y_list.index((y, x))), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # cv2.putText(frame, f"by: {by}, y_base: {y_base}", (25, 225), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

            # cv2.line(frame, (0, by), (640, by), (255, 255, 255), 2)
            # cv2.line(frame, (0, y_base), (640, y_base), (255, 255, 255), 2)


            if (time.time() - last_flap_time > 0.01):
                # display by and y_base

                # if y_base - by < 0:
                #     pydirectinput.press('space')
                #     pydirectinput.press('space')
                #     print('fast')
                #     # cv2.putText(frame, "DIVE", (25, 325), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                # if y_base - by < 0:
                #     pydirectinput.press('space')
                #     print('fast dd')

                if (y_base > y_prev and y_base - by < 23) or (y_base <= y_prev and y_base - by < 55):
                    pydirectinput.press('space')
                    print('flap')
                    last_flap_time = time.time()
                    # cv2.putText(frame, "FLAP", (25, 325), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                y_prev = y_base
                
    # draw skyline
    # cv2.line(frame, (0, SKY_Y), (640, SKY_Y), (255, 255, 255), 2)

    # cv2.imshow('Pipe Edge Tracker', frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
import cv2
import numpy as np
import json
import smtplib
import pandas as pd 
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from keras.models import load_model
from PIL import Image, ImageOps
from datetime import datetime
import time
import threading
import os
import Final_Checking
import tkinter as tk
from tkinter import messagebox

# Load models
face_model = load_model("C:\\Users\\sivav\\new_final_project\\app\\Training_Face_Images\\keras_model.h5", compile=False)
idcard_model = load_model("C:\\Users\\sivav\\new_final_project\\app\\ID_Training_Images\\keras_model.h5", compile=False)

# Load labels
face_class_names = open("C:\\Users\\sivav\\new_final_project\\app\\Training_Face_Images\\labels.txt", "r").readlines()
idcard_class_names = open("C:\\Users\\sivav\\new_final_project\\app\\ID_Training_Images\\labels.txt", "r").readlines()

# Load student details
with open("C:/Users/sivav/new_final_project/app/students.json", "r") as file:
    student_data = json.load(file)

# Email configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "projectmail2614@gmail.com"
sender_password = "xxdk kmiu gafk rdto"
admin_email = "sivavisu71@gmail.com"

# Attendance directory
attendance_directory = "C:\\Users\\sivav\\new_final_project\\app\\Attendance"
os.makedirs(attendance_directory, exist_ok=True)

# Attendance deadlines
attendance_deadline = "17:50:00"
attendance_finalline = "17:59:00"

# Global flags and trackers
deadline_crossed = False
attendance_status_tracker = {}
id_card_capture_start_time = None

# --------------------------------------------------
# Function Definitions
# --------------------------------------------------
def get_attendance_file_path():
    current_date = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(attendance_directory, f"Attendance_{current_date}.xlsx")

def log_attendance(name, roll_number, department, status):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([[current_time, name, roll_number, department, status]],
                             columns=["Timestamp", "Name", "Roll Number", "Department", "Status"])
    attendance_file = get_attendance_file_path()
    
    try:
        if os.path.exists(attendance_file):
            existing_data = pd.read_excel(attendance_file)
            if roll_number in existing_data["Roll Number"].values:
                show_popup_message(f"Attendance already logged for {name} ({roll_number})")
                return False
            updated_data = pd.concat([existing_data, new_entry], ignore_index=True)
        else:
            updated_data = new_entry
        
        updated_data.to_excel(attendance_file, index=False, engine='openpyxl')
        print(f"✅ Attendance logged for {name}")
        return True
    except Exception as e:
        print(f"⚠ Error: {e}")
        return False

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"📧 Email sent to {to_email}")
    except Exception as e:
        print(f"⚠ Email failed: {e}")

def send_admin_alert(student_name, roll_number, department, status):
    if "Absent" in status or "Late" in status:
        subject = f"Attendance Alert: {student_name} ({roll_number}) - {status}"
        body = f"""
Dear Admin,

Student attendance requires attention:

- Name: {student_name}
- Roll Number: {roll_number}
- Department: {department}
- Status: {status}

Action Required: Please verify attendance records.

Regards,
Attendance System
"""
        send_email(admin_email, subject, body)

def show_popup_message(message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Attendance System", message)
    root.destroy()

def preprocess_image(frame):
    """Convert frame to a normalized array compatible with the model."""
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
    return np.expand_dims(normalized_image_array, axis=0)

def predict_class(model, class_names, image):
    """Predict class from the model and return the class name and index."""
    prediction = model.predict(image)
    index = np.argmax(prediction)  # Get the highest confidence class index
    class_name = class_names[index].strip()
    confidence = prediction[0][index]
    return class_name, confidence, index

def check_deadline_and_finalize():
    global deadline_crossed
    while not deadline_crossed:
        current_time = datetime.now().strftime("%H:%M:%S")
        if current_time >= attendance_finalline:
            print("⏳ Finalizing attendance...")
            Final_Checking.check_attendance()
            deadline_crossed = True
            break
        time.sleep(1)

# --------------------------------------------------
# Camera and Main Logic
# --------------------------------------------------
def camera_loop():
    global deadline_crossed, id_card_capture_start_time

    cap = cv2.VideoCapture(1)
    IMAGE_SIZE = (224, 224)
    face_index = None
    idcard_index = None
    capture_stage = 0

    while not deadline_crossed:
        ret, frame = cap.read()
        if not ret:
            print("Error accessing camera.")
            break

        # Display instructions
        if capture_stage == 0:
            cv2.putText(frame, "Press SPACE to capture FACE", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        elif capture_stage == 1:
            cv2.putText(frame, "Press SPACE to capture ID CARD", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        elif capture_stage == 2:
            result_text = "Present ✅" if face_index == idcard_index else "Absent ❌"
            cv2.putText(frame, result_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Attendance System", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):
            if capture_stage == 0:
                # Capture face
                face_image = preprocess_image(frame)
                _, _, face_index = predict_class(face_model, face_class_names, face_image)
                capture_stage = 1
                id_card_capture_start_time = time.time()

            elif capture_stage == 1:
                # Capture ID card
                idcard_image = preprocess_image(frame)
                _, _, idcard_index = predict_class(idcard_model, idcard_class_names, idcard_image)
                
                if str(face_index) in student_data:
                    student = student_data[str(face_index)]
                    student_name = student["name"]
                    roll_number = student["roll_number"]
                    department = student["department"]
                    student_email = student["email"]
                    current_time = datetime.now().strftime("%H:%M:%S")

                    if roll_number in attendance_status_tracker:
                        show_popup_message("Already marked attendance!")
                        capture_stage = 0
                        continue

                    # Check if face and ID card match
                    if face_index != idcard_index:
                        show_popup_message("You are marked attendance with wrong ID card! Please recapture.")
                        capture_stage = 1  # Stay in ID capture stage
                        id_card_capture_start_time = time.time()  # Reset timeout
                        continue

                    # Only proceed if IDs match
                    attendance_status = "Present ✅" if current_time <= attendance_deadline else "Late ❌"
                    if log_attendance(student_name, roll_number, department, attendance_status):
                        attendance_status_tracker[roll_number] = True
                        send_email(student_email, "Attendance Update", f"Your status: {attendance_status}")
                        send_admin_alert(student_name, roll_number, department, attendance_status)
                        capture_stage = 2  # Show result stage

        elif key == ord('r'):  # Reset
            capture_stage = 0
            face_index = None
            idcard_index = None
            id_card_capture_start_time = None

        elif key == ord('q'):  # Immediate termination
            deadline_crossed = True
            break

        # Timeout handling (10 seconds for ID capture)
        if capture_stage == 1 and id_card_capture_start_time and (time.time() - id_card_capture_start_time > 10):
            if str(face_index) in student_data:
                student = student_data[str(face_index)]
                log_attendance(student["name"], student["roll_number"], student["department"], "Absent ❌")
                send_admin_alert(student["name"], student["roll_number"], student["department"], "Absent ❌")
            capture_stage = 0
            id_card_capture_start_time = None

    cap.release()
    cv2.destroyAllWindows()
    print("Program terminated.")

# --------------------------------------------------
# Start Execution
# --------------------------------------------------
if __name__ == "__main__":
    deadline_thread = threading.Thread(target=check_deadline_and_finalize)
    deadline_thread.daemon = True  # Ensures thread exits when main program exits
    deadline_thread.start()
    camera_loop()
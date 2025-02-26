import json
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os

# Load student details from JSON file
with open("C:/Users/sivav/new_final_project/app/students.json", "r") as file:
    student_data = json.load(file)

# Email configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "projectmail2610@gmail.com"
sender_password = "armn egas osld igfd"
admin_email = "sivavisu71@gmail.com"

# Attendance directory
attendance_directory = "C:/Users/sivav/new_final_project/app/Attendance"
os.makedirs(attendance_directory, exist_ok=True)  # Ensure the directory exists

# Attendance deadline (24-hour format)
attendance_deadline = "13:00:00"  # Example: 4:08 PM

def get_attendance_file_path():
    """Generate the attendance file path for the current date."""
    current_date = datetime.now().strftime("%Y-%m-%d")  # Format: YYYY-MM-DD
    file_name = f"Attendance_{current_date}.xlsx"
    file_path = os.path.join(attendance_directory, file_name)
    print(f"📂 Generated file path: {file_path}")  # Debugging: Print the file path
    return file_path

def send_email(to_email, subject, body):
    """Send an email to the specified recipient."""
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
        print(f"⚠ Failed to send email: {e}")

def check_attendance():
    """Check attendance for the current day and notify students on leave."""
    attendance_file = get_attendance_file_path()

    # Check if the attendance file exists
    if not os.path.exists(attendance_file):
        print(f"⚠ Attendance file not found for today: {attendance_file}")
        print(f"📂 Files in directory: {os.listdir(attendance_directory)}")  # Debugging: List files in directory
        return

    try:
        # Load attendance file for the current day
        attendance_df = pd.read_excel(attendance_file)
        print("✅ Attendance file loaded successfully.")
        # print(f"📊 Attendance records:\n{attendance_df}")  # Debugging: Print the loaded data
    except Exception as e:
        print(f"⚠ Error loading attendance file: {e}")
        return

    # Normalize roll numbers from the attendance file
    attended_students = set(attendance_df["Roll Number"].astype(str).str.strip().str.upper())

    # Extract all students from JSON (Normalize roll numbers)
    all_students = {str(info["roll_number"]).strip().upper(): info for info in student_data.values()}

    # Identify students who did NOT attend (students in JSON but NOT in attendance sheet)
    students_on_leave = {roll: info for roll, info in all_students.items() if roll not in attended_students}

    print(f"📌 Students on Leave: {len(students_on_leave)}")  # Debugging print

    if not students_on_leave:
        print("✅ No students on leave today.")
        return

    # Send emails to students on leave
    for roll_number, student_info in students_on_leave.items():
        student_name = student_info["name"]
        student_email = student_info["email"]
        
        # Professional email format for students
        subject = f"Attendance Notice: {student_name} (Leave)"
        body = f"""
Dear {student_name},

This is to inform you that your attendance status for today, {datetime.now().strftime("%Y-%m-%d")}, has been marked as **ON LEAVE**.

**Details:**
- Name: {student_name}
- Roll Number: {roll_number}
- Status: Absent ❌
- Date: {datetime.now().strftime("%Y-%m-%d")}

If this is incorrect or if you have any concerns, please contact the administration at your earliest convenience.

Regards,
Attendance System
"""
        print(f"📧 Sending leave notification to {student_name} ({roll_number})...")
        send_email(student_email, subject, body)

        # Professional email format for admin
        admin_subject = f"Admin Alert: {student_name} - On Leave"
        admin_body = f"""
Dear Admin,

This is to notify you that the following student has been marked as **ON LEAVE** today:

**Student Details:**
- Name: {student_name}
- Roll Number: {roll_number}
- Date: {datetime.now().strftime("%Y-%m-%d")}
- Status: Absent ❌

**Action Required:**
Please verify the attendance records and take necessary action if required.

Regards,
Attendance System
"""
        print(f"📧 Sending admin alert for {student_name} ({roll_number})...")
        send_email(admin_email, admin_subject, admin_body)

    print("✅ Leave check completed.")

if __name__ == "__main__":
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"⏳ Waiting for attendance deadline... Current time: {current_time}", end="\r")  # Show waiting status

        if current_time >= attendance_deadline:
            print("\n🔄 Running final attendance check...")  # Debugging print
            check_attendance()
            break  # Exit loop after running attendance check
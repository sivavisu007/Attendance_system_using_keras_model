import cv2
import numpy as np
from keras.models import load_model
from PIL import Image, ImageOps

# Load the models
face_model = load_model("C:\Users\sivav\new_final_project\app\Training_Face_Images\keras_model.h5", compile=False)
idcard_model = load_model("C:\Users\sivav\new_final_project\app\ID_Training_Images\keras_model.h5", compile=False)

# Load the class labels
face_class_names = open("C:\Users\sivav\new_final_project\app\Training_Face_Images\labels.txt", "r").readlines()
idcard_class_names = open("C:\Users\sivav\new_final_project\app\ID_Training_Images\labels.txt", "r").readlines()

# Initialize camera
cap = cv2.VideoCapture(0)  

# Image size required for the model
IMAGE_SIZE = (224, 224)

# Variables to store face and ID card results
face_class = None
idcard_class = None
capture_stage = 0  # 0 = capture face, 1 = capture ID card

def preprocess_image(frame):
    """Convert frame to a normalized array compatible with the model."""
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    image = ImageOps.fit(image, IMAGE_SIZE, Image.Resampling.LANCZOS)
    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
    return np.expand_dims(normalized_image_array, axis=0)

def predict_class(model, class_names, image):
    """Predict class from the model and return the class name and index."""
    prediction = model.predict(image)
    index = np.argmax(prediction)  # Get the highest confidence class index
    class_name = class_names[index].strip()
    confidence = prediction[0][index]
    return class_name, confidence, index  # Return class index for comparison

while True:
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

    # Show camera feed
    cv2.imshow("Attendance System", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord(' '):  # Press SPACE to capture
        if capture_stage == 0:
            # Process face image
            face_image = preprocess_image(frame)
            face_class, _, face_index = predict_class(face_model, face_class_names, face_image)
            print(f"Face detected: {face_class} (Class {face_index})")
            capture_stage = 1  # Move to next stage

        elif capture_stage == 1:
            # Process ID card image
            idcard_image = preprocess_image(frame)
            idcard_class, _, idcard_index = predict_class(idcard_model, idcard_class_names, idcard_image)
            print(f"ID Card detected: {idcard_class} (Class {idcard_index})")
            capture_stage = 2  # Move to next stage

            # Compare both class indices
            if face_index == idcard_index:
                print(f"{face_class} - Present ✅")
            else:
                print(f"{face_class} vs {idcard_class} - Absent ❌")

    elif key == ord('r'):  # Press 'R' to restart process
        face_class = None
        idcard_class = None
        capture_stage = 0
        print("Restarting process...")

    elif key == ord('q'):  # Press 'Q' to exit
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

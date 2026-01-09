Selfie-Based 3D Avatar and Virtual Try-On System

This project is a selfie-based 3D avatar generation and virtual clothing try-on system developed as a computer engineering graduation project.

The system enables users to create a personalized 3D avatar using their own selfie images and body measurements, and then visualize clothing on that avatar before making a purchase.

------------------------------------------------------------

Project Motivation

Online clothing shopping platforms often fail to provide accurate size and appearance estimation. This leads to high return rates and low user satisfaction.

The goal of this project is to reduce these problems by allowing users to generate a realistic 3D avatar based on their physical characteristics and preview how clothing items would look on their own body.

------------------------------------------------------------

System Overview

The system consists of three main components:

1. Mobile Application
2. Backend Service
3. 3D Processing Engine

Each component works independently but communicates through well-defined interfaces.

------------------------------------------------------------

Mobile Application (Flutter)

The mobile application is developed using Flutter.

Main responsibilities of the mobile application:
- User authentication using Firebase Authentication
- Collecting user body measurements
- Collecting front and side selfie images
- Sending data to the backend API
- Displaying the generated 3D avatar using a GLB viewer
- Allowing users to upload clothing images for virtual try-on

The avatar is displayed in real time using the model_viewer_plus package.

------------------------------------------------------------

Backend Service (FastAPI)

The backend service is developed using Python and FastAPI.

Main responsibilities of the backend:
- Receiving selfie images and user measurements
- Image processing using OpenCV and MediaPipe
- Estimating skin, hair and eye colors
- Managing avatar generation workflow
- Running Blender in background mode
- Uploading the generated avatar to Firebase Storage
- Storing user data in Firebase Firestore

------------------------------------------------------------

3D Processing and Avatar Generation (Blender)

Blender is used as the 3D processing engine in headless mode.

Avatar generation steps:
- A base human model is selected according to gender
- Face landmarks are extracted from the selfie image
- Hair models are attached to the head mesh
- Skin, hair and eye colors are applied
- Clothing images are applied as textures
- The final avatar is exported as a GLB file

------------------------------------------------------------

Avatar Generation Pipeline

1. User uploads front and side selfie images
2. Face landmarks and segmentation masks are extracted
3. Skin, hair and eye colors are estimated from the selfie
4. A gender-based base model is selected
5. Hair model is attached
6. Clothing texture is applied
7. Final avatar is exported and uploaded

------------------------------------------------------------

Technologies Used

Mobile Application:
- Flutter
- Dart

Backend:
- Python
- FastAPI
- OpenCV
- MediaPipe

3D Processing:
- Blender
- glTF / GLB format

Cloud Services:
- Firebase Authentication
- Firebase Firestore
- Firebase Storage

------------------------------------------------------------

Project Structure

bitirme_projesi/
flutter_app/
utils/
api.py
avatar_generator.py
blender_integration/
outputs/
blender_scripts/
build_avatar.py
base_models/
hair_models/
clothes/
README.md

------------------------------------------------------------

How to Run the Project

Backend:
python main.py

Mobile Application:
flutter pub get
flutter run

------------------------------------------------------------

Academic Note

This project was developed as a computer engineering graduation project. It demonstrates the integration of mobile application development, backend systems, computer vision techniques and 3D graphics processing.

------------------------------------------------------------

Author

Haydar Maras  
Computer Engineering Student  
Graduation Project – 2025

Intelli-Docs: AI-Powered Personal Document Assistant
 
Intelli-Docs is an innovative AI-powered system designed to simplify the management and retrieval of personal documents using Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), and image retrieval technologies. This project, submitted as part of the Bachelor of Engineering in Computer Engineering at Tribhuvan University, Purwanchal Campus, addresses challenges in traditional document management by offering secure storage, OCR-based text extraction, and intelligent search capabilities.

Table of Contents

Features
Installation
Usage
Project Report
Contributing
License
Team

Features

OCR Text Extraction: Uses Pytesseract to digitize text from scanned documents like IDs and certificates.
Image Retrieval: Leverages CLIP for visual document search and retrieval.
Intelligent Search: Implements RAG and LLMs for natural language-based document queries.
Secure Storage: Integrates Cloudinary for safe and scalable document management.
Mobile Interface: Features a Flutter-based app for user-friendly access.

Installation
Prerequisites

Python 3.8+
TensorFlow 2.10
Pytesseract
Flask
Flutter 3.x
FastAPI
Cloudinary SDK
(Optional) CUDA-enabled GPU for faster processing

Steps

Clone the repository:git clone https://github.com/your-username/intelli-docs.git


Navigate to the project directory:cd intelli-docs


Install Python dependencies:pip install -r requirements.txt


Set up Flutter environment (follow Flutter setup guide).
Configure Cloudinary credentials in config.yaml.
Run the backend:uvicorn app.main:app --reload


Launch the Flutter app:flutter run



Usage
Running the App

Start the backend server as described above.
Open the Flutter app on your device or emulator.
Upload documents (e.g., PDFs, images) and use natural language queries to retrieve information.

Example Query: Ask "Who is our deputy head of department?" to get "Asst. Prof. Pukar Karki."
Screenshots

Thumbs Up Photo: Team Celebration
ID Cards Retrieval: Sample ID Retrieval
App Interface: Main App Screen

Project Report
The full project report, submitted in March 2025, is available here. It includes detailed methodology, implementation, results, and references.
Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a feature branch:git checkout -b feature/your-feature


Commit changes:git commit -m "Add your feature"


Push to the branch:git push origin feature/your-feature


Open a Pull Request.

License
This project is licensed under the MIT License.
Team

Kritika Thapa 
Prashant Bhattarai 
Roshan Chaudhary 
Saurab Baral 

For inquiries, contact the team via the GitHub Issues page.

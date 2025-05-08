# Intelli-Docs: AI-Powered Personal Document Assistant

**Intelli-Docs** is an AI-powered system that simplifies personal document management using Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), and image retrieval. Developed for the Bachelor of Engineering in Computer Engineering at Tribhuvan University, Purwanchal Campus, this project addresses traditional document handling with OCR, intelligent search, and secure storage.

## 🚀 Features

- **OCR Text Extraction**: Extracts text from scanned images (IDs, certificates) using Pytesseract.
- **Image Retrieval**: Uses OpenAI CLIP for visual document search.
- **Intelligent Search**: Supports natural language queries via RAG + LLMs.
- **Secure Storage**: Cloudinary-backed document storage.
- **Mobile Interface**: Flutter-based mobile app for accessibility.

## 🛠 Installation

### Prerequisites

- Python 3.8+
- TensorFlow 2.10
- Flask & FastAPI
- Pytesseract
- Cloudinary SDK
- Flutter 3.x
- (Optional) CUDA-enabled GPU

### Steps

```bash
git clone https://github.com/your-username/intelli-docs.git
cd intelli-docs
pip install -r requirements.txt
```

- Set up Flutter (see [Flutter docs](https://docs.flutter.dev/get-started)).
- Add Cloudinary credentials to `config.yaml`.

### Run the App

```bash
uvicorn app.main:app --reload  # Start backend
flutter run                    # Launch Flutter app
```

## 📱 Usage

Upload documents (PDFs, images) and ask natural language questions like:

> _“Who is our deputy head of department?”_  
> ➜ _“Asst. Prof. Pukar Karki”_

## 📸 Screenshots

- ✅ Team Celebration
- 🆔 ID Card Retrieval
- 📲 App Interface

## 📄 Project Report

The complete project report (submitted March 2025) includes implementation, results, and references.

## 🤝 Contributing

```bash
# Fork and clone
git checkout -b feature/your-feature
git commit -m "Add your feature"
git push origin feature/your-feature
```

Open a Pull Request to contribute!

## 📜 License

Licensed under the [MIT License](LICENSE).

## 👥 Team

- Kritika Thapa 
- Prashant Bhattarai 
- Roshan Chaudhary  
- Saurab Baral 

_For queries, use the [GitHub Issues](https://github.com/IamPrashantBhattarai/Intelli-Docs/issues) page._


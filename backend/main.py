from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cloudinary
import cloudinary.api
import cloudinary.exceptions
import cloudinary.uploader
import os
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from pathlib import Path
from langchain_community.vectorstores import FAISS
from fastapi.responses import JSONResponse
from classificationModel import predict_category
from imageRetrievalModel import image_retrieval
from textRetrievalModel import ask_question
from freewillModel import chat_with_groq
from textRetrievalModel import CloudinaryDocumentProcessor


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("imageExtraction")

processor=CloudinaryDocumentProcessor()

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),  
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


app = FastAPI()


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path("user_content")
IMAGE_DIR = BASE_DIR / "images"
BASE_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)

def get_file_hash(file: UploadFile) -> str:
    """
    Compute the SHA‑1 hash of the file.
    """
    file.file.seek(0)
    content = file.file.read()
    file_hash = hashlib.sha1(content).hexdigest()
    file.file.seek(0)
    return file_hash

def image_exists_in_cloudinary(file: UploadFile) -> Dict[str, Any]:
    """
    Check if an image already exists in Cloudinary by computing its SHA‑1 hash
    and looking for the corresponding public_id.
    """
    file_hash = get_file_hash(file)
    public_id = file_hash  # Use the hash as the public id

    try:
        result = cloudinary.api.resource(public_id)
        return result
    except cloudinary.exceptions.NotFound:
        return None



@app.get("/api/files")
def get_all_files():
    try:
        # Fetch images (resource_type="image")
        images = cloudinary.api.resources(type="upload", resource_type="image", max_results=100)
        image_files = [
            {
                "public_id": img["public_id"],
                "url": img["secure_url"],
                "format": img.get("format", "unknown") 
            }
            for img in images.get("resources", [])
        ]

        # Fetch PDFs and text files (resource_type="raw")
        raw_files = cloudinary.api.resources(type="upload", resource_type="raw", max_results=100)
        documents = [
            {
                "public_id": doc["public_id"],
                "url": doc["secure_url"],
                "format": doc.get("format", "raw") 
            }
            for doc in raw_files.get("resources", [])
        ]

        # Combine all files
        all_files = image_files + documents

        return {"files": all_files}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        logger.info(f"Received file: {file.filename}, Type: {file.content_type}")

        # Check if file is already in Cloudinary
        file_hash = get_file_hash(file)
        existing_file = image_exists_in_cloudinary(file)

        if existing_file:
            return {
                "message": "Image already exists in Cloudinary",
                "filename": file.filename,
                "public_id": existing_file["public_id"],
                "url": existing_file["secure_url"],
                "resource_type": existing_file["resource_type"],
                "created_at": existing_file["created_at"]
            }

        file.file.seek(0)  # Reset file pointer

        # Save file locally in chunks
        local_file_path = IMAGE_DIR / f"{file_hash}_{file.filename}"
        with open(local_file_path, "wb") as f:
            for chunk in file.file:
                f.write(chunk)

        # Determine resource type
        file_format = file.filename.split(".")[-1].lower()
        resource_type = "raw" if file_format in ["pdf", "txt"] else "auto"

        # Upload file to Cloudinary
        result = cloudinary.uploader.upload(
            str(local_file_path),
            public_id=file_hash, 
            resource_type=resource_type,
            timeout=60  # Prevents long upload delays
        )

        public_id = result["public_id"]
        file_url = result["secure_url"]

        # Skip if already processed
        if public_id in processor.processed_files:
            logger.info(f"Skipping already processed file: {public_id}")
            return {"message": "File already processed", "file_url": processor.processed_files[public_id]["url"]}

        logger.info(f"Processing file: {public_id}")

        # Process file based on type
        try:
            if file_format == "pdf":
                chunks = processor._process_pdf(file_url, local_file_path)
            elif file_format == "txt":
                chunks = processor._process_txt(file_url, local_file_path)
            elif file_format in ["png", "jpg", "jpeg"]:
                chunks = processor._process_image(file_url, local_file_path)
            else:
                return {"message": f"Unsupported file type: {file_format}"}
        except Exception as e:
            logger.error(f"Error processing {file_format} file: {e}")
            return {"message": f"Error processing file: {str(e)}"}

        # Store in FAISS vector database
        if chunks:
            texts = [chunk["text"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]

            try:
                if processor.vector_store:
                    processor.vector_store.add_texts(texts=texts, metadatas=metadatas)
                else:
                    processor.vector_store = FAISS.from_texts(
                        texts=texts, embedding=processor.embeddings, metadatas=metadatas
                    )

                processor._save_vector_store()
                processor.processed_files[public_id] = {"url": file_url, "path": str(local_file_path)}
                processor._save_processed_files()
            except Exception as e:
                logger.error(f"Error updating FAISS vector store: {e}")
                return {"message": "File processed but vector store update failed."}

        return {
            "filename": file.filename,
            "public_id": public_id,
            "url": file_url,
            "resource_type": result["resource_type"],
            "message": "File uploaded and processed successfully",
            "created_at": result["created_at"]
        }

    except Exception as e:
        logger.error(f"Server error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Main API Endpoint
@app.post("/api/process-input/{key}")
async def process_input(
    key: int,
    text_prompt: Optional[str] = Form(None)
) -> Dict[str, Any]:
    try:
        logger.info(f"this is text prompt: {text_prompt}")
        logger.info(f"this is key: {key}")
        # Determine which model to use

        if key==1:
            model_type="text_retrieval"
        elif key==2:
            model_type="image_retrieval"
        elif key==3:
            model_type="freewill"
        elif key==0:
            model_type = None

        if key==0 and text_prompt:
            model_type = predict_category(text_prompt)
            logger.info(f"Predicted model type: {model_type}")

        logger.info(f"model type: {model_type}")


        # Process the input based on the model type
        if model_type == "text_retrieval":
            ask_question(text_prompt)
            return JSONResponse(content={
                "model": "text_retrieval",
                "response": ask_question(text_prompt)
            })

        elif model_type == "image_retrieval":
            # Retrieve an image based on the text prompt
            image_url = image_retrieval(text_prompt)
            return JSONResponse(content={
                "model": "image_retrieval",
                "response": image_url
            })

        elif model_type == "freewill":
            # Generate a conversational response
            response = chat_with_groq(text_prompt)
            return JSONResponse(content={
                "model": "freewill",
                "response": response
            })

        else:
            raise HTTPException(status_code=400, detail="Invalid input")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="172.20.10.8", port=3000)
import os
import json
import time
import logging
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
from pathlib import Path
from PyPDF2 import PdfReader
from typing import List, Dict, Any  
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings

from textExtractionFromImgModel import describe_image, extract_text_from_image
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),  
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


# Ensure required directories exist
BASE_DIR = Path("user_content")
IMAGE_DIR = BASE_DIR / "images"
BASE_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)

class CloudinaryDocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=200, length_function=len, add_start_index=True
        )
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self.vector_store_path = Path("vector_store/faiss_index")
        self.processed_files_path = Path("vector_store/processed_files.json")
        self.processed_files = self._load_processed_files()
        self._load_vector_store()

    def _load_processed_files(self) -> Dict[str, Any]:
        if self.processed_files_path.exists():
            with open(self.processed_files_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_processed_files(self) -> None:
        with open(self.processed_files_path, "w", encoding="utf-8") as f:
            json.dump(self.processed_files, f, indent=4)

    def _load_vector_store(self) -> None:
        if self.vector_store_path.exists():
            self.vector_store = FAISS.load_local(
                str(self.vector_store_path), self.embeddings, allow_dangerous_deserialization=True
            )

    def _save_vector_store(self) -> None:
        if self.vector_store:
            self.vector_store.save_local(str(self.vector_store_path))

    def fetch_files_from_cloudinary(self) -> List[Dict[str, Any]]:
        result = cloudinary.api.resources(type="upload", max_results=100)
        return result.get("resources", [])

    def _download_file(self, file_url: str, save_path: Path) -> bool:
        """Downloads a file from a URL and saves it locally."""
        try:
            response = requests.get(file_url, stream=True)
            if response.status_code != 200:
                logging.error(f"Failed to download file: {file_url}")
                return False

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            return True
        except Exception as e:
            logging.error(f"Error downloading file {file_url}: {e}")
            return False

    def _process_pdf(self, file_url: str, file_path: Path) -> List[Dict]:
        """Extracts text from a downloaded PDF file."""
        try:
            reader = PdfReader(str(file_path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return self._split_text(text, source=file_url)
        except Exception as e:
            logging.error(f"Error processing PDF {file_url}: {e}")
            return []

    def _process_txt(self, file_url: str, file_path: Path) -> List[Dict]:
        """Reads and processes a downloaded TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            return self._split_text(text, source=file_url)
        except Exception as e:
            logging.error(f"Error processing TXT {file_url}: {e}")
            return []

    def _process_image(self, file_url: str, file_path: Path) -> List[Dict]:
        """Processes an image file by extracting descriptions and text."""
        try:
            captions = describe_image(str(file_path))
            extracted_text = extract_text_from_image(str(file_path))
            combined_text = f"Image Description:\n{captions}\nExtracted Text:\n{extracted_text}"
            return self._split_text(combined_text, source=file_url)
        except Exception as e:
            logging.error(f"Error processing image {file_url}: {e}")
            return []

    def _split_text(self, text: str, source: str) -> List[Dict]:
        """Splits extracted text into chunks for vector storage."""
        documents = self.text_splitter.create_documents([text])
        return [{"text": doc.page_content, "metadata": {"source": source}} for doc in documents]

    def process_new_documents(self) -> None:
        """Processes new documents from Cloudinary and stores them in the vector database."""
        cloudinary_files = self.fetch_files_from_cloudinary()
        new_chunks = []

        for file in cloudinary_files:
            file_url = file["secure_url"]
            public_id = file["public_id"]
            file_format = file["format"].lower()

            if public_id in self.processed_files:
                continue  # Skip already processed files

            logging.info(f"Processing file: {public_id}")

            # Determine save location
            if file_format == "pdf":
                file_path = BASE_DIR / f"{public_id}.pdf"
            elif file_format == "txt":
                file_path = BASE_DIR / f"{public_id}.txt"
            elif file_format in ["jpg", "jpeg", "png"]:
                file_path = IMAGE_DIR / f"{public_id}.{file_format}"
            else:
                logging.info(f"Skipping unsupported file type: {file_format}")
                continue

            # Download file before processing
            if not self._download_file(file_url, file_path):
                continue

            # Process file based on its type
            if file_format == "pdf":
                chunks = self._process_pdf(file_url, file_path)
            elif file_format == "txt":
                chunks = self._process_txt(file_url, file_path)
            elif file_format in ["jpg", "jpeg", "png"]:
                chunks = self._process_image(file_url, file_path)
            else:
                continue

            new_chunks.extend(chunks)
            self.processed_files[public_id] = {"url": file_url, "path": str(file_path)}

        # Store new chunks in the vector database
        if new_chunks:
            texts = [chunk["text"] for chunk in new_chunks]
            metadatas = [chunk["metadata"] for chunk in new_chunks]

            if self.vector_store:
                self.vector_store.add_texts(texts=texts, metadatas=metadatas)
            else:
                self.vector_store = FAISS.from_texts(texts=texts, embedding=self.embeddings, metadatas=metadatas)

            self._save_vector_store()
            self._save_processed_files()
            logging.info(f"Processed {len(new_chunks)} new chunks.")

class DocumentQA:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not set.")
        self.llm = ChatGroq(
            temperature=0.1, model_name="mixtral-8x7b-32768", groq_api_key=self.groq_api_key
        )
        self.qa_chain = None

    def create_chain(self, vector_store: Any) -> None:
        if vector_store is None:
            raise ValueError("Vector store is not initialized.")
        prompt_template = (
            "You are an expert assistant with in-depth knowledge of the provided documents. "
            "Using the context below, provide the best and most detailed answer possible. "
            "If the context does not answer the question, state your uncertainty."
            "\n\nContext: {context}\nQuestion: {question}\nAnswer:"
        )
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm, chain_type="stuff", retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": prompt}, return_source_documents=True
        )

    def ask_question(self, question: str) -> Dict:
        if not self.qa_chain:
            raise ValueError("QA chain is not initialized.")

        start_time = time.time()
        result = self.qa_chain.invoke({"query": question})
        elapsed = time.time() - start_time

        sources = [doc.metadata.get("source", "unknown") for doc in result.get("source_documents", [])]
        return {"question": question, "answer": result.get("result", "No answer."), "sources": sources, "time": f"{elapsed:.2f}s"}

# Main execution
processor = CloudinaryDocumentProcessor()
processor.process_new_documents()
qa_system = DocumentQA()
qa_system.create_chain(processor.vector_store)


def ask_question(prompt: str) -> str:
    response = qa_system.ask_question(prompt)
    return response["answer"]

if __name__ == "__main__":
    prompt = "What is date of birth of bhagwati kumari?"
    answer = ask_question(prompt)
    logging.info(f"Question: {prompt}\nAnswer: {answer}")
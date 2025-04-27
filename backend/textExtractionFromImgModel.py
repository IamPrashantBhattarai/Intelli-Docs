from PIL   import Image , ImageEnhance, ImageFilter
import pytesseract  # For OCR
from transformers import BlipProcessor, BlipForConditionalGeneration
from spellchecker import SpellChecker
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def describe_image(image_path, num_captions=3):
    """Generate multiple captions for an image."""
    # Load the processor and model
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
    
    # Open and convert the image to RGB
    raw_image = Image.open(image_path).convert('RGB')

    # Process the image
    inputs = processor(raw_image, return_tensors="pt") 

    # Generate multiple captions using beam search
    outputs = model.generate(
        **inputs,
        max_length=100,              # Increase for detailed captions
        num_return_sequences=num_captions,  # Generate multiple captions
        num_beams=num_captions * 2   # Increase the beam size for diversity
    )

    # Decode each output to get the captions
    captions = [processor.decode(output, skip_special_tokens=True) for output in outputs]
    
    return captions

def preprocess_image(image_path):
    """
    Preprocess the image to improve OCR accuracy for English, Hindi, and Nepali.
    """
    # Open the image
    image = Image.open(image_path).convert('RGB')
    
    # Convert to grayscale
    image = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  # Increase contrast
    
    # Apply a slight blur to reduce noise
    image = image.filter(ImageFilter.SMOOTH)
    
    # Binarize the image (black and white)
    image = image.point(lambda x: 0 if x < 128 else 255, '1')
    
    return image

def postprocess_text(text):
    spell = SpellChecker()
    corrected_text = []
    for word in text.split():
        corrected_word = spell.correction(word) or word
        corrected_text.append(corrected_word)
    return ' '.join(corrected_text)

def extract_text_from_image(image_path):
    """
    Extract text from an image using Tesseract OCR for English, Hindi, and Nepali.
    """
    try:
        # Preprocess the image
        processed_image = preprocess_image(image_path)
        
        # Use Tesseract with custom configurations for English, Hindi, and Nepali
        custom_config = r'--oem 3 --psm 6 -l eng+hin+nep'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # check spelling
        text = postprocess_text(text)
        
        return text
    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return ""
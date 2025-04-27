from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model_path = r"C:\Users\Roshan Chaudhary\Desktop\major project\fine_tuned_model"


def predict_category(text):
    global model_path
    # Load the tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    
    # Tokenize the text
    inputs = tokenizer(text, truncation=True, padding="max_length", max_length=128, return_tensors="pt")
    
    # Move input tensors to the appropriate device (CPU/GPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    inputs = {key: value.to(device) for key, value in inputs.items()}
    
    # Run inference
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get predicted label
    logits = outputs.logits
    predicted_class = torch.argmax(logits, dim=-1).item()
    
    # Define label mapping (same as used during training)
    id2label = {0: "freewill", 1: "image_retrieval", 2: "text_retrieval"}
    
    # Get predicted category
    predicted_label = id2label[predicted_class]
    
    return predicted_label

# Example usage
# text_prompt = "what is my date of birth?"
# predicted_category = predict_category(text_prompt)
# print(f"Predicted category: {predicted_category}")

from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image
import re
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import tempfile
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize ML model
model = SentenceTransformer('all-MiniLM-L6-v2')

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# Enhanced ingredient database with eco-friendly alternatives
def create_harmful_ingredients_db():
    data = [
        ["Cocos nucifera (Coconut) Oil", "Low", "Moisturizing but may clog pores", "Jojoba oil"],
        ["Sodium Hydroxide", "Moderate", "Skin irritant in high concentrations", "Baking soda"],
        ["Fragrance", "High", "Potential allergen", "Essential oil blends"],
        ["Kojic Acid", "Moderate", "May irritate sensitive skin", "Licorice root extract"],
        ["Phenoxyethanol", "Moderate", "Preservative concerns", "Radish root ferment"],
        ["Mineral Oil", "Moderate", "Petroleum-derived", "Plant-based oils"],
        ["Talc", "High", "Asbestos contamination risk", "Arrowroot powder"],
        ["PEG-8", "Moderate", "Ethoxylated compound", "Vegetable glycerin"],
        ["BHT", "High", "Preservative with health concerns", "Rosemary extract"],
        ["Parabens", "High", "Endocrine disruptors", "Leuconostoc ferment"],
        ["SLS/SLES", "Moderate", "Harsh detergent", "Coco glucoside"]
    ]
    return pd.DataFrame(data, columns=["Ingredient", "Risk Level", "Notes", "Eco-Friendly Alternative"])

harmful_data_df = create_harmful_ingredients_db()

def extract_ingredients(ocr_text):
    """Improved ingredient extraction with OCR error handling"""
    # Normalize text
    text = re.sub(r'\s+', ' ', ocr_text.lower())
    
    # Find ingredients section
    ingredients_section = re.search(
        r'ingredients?[:\-]?\s*(.*?)(?:\s*(?:batch|mfg|exp|how to use|precautions|\*\*|$))', 
        text, 
        re.IGNORECASE
    )
    
    if not ingredients_section:
        return []
    
    # Clean and split ingredients
    ingredients_line = ingredients_section.group(1)
    ingredients_line = re.sub(r'[^a-zA-Z0-9(),\s.\-]', ' ', ingredients_line)
    
    # Handle nested parentheses and commas
    ingredients = []
    current = []
    paren_level = 0
    
    for char in ingredients_line:
        if char == '(':
            paren_level += 1
        elif char == ')':
            paren_level -= 1
            
        if char == ',' and paren_level == 0:
            ingredients.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    
    if current:
        ingredients.append(''.join(current).strip())
    
    return [i for i in ingredients if i]

@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """Endpoint for image upload and analysis"""
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image provided"}), 400
    
    # Create temp file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
    try:
        request.files['image'].save(temp_path)
        
        # OCR processing
        try:
            text = pytesseract.image_to_string(Image.open(temp_path), lang='eng')
            ingredients = extract_ingredients(text)
            
            if not ingredients:
                return jsonify({
                    "success": False,
                    "error": "No ingredients found",
                    "ocr_sample": text[:200] + "..." if text else None
                }), 400
            
            # Analyze ingredients
            product_embeddings = model.encode(ingredients)
            harmful_embeddings = model.encode(harmful_data_df['Ingredient'])
            
            similarity_matrix = cosine_similarity(product_embeddings, harmful_embeddings)
            max_scores = similarity_matrix.max(axis=1)
            max_indices = similarity_matrix.argmax(axis=1)
            
            results = []
            for i, score, idx in zip(ingredients, max_scores, max_indices):
                if score >= 0.75:  # Confidence threshold
                    harmful = harmful_data_df.iloc[idx]
                    results.append({
                        "input_ingredient": i,
                        "matched_ingredient": harmful['Ingredient'],
                        "risk_level": harmful['Risk Level'],
                        "confidence": float(score),
                        "notes": harmful['Notes'],
                        "recommendation": harmful['Eco-Friendly Alternative']
                    })
            
            return jsonify({
                "success": True,
                "data": {
                    "analysis": results,
                    "summary": {
                        "total_ingredients": len(ingredients),
                        "high_risk": len([r for r in results if r['risk_level'] == "High"]),
                        "moderate_risk": len([r for r in results if r['risk_level'] == "Moderate"])
                    },
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Processing error: {str(e)}",
                "type": type(e).__name__
            }), 500
            
    finally:
        os.close(temp_fd)
        os.unlink(temp_path)

@app.route('/api/analyze/text', methods=['POST'])
def analyze_text():
    """Endpoint for direct text analysis"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"success": False, "error": "No text provided"}), 400
    
    try:
        ingredients = extract_ingredients(data['text'])
        if not ingredients:
            return jsonify({"success": False, "error": "No ingredients found"}), 400
        
        # Same analysis logic as image endpoint
        product_embeddings = model.encode(ingredients)
        harmful_embeddings = model.encode(harmful_data_df['Ingredient'])
        
        similarity_matrix = cosine_similarity(product_embeddings, harmful_embeddings)
        max_scores = similarity_matrix.max(axis=1)
        max_indices = similarity_matrix.argmax(axis=1)
        
        results = []
        for i, score, idx in zip(ingredients, max_scores, max_indices):
            if score >= 0.75:
                harmful = harmful_data_df.iloc[idx]
                results.append({
                    "input_ingredient": i,
                    "matched_ingredient": harmful['Ingredient'],
                    "risk_level": harmful['Risk Level'],
                    "confidence": float(score),
                    "notes": harmful['Notes'],
                    "recommendation": harmful['Eco-Friendly Alternative']
                })
        
        return jsonify({
            "success": True,
            "data": {
                "analysis": results,
                "summary": {
                    "total_ingredients": len(ingredients),
                    "high_risk": len([r for r in results if r['risk_level'] == "High"]),
                    "moderate_risk": len([r for r in results if r['risk_level'] == "Moderate"])
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Analysis error: {str(e)}"
        }), 500

@app.route('/api/ingredients', methods=['GET'])
def get_ingredient_list():
    """Get list of all known ingredients"""
    return jsonify({
        "success": True,
        "data": harmful_data_df.to_dict(orient='records')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
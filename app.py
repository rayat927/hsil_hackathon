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
    ["Cocos nucifera (Coconut) Oil", "Low", "Moisturizing but may clog pores for some", "Jojoba oil or squalane"],
    ["Deionized Water", "Low", "Purified water", "Aloe vera juice (for added benefits)"],
    ["Sodium Hydroxide", "Moderate", "Can be irritating in high concentrations", "Sodium bicarbonate (baking soda)"],
    ["Fragrance", "Moderate–High", "Common allergen - exact composition unknown", "Essential oil blends (clearly labeled)"],
    ["Kojic Acid", "Moderate", "Effective brightener but can irritate sensitive skin", "Licorice root extract or alpha-arbutin"],
    ["Glycerin", "Low", "Hydrating and skin-soothing", "Vegetable-derived glycerin (already eco-friendly)"],
    ["Aqua", "Low", "Water", "Floral hydrosols (rose water, chamomile water)"],
    ["Xanthan Gum", "Low", "Thickener—generally safe", "Konjac root powder"],
    ["Caprylyl Glycol", "Low", "Moisturizer and preservative booster", "Ethylhexylglycerin (milder alternative)"],
    ["Glucose", "Low", "Moisturizer", "Honey or rice bran extract"],
    ["Chondrus crispus (Carrageenan)", "Low", "Thickener from red algae—safe", "Agar agar (from seaweed)"],
    ["Phenoxyethanol", "Low–Moderate", "Preservative—can irritate sensitive skin", "Leucidal Liquid (radish root ferment)"],
    ["Ethylhexylglycerine", "Low", "Preservative enhancer—usually non-irritating", "Rosemary extract"],
    ["Cocodiethanolamide", "Moderate", "Can be irritating in high concentrations", "Decyl glucoside"],
    ["Mineral Oil", "Moderate", "Cosmetic-grade is safe; untreated types are carcinogenic", "Jojoba oil or meadowfoam seed oil"],
    ["Melaleuca alternifolia (Tea Tree Oil)", "Moderate", "Natural antiseptic—can irritate if undiluted", "Manuka oil (Leptospermum scoparium)"],
    ["Sodium Palmate", "Low", "Common soap base ingredient, generally safe", "Olive oil-based soap"],
    ["Sodium Palm Kernelate", "Low", "Soap base derived from palm kernel oil", "Coconut oil-based soap (sustainable sourced)"],
    ["Water", "Low", "Purified water", "Aloe vera juice"],
    ["Talc", "Moderate–High", "Asbestos contamination risk", "Arrowroot powder or rice starch"],
    ["Perfume", "Moderate–High", "Fragrance; can be allergenic or irritating", "Phthalate-free essential oil blends"],
    ["Sodium Chloride", "Low", "Table salt; generally safe", "Dead sea salt (for mineral benefits)"],
    ["Titanium Dioxide", "Low–Moderate", "Safe in topical products; inhalation risk", "Non-nano zinc oxide"],
    ["Lauric Acid", "Low", "Fatty acid, used as a cleanser or emulsifier", "Caprylic acid (from coconut)"],
    ["PEG-8", "Moderate", "Humectant; may contain impurities", "Vegetable glycerin"],
    ["Polysorbate 20", "Low–Moderate", "Emulsifier; potential impurities", "Olivem 300 (from olive oil)"],
    ["Tetrasodium Etidronate", "Low", "Chelating agent; stabilizer", "Citric acid"],
    ["Milk Lipids", "Low", "Moisturizing; derived from milk", "Plant-based ceramides"],
    ["Tetrasodium EDTA", "Low–Moderate", "Chelating agent; may irritate", "Gluconolactone (from corn)"],
    ["Disodium Distyryl Biphenyl Disulfonate", "Low", "Fluorescent whitening agent", "Mica (natural mineral)"],
    ["Sericin", "Low", "Silk protein derivative; moisturizing", "Oat protein"],
    ["Rosa Gallica Flower Extract", "Low", "May cause mild irritation", "Calendula extract"],
    ["Jasminum Officinale (Jasmine) Flower Extract", "Low", "Potential allergen", "Vanilla CO2 extract"],
    ["Prunus Amygdalus Dulcis (Sweet Almond) Oil", "Low", "Safe unless allergic to nuts", "Apricot kernel oil"],
    ["Nelumbium Speciosum Flower Oil", "Low", "Generally safe", "Blue tansy oil"],
    ["Mentha Arvensis Leaf Oil", "Moderate", "Can irritate or sensitize skin", "Peppermint hydrosol"],
    ["Cymbopogon Martini Oil", "Low", "Considered safe in diluted amounts", "Geranium oil"],
    ["PEG-40 Hydrogenated Castor Oil", "Moderate", "May contain impurities", "Cetearyl glucoside"],
    ["Alpha-Isomethyl Ionone", "Moderate", "Fragrance allergen", "Naturally derived ionones"],
    ["Benzyl Salicylate", "Moderate", "Known allergen", "Willow bark extract"],
    ["Coumarin", "Moderate", "Fragrance compound; allergen", "Tonka bean extract"],
    ["Eugenol", "Moderate", "Potential irritant/allergen", "Farnesol (from chamomile)"],
    ["Hexyl Cinnamal", "Moderate", "Synthetic fragrance; allergen", "Cinnamon bark oil"],
    ["Linalool", "Moderate", "Can oxidize and cause irritation", "Lavender hydrosol"],
    ["Aqua (Water)", "Low", "Purified water", "Coconut water"],
    ["Glyceryl Palmitate", "Low-Moderate", "May cause milia", "Cetearyl olivate"],
    ["Sesamum Indicum (Sesame) Seed Oil", "Low", "Potential allergen", "Sunflower seed oil"],
    ["Coconut Alkanes", "Low", "Emollient derived from coconut", "Plant-derived squalane"],
    ["Stearate Citrate", "Low", "Emulsifying agent", "Glyceryl stearate citrate"],
    ["Cetyl Alcohol", "Low", "May be drying", "Cetearyl alcohol"],
    ["Jojoba Esters", "Low", "Wax-like emollient", "Carnauba wax"],
    ["Squalene", "Moderate", "Often shark-derived", "100% plant-derived squalane"],
    ["Helianthus Annuus (Sunflower) Seed Oil", "Low", "Non-comedogenic oil", "Grapeseed oil"],
    ["Sodium Hyaluronate", "Low", "Low-MW may irritate", "High-MW hyaluronic acid"],
    ["Malate Phosphonic Acid", "Moderate", "Chelating agent", "Phytic acid (from rice)"],
    ["Polyglycerin-3", "Low", "Humectant", "Vegetable glycerin"],
    ["Pentaerythrityl Distearate", "Moderate", "May clog pores", "Candelilla wax"],
    ["Sodium Acrylates Copolymer", "Low-Moderate", "Potential irritant", "Xanthan gum"],
    ["Methylpropanediol", "Moderate", "Penetration enhancer", "Corn-derived propanediol"],
    ["Hydrogenated Lecithin", "Low", "Emulsifier", "Sunflower lecithin"],
    ["Caprylhydroxamic Acid", "Moderate", "Preservative", "Leuconostoc ferment filtrate"],
    ["Tocopherol", "Low", "Antioxidant (Vitamin E)", "Rosemary extract"],
    ["Sorbitan Laurate", "Low", "Emulsifier", "Olivem 300"],
    ["Chlorphenesin", "Moderate-High", "Muscle relaxant", "Radish root ferment"]
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
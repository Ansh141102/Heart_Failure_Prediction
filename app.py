from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib
import os

app = Flask(__name__)

# Load Model and Scaler
MODEL_PATH = 'heart_model.pkl'
SCALER_PATH = 'scaler.pkl'
FEATURES_PATH = 'model_features.pkl'

if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH) and os.path.exists(FEATURES_PATH):
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    model_features = joblib.load(FEATURES_PATH)
    print("Model, Scaler, and Features loaded successfully.")
else:
    print("Error: Model files not found. Please run 'heart_failure_prediction.py' first.")
    model = None
    scaler = None
    model_features = None

def get_risk_factors(row):
    factors = []
    # Cholesterol
    if row.get('Cholesterol', 0) > 200:
        factors.append(f"High Cholesterol ({row['Cholesterol']} mg/dl)")
    
    # RestingBP
    if row.get('RestingBP', 0) > 140:
        factors.append(f"High BP ({row['RestingBP']} mm Hg)")
        
    # FastingBS
    if row.get('FastingBS', 0) == 1:
        factors.append("High Fasting Blood Sugar")
        
    # ExerciseAngina
    if row.get('ExerciseAngina') == 'Y':
        factors.append("Exercise Induced Angina")
        
    # Oldpeak
    if row.get('Oldpeak', 0) > 1.0:
        factors.append(f"ST Depression ({row['Oldpeak']})")
        
    # ST_Slope
    if row.get('ST_Slope') in ['Flat', 'Down']:
        factors.append(f"Abnormal ST Slope ({row['ST_Slope']})")
        
    return factors

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if not model or not scaler:
        return jsonify({'error': 'Model not loaded.'}), 500

    try:
        data = request.json
        
        # Convert input to DataFrame
        input_data = {
            'Age': float(data['Age']),
            'Sex': data['Sex'],
            'ChestPainType': data['ChestPainType'],
            'RestingBP': float(data['RestingBP']),
            'Cholesterol': float(data['Cholesterol']),
            'FastingBS': int(data['FastingBS']),
            'RestingECG': data['RestingECG'],
            'MaxHR': float(data['MaxHR']),
            'ExerciseAngina': data['ExerciseAngina'],
            'Oldpeak': float(data['Oldpeak']),
            'ST_Slope': data['ST_Slope']
        }
        
        df = pd.DataFrame([input_data])
        
        # Get Risk Factors (Before encoding)
        risk_factors = get_risk_factors(input_data)
        
        # Feature Engineering (Must match training script)
        df['Oldpeak_squared'] = df['Oldpeak'] ** 2
        df['MaxHR_Age_Ratio'] = df['MaxHR'] / df['Age']
        df['Cholesterol_Age_Ratio'] = df['Cholesterol'] / df['Age']
        df['RestingBP_Age_Ratio'] = df['RestingBP'] / df['Age']
        
        # One-Hot Encoding
        # We need to ensure the DataFrame has the exact same columns as the training data
        # First, encode categorical variables
        cat_cols = ['Sex', 'ChestPainType', 'RestingECG', 'ExerciseAngina', 'ST_Slope']
        df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
        
        # Reindex to match model features, filling missing columns with 0
        df = df.reindex(columns=model_features, fill_value=0)
        
        # Scaling
        df_scaled = scaler.transform(df)
        
        # Prediction
        prediction = model.predict(df_scaled)[0]
        probability = model.predict_proba(df_scaled)[0][1] * 100
        
        result = {
            'prediction': int(prediction),
            'probability': round(probability, 2),
            'risk_level': 'High' if probability > 50 else 'Low',
            'risk_factors': risk_factors
        }
        
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/upload', methods=['POST'])
def upload():
    if not model or not scaler:
        return jsonify({'error': 'Model not loaded.'}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        df_original = pd.read_csv(file)
        df = df_original.copy()
        
        # Calculate Risk Factors for each row
        df_original['Risk_Factors'] = df_original.apply(lambda row: get_risk_factors(row), axis=1)
        
        # Preprocessing loop for batch prediction
        # Feature Engineering
        df['Oldpeak_squared'] = df['Oldpeak'] ** 2
        df['MaxHR_Age_Ratio'] = df['MaxHR'] / df['Age']
        df['Cholesterol_Age_Ratio'] = df['Cholesterol'] / df['Age']
        df['RestingBP_Age_Ratio'] = df['RestingBP'] / df['Age']
        
        # Encoding
        cat_cols = ['Sex', 'ChestPainType', 'RestingECG', 'ExerciseAngina', 'ST_Slope']
        # Check if columns exist before encoding
        existing_cat_cols = [c for c in cat_cols if c in df.columns]
        df = pd.get_dummies(df, columns=existing_cat_cols, drop_first=True)
        
        # Reindex
        df = df.reindex(columns=model_features, fill_value=0)
        
        # Scaling
        df_scaled = scaler.transform(df)
        
        # Predictions
        predictions = model.predict(df_scaled)
        probabilities = model.predict_proba(df_scaled)[:, 1] * 100
        
        # Add results to original dataframe
        df_original['HeartFailure_Prediction'] = predictions
        df_original['Risk_Probability'] = probabilities.round(2)
        df_original['Risk_Level'] = ['High' if p > 50 else 'Low' for p in probabilities]
        
        # Convert to dictionary for JSON response
        results = df_original.to_dict(orient='records')
        
        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Use Render's assigned PORT if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

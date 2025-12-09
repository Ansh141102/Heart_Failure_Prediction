# === HEART FAILURE PREDICTION ML SCRIPT (OPTIMIZED) ===
# This script will:
# 1. Load the 'heart.csv' dataset.
# 2. Preprocess the data (Feature Engineering, Encoding, Scaling).
# 3. Tune and Train ML models (Logistic Regression, Random Forest, XGBoost, SVM).
# 4. Train an Ensemble Voting Classifier.
# 5. Generate the outputs for Table 1, Table 2, and Figure 1.
# 6. Save the trained model and scaler for the Web App.

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
import os
import joblib

# --- Dataset Details ---
DATASET_FILENAME = 'heart.csv'
FIGURE_FILENAME = 'heart_figure1.png'
MODEL_FILENAME = 'heart_model.pkl'
SCALER_FILENAME = 'scaler.pkl'

def run_analysis():
    """
    Main function to run the ML analysis.
    """
    print("Loading Heart Failure data...")
    if not os.path.exists(DATASET_FILENAME):
        print(f"Error: '{DATASET_FILENAME}' not found.")
        print("not in this directory.")
        return

    df = pd.read_csv(DATASET_FILENAME)
    print(f"Data loaded. Shape: {df.shape}")

    # === STEP 2: [OUTPUT FOR REPORT: TABLE 1] ===
    print("\n" + "="*30)
    print("OUTPUT FOR REPORT: TABLE 1")
    print("="*30)
    
    target_col = 'HeartDisease'
    
    if target_col not in df.columns:
        print(f"Error: Target column '{target_col}' not found.")
        return

    imbalance_report = df[target_col].value_counts(normalize=True) * 100
    imbalance_counts = df[target_col].value_counts()

    print("Class Balance Report:")
    try:
        no_count = imbalance_counts[0]
        has_count = imbalance_counts[1]
        no_pct = imbalance_report[0]
        has_pct = imbalance_report[1]
        print(f"Normal (0): {no_count} samples ({no_pct:.2f}%)")
        print(f"Heart Disease (1): {has_count} samples ({has_pct:.2f}%)")
    except Exception:
        print(imbalance_counts)
    print("\n--> COPY the counts and percentages above into Table 1 of your report.")
    print("="*30 + "\n")


    # === STEP 3: FEATURE ENGINEERING & PREPROCESSING ===
    print("Preprocessing data (Feature Engineering)...")

    # 1. Feature Engineering
    df['Oldpeak_squared'] = df['Oldpeak'] ** 2
    df['MaxHR_Age_Ratio'] = df['MaxHR'] / df['Age']
    df['Cholesterol_Age_Ratio'] = df['Cholesterol'] / df['Age']
    df['RestingBP_Age_Ratio'] = df['RestingBP'] / df['Age']
    
    # Separate features and target
    y = df[target_col].astype(int)
    X = df.drop(columns=[target_col])

    # 2. Encode Categorical Variables
    cat_cols = X.select_dtypes(include=['object']).columns.tolist()
    print(f"Categorical columns to encode: {cat_cols}")
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
    
    all_feature_names = X.columns.tolist()
    print(f"Using {len(all_feature_names)} features for prediction after engineering and encoding.")


    # === STEP 4: SCALING ===
    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X = pd.DataFrame(X_scaled, columns=all_feature_names)


    # === STEP 5: TRAIN-TEST SPLIT ===
    print("Splitting data into training and testing sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.2, 
        random_state=42,
        stratify=y 
    )
    print(f"Training set size: {X_train.shape[0]} samples")
    print(f"Testing set size:  {X_test.shape[0]} samples")


    # === STEP 6: TRAIN & TUNE MODELS ===
    print("Training and Tuning models... (This may take a moment)")

    # Model 1: Logistic Regression
    print("Fitting Logistic Regression...")
    model_lr = LogisticRegression(random_state=42, max_iter=2000, class_weight='balanced', C=0.1)
    model_lr.fit(X_train, y_train)

    # Model 2: Random Forest (Tuned)
    print("Tuning Random Forest...")
    rf_params = {
        'n_estimators': [100, 200, 300],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'bootstrap': [True, False]
    }
    rf_search = RandomizedSearchCV(
        RandomForestClassifier(random_state=42, class_weight='balanced'),
        param_distributions=rf_params,
        n_iter=20,
        cv=5,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    rf_search.fit(X_train, y_train)
    model_rf = rf_search.best_estimator_
    print(f"Best RF Params: {rf_search.best_params_}")

    # Model 3: XGBoost (Tuned)
    print("Tuning XGBoost...")
    scale_pos_weight = (y == 0).sum() / (y == 1).sum()
    xgb_params = {
        'n_estimators': [100, 200, 300],
        'learning_rate': [0.01, 0.05, 0.1, 0.2],
        'max_depth': [3, 5, 7, 10],
        'subsample': [0.6, 0.8, 1.0],
        'colsample_bytree': [0.6, 0.8, 1.0]
    }
    xgb_search = RandomizedSearchCV(
        XGBClassifier(
            random_state=42, 
            n_jobs=-1, 
            eval_metric='logloss',
            scale_pos_weight=scale_pos_weight,
            use_label_encoder=False
        ),
        param_distributions=xgb_params,
        n_iter=20,
        cv=5,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    xgb_search.fit(X_train, y_train)
    model_xgb = xgb_search.best_estimator_
    print(f"Best XGB Params: {xgb_search.best_params_}")

    # Model 4: SVM (Support Vector Machine)
    print("Fitting SVM...")
    model_svm = SVC(probability=True, random_state=42, class_weight='balanced', kernel='rbf', C=1.0)
    model_svm.fit(X_train, y_train)

    # Model 5: Ensemble Voting Classifier
    print("Training Ensemble Voting Classifier...")
    model_ensemble = VotingClassifier(
        estimators=[
            ('lr', model_lr),
            ('rf', model_rf),
            ('xgb', model_xgb),
            ('svm', model_svm)
        ],
        voting='soft'
    )
    model_ensemble.fit(X_train, y_train)

    print("All models trained.")


    # === STEP 7: [OUTPUT FOR REPORT: TABLE 2] ===
    print("\n" + "="*30)
    print("OUTPUT FOR REPORT: TABLE 2")
    print("="*30)

    models = {
        "Logistic Regression": model_lr,
        "Random Forest (Tuned)": model_rf,
        "XGBoost (Tuned)": model_xgb,
        "SVM": model_svm,
        "Ensemble (Voting)": model_ensemble
    }

    report_data = []

    for name, model in models.items():
        print(f"\n--- Classification Report for {name} ---")
        y_pred = model.predict(X_test)
        report = classification_report(y_test, y_pred, target_names=['Normal (0)', 'Heart Disease (1)'], output_dict=True)
        
        print(classification_report(y_test, y_pred, target_names=['Normal (0)', 'Heart Disease (1)']))
        
        report_data.append({
            "Model": name,
            "Accuracy": f"{report['accuracy'] * 100:.2f}%",
            "F1-Score (Class 0)": f"{report['Normal (0)']['f1-score']:.2f}",
            "F1-Score (Class 1)": f"{report['Heart Disease (1)']['f1-score']:.2f}",
            "Macro Avg F1-Score": f"{report['macro avg']['f1-score']:.2f}"
        })

    print("\n--> COPY THE DATA BELOW INTO Table 2 of your report:")
    print_friendly_table = pd.DataFrame(report_data).set_index('Model')
    print(print_friendly_table)
    print("="*30 + "\n")


    # === STEP 8: [OUTPUT FOR REPORT: FIGURE 1] ===
    print("\n" + "="*30)
    print("OUTPUT FOR REPORT: FIGURE 1")
    print("="*30)

    print("Generating Feature Importance plot (from Tuned Random Forest)...")

    importances = pd.DataFrame(
        data={'feature': all_feature_names, 'importance': model_rf.feature_importances_}
    ).sort_values(by='importance', ascending=False)

    print("\nTop Features:")
    print(importances)

    plt.figure(figsize=(12, 10))
    sns.barplot(
        x='importance',
        y='feature',
        data=importances,
        palette='viridis'
    )
    plt.title('Feature Importance (Tuned Random Forest)', fontsize=16)
    plt.xlabel('Importance Score', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.tight_layout()

    plt.savefig(FIGURE_FILENAME, dpi=300)

    print(f"\n--> SUCCESS: '{FIGURE_FILENAME}' has been saved.")
    print("--> This is the bar chart for Figure 1 in your report.")
    print("="*30 + "\n")

    # === STEP 9: SAVE MODEL FOR WEB APP ===
    print("Saving model and scaler for Web App...")
    joblib.dump(model_ensemble, MODEL_FILENAME)
    joblib.dump(scaler, SCALER_FILENAME)
    # Also save the feature columns to ensure alignment during inference
    joblib.dump(all_feature_names, 'model_features.pkl')
    print(f"Model saved to '{MODEL_FILENAME}'")
    print(f"Scaler saved to '{SCALER_FILENAME}'")
    print(f"Feature names saved to 'model_features.pkl'")

    print("=== SCRIPT FINISHED ===")


if __name__ == "__main__":
    run_analysis()

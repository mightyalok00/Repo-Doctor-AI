"""
Data processing and model training pipeline with intentional ML anti-patterns for demonstration.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


def load_and_preprocess_data():
    # Generate synthetic classification dataset
    np.random.seed(42)
    X = np.random.randn(200, 5)
    y = np.random.randint(0, 2, size=200)

    # ANTI-PATTERN 1 (DATA LEAKAGE): Fitting scaler on full dataset BEFORE splitting
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # ANTI-PATTERN 2: Missing random_state & stratify in train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y)

    return X_train, X_test, y_train, y_test


def run_experiment():
    X_train, X_test, y_train, y_test = load_and_preprocess_data()

    # ANTI-PATTERN 3: Missing random_state in stochastic estimator
    clf = RandomForestClassifier(n_estimators=50)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    return acc

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.operational_intelligence import student_rows

MODEL_VERSION = 'sklearn-v1'
FEATURE_COLUMNS = [
    'attendance_rate',
    'assignment_completion',
    'engagement_score',
    'overall_score',
    'missing_assignments',
    'late_submissions',
    'risk_score',
]


class ConstantBinaryModel:
    def __init__(self, probability: float):
        self.probability = probability

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        negative = 1 - self.probability
        return np.array([[negative, self.probability] for _ in range(len(X))])


class ConstantRegressor:
    def __init__(self, value: float):
        self.value = value

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.array([self.value for _ in range(len(X))])


def model_status(db: Session) -> dict[str, Any]:
    rows = student_rows(db)
    artifacts = {
        name: {
            'path': str(_model_path(name)),
            'exists': _model_path(name).exists(),
        }
        for name in ['attendance_risk', 'performance_forecast', 'risk_classifier']
    }
    return {
        'model_version': MODEL_VERSION,
        'training_rows_available': len(rows),
        'storage_dir': str(_model_dir()),
        'artifacts': artifacts,
        'can_retrain': len(rows) > 0,
    }


def retrain_models(db: Session) -> dict[str, Any]:
    rows = student_rows(db)
    if not rows:
        return {
            'status': 'insufficient_data',
            'model_version': MODEL_VERSION,
            'message': 'No active student records are available for training.',
            'artifacts': {},
        }

    dataset = _training_frame(rows)
    X = dataset[FEATURE_COLUMNS]
    results = {
        'attendance_risk': _train_attendance_model(X, dataset),
        'performance_forecast': _train_performance_model(X, dataset),
        'risk_classifier': _train_risk_model(X, dataset),
    }
    return {
        'status': 'completed',
        'model_version': MODEL_VERSION,
        'training_rows': len(dataset),
        'source_students': len(rows),
        'artifacts': results,
    }


def attendance_model_probabilities(db: Session) -> dict[str, float]:
    artifact = _load_model('attendance_risk')
    if not artifact:
        return {}
    probabilities: dict[str, float] = {}
    for row in student_rows(db):
        features = _features_from_row(row)
        probability = artifact['model'].predict_proba(pd.DataFrame([features]))[0][1]
        probabilities[row['registration_number']] = round(float(probability) * 100, 1)
    return probabilities


def performance_model_scores(db: Session) -> dict[str, float]:
    artifact = _load_model('performance_forecast')
    if not artifact:
        return {}
    scores: dict[str, float] = {}
    for row in student_rows(db):
        features = _features_from_row(row)
        score = artifact['model'].predict(pd.DataFrame([features]))[0]
        scores[row['registration_number']] = round(float(np.clip(score, 0, 100)), 1)
    return scores


def _training_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    base = pd.DataFrame([_features_from_row(row) | {'registration_number': row['registration_number']} for row in rows])
    augmented = [base]
    for delta in [-8, -4, 4, 8]:
        shifted = base.copy()
        shifted['attendance_rate'] = np.clip(shifted['attendance_rate'] + delta, 0, 100)
        shifted['assignment_completion'] = np.clip(shifted['assignment_completion'] + delta / 2, 0, 100)
        shifted['engagement_score'] = np.clip(shifted['engagement_score'] + delta / 2, 0, 100)
        shifted['overall_score'] = np.clip(
            shifted['attendance_rate'] * 0.4 + shifted['assignment_completion'] * 0.4 + shifted['engagement_score'] * 0.2,
            0,
            100,
        )
        shifted['risk_score'] = np.clip(100 - shifted['overall_score'] + shifted['missing_assignments'] * 8, 0, 100)
        augmented.append(shifted)

    dataset = pd.concat(augmented, ignore_index=True)
    dataset['attendance_risk_label'] = (
        (dataset['attendance_rate'] < 75)
        | (dataset['risk_score'] >= 45)
        | (dataset['missing_assignments'] >= 2)
    ).astype(int)
    dataset['predicted_final_score'] = np.clip(
        dataset['overall_score']
        + np.where(dataset['attendance_rate'] >= 85, 4, -4)
        - dataset['missing_assignments'] * 2.5
        - dataset['late_submissions'] * 1.2,
        0,
        100,
    )
    dataset['risk_class'] = np.select(
        [dataset['risk_score'] >= 75, dataset['risk_score'] >= 45, dataset['risk_score'] >= 20],
        ['Critical', 'High', 'Medium'],
        default='Low',
    )
    return dataset


def _features_from_row(row: dict[str, Any]) -> dict[str, float]:
    return {
        'attendance_rate': float(row['attendance_rate']),
        'assignment_completion': float(row['assignment_completion']),
        'engagement_score': float(row['engagement_score']),
        'overall_score': float(row['overall_score']),
        'missing_assignments': float(row['missing_assignments']),
        'late_submissions': float(row['late_submissions']),
        'risk_score': float(row['risk_score']),
    }


def _train_attendance_model(X: pd.DataFrame, dataset: pd.DataFrame) -> dict[str, Any]:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    y = dataset['attendance_risk_label']
    if y.nunique() < 2:
        model = ConstantBinaryModel(float(y.iloc[0]))
        return _save_model('attendance_risk', model, {'training_accuracy': 1.0, 'constant_model': True})
    model = RandomForestClassifier(n_estimators=80, random_state=42, class_weight='balanced')
    model.fit(X, y)
    accuracy = accuracy_score(y, model.predict(X))
    return _save_model('attendance_risk', model, {'training_accuracy': round(float(accuracy), 3)})


def _train_performance_model(X: pd.DataFrame, dataset: pd.DataFrame) -> dict[str, Any]:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error

    y = dataset['predicted_final_score']
    if y.nunique() < 2:
        model = ConstantRegressor(float(y.iloc[0]))
        return _save_model('performance_forecast', model, {'mean_absolute_error': 0.0, 'constant_model': True})
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    mae = mean_absolute_error(y, model.predict(X))
    return _save_model('performance_forecast', model, {'mean_absolute_error': round(float(mae), 3)})


def _train_risk_model(X: pd.DataFrame, dataset: pd.DataFrame) -> dict[str, Any]:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    y = dataset['risk_class']
    model = RandomForestClassifier(n_estimators=80, random_state=42, class_weight='balanced')
    model.fit(X, y)
    accuracy = accuracy_score(y, model.predict(X))
    return _save_model('risk_classifier', model, {'training_accuracy': round(float(accuracy), 3)})


def _model_dir() -> Path:
    path = Path(settings.ai_storage_dir) / 'models'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _model_path(name: str) -> Path:
    return _model_dir() / f'{name}.pkl'


def _save_model(name: str, model: Any, metrics: dict[str, Any]) -> dict[str, Any]:
    path = _model_path(name)
    payload = {
        'model_version': MODEL_VERSION,
        'feature_columns': FEATURE_COLUMNS,
        'model': model,
        'metrics': metrics,
    }
    with path.open('wb') as handle:
        pickle.dump(payload, handle)
    return {'path': str(path), 'model_version': MODEL_VERSION, 'metrics': metrics}


def _load_model(name: str) -> dict[str, Any] | None:
    path = _model_path(name)
    if not path.exists():
        return None
    with path.open('rb') as handle:
        return pickle.load(handle)

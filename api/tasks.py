# api/tasks.py
import pandas as pd
import numpy as np
from celery import shared_task
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from .models import FeatureSelectionJob

# Ruta al archivo CSV. Súbelo a la raíz de este nuevo proyecto.
DATA_FILE_PATH = 'TotalFeatures-ISCXFlowMeter.csv'

def load_and_split_data():
    """Carga y prepara los datos solo para clasificación."""
    try:
        df = pd.read_csv(DATA_FILE_PATH)
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró {DATA_FILE_PATH}. "
                               f"Asegúrate de subirlo a la raíz del proyecto.")
    
    # Factorizar la variable 'calss' (como en la celda 14 del notebook)
    df_copy = df.copy()
    y_classification = df_copy['calss'].factorize()[0]
    
    # Quitamos solo 'calss'. Dejamos 'duration' como una característica más.
    X = df_copy.drop('calss', axis=1, errors='ignore')

    # División (celda 17)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y_classification, test_size=0.4, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42
    )
    
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
    }

def feature_selection_logic(user_params, top_n, data):
    """
    Lógica principal del notebook de selección de características.
    """
    X_train = data['X_train']
    y_train = data['y_train']
    X_val = data['X_val']
    y_val = data['y_val']
    
    # Parámetros (basado en celda 19 del notebook)
    default_params = {'n_estimators': 50, 'random_state': 42, 'n_jobs': -1}
    final_params = {**default_params, **user_params}
    
    # --- Modelo Completo ---
    clf_full = RandomForestClassifier(**final_params)
    clf_full.fit(X_train, y_train)
    
    y_pred_full = clf_full.predict(X_val)
    f1_full = f1_score(y_val, y_pred_full, average='weighted')
    
    # --- Selección de Características ---
    importances = clf_full.feature_importances_
    feature_names = list(X_train.columns)
    feature_series = pd.Series(importances, index=feature_names).sort_values(ascending=False)
    
    top_features_list = list(feature_series.head(top_n).index)
    
    # --- Modelo Reducido ---
    X_train_reduced = X_train[top_features_list]
    X_val_reduced = X_val[top_features_list]
    
    clf_reduced = RandomForestClassifier(**final_params)
    clf_reduced.fit(X_train_reduced, y_train)
    
    y_pred_reduced = clf_reduced.predict(X_val_reduced)
    f1_reduced = f1_score(y_val, y_pred_reduced, average='weighted')
    
    # --- Resultados ---
    return {
        "full_model_f1_score": f1_full,
        "reduced_model_f1_score": f1_reduced,
        "f1_difference_percentage": ((f1_full - f1_reduced) / f1_full) * 100,
        "total_features_evaluated": len(feature_names),
        "features_selected_count": top_n,
        "top_features_list": top_features_list
    }

@shared_task
def run_feature_selection_job(job_id):
    """ Tarea de Celery que ejecuta la lógica. """
    try:
        job = FeatureSelectionJob.objects.get(id=job_id)
        job.status = FeatureSelectionJob.Status.RUNNING
        job.save()

        data = load_and_split_data()
        
        metrics = feature_selection_logic(
            job.model_params,
            job.top_n_features,
            data
        )
        
        job.results = metrics
        job.status = FeatureSelectionJob.Status.COMPLETE
        job.save()
    except Exception as e:
        job.status = FeatureSelectionJob.Status.FAILED
        job.error_message = str(e)
        job.save()
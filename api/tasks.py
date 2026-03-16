import pandas as pd
import numpy as np
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

from celery import shared_task
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import MinMaxScaler
from sklearn import metrics
from sklearn.metrics import f1_score, silhouette_score, calinski_harabasz_score
from sklearn.metrics.cluster import contingency_matrix
from .models import FeatureSelectionJob

DATA_FILE_PATH = 'creditcard.csv'

# --- Funciones Auxiliares para Graficar (K-Means) ---
def plot_data(X, y):
    plt.plot(X[:, 0][y == 0], X[:, 1][y == 0], 'k.', markersize=2)
    plt.plot(X[:, 0][y == 1], X[:, 1][y == 1], 'r.', markersize=2)

def plot_centroids(centroids, weights=None, circle_color='w', cross_color='k'):
    if weights is not None:
        centroids = centroids[weights > weights.max() / 10]
    plt.scatter(centroids[:, 0], centroids[:, 1], marker='o', s=30, linewidths=8, 
                color=circle_color, zorder=10, alpha=0.9)
    plt.scatter(centroids[:, 0], centroids[:, 1], marker='x', s=30, linewidths=2, 
                color=cross_color, zorder=11)

def plot_decision_boundaries(clusterer, X, y, resolution=1000, show_centroids=True):
    mins = X.min(axis=0) - 0.1
    maxs = X.max(axis=0) + 0.1
    
    xx, yy = np.meshgrid(np.linspace(mins[0], maxs[0], resolution),
                         np.linspace(mins[1], maxs[1], resolution))
    
    Z = clusterer.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    plt.contourf(Z, extent=(mins[0], maxs[0], mins[1], maxs[1]), cmap="Pastel2")
    plt.contour(Z, extent=(mins[0], maxs[0], mins[1], maxs[1]), colors='k', linewidths=1)

    plot_data(X, y)
    
    if show_centroids:
        plot_centroids(clusterer.cluster_centers_)

# --- Utilidades ---
def load_data_raw():
    try:
        return pd.read_csv(DATA_FILE_PATH)
    except FileNotFoundError:
        raise FileNotFoundError(f"Falta {DATA_FILE_PATH}")

def plot_to_base64(plt_figure):
    buf = io.BytesIO()
    plt_figure.savefig(buf, format='png', bbox_inches='tight')
    plt_figure.close()
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

def purity_score(y_true, y_pred):
    c_matrix = contingency_matrix(y_true, y_pred)
    return np.sum(np.amax(c_matrix, axis=0)) / np.sum(c_matrix)

# --- Lógica 1: Random Forest ---
def run_rf_logic(df, user_params, top_n):
    X = df.drop('Class', axis=1)
    y = df['Class']
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.4, random_state=42, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)
    
    defaults = {'n_estimators': 50, 'random_state': 42, 'n_jobs': -1}
    params = {**defaults, **user_params}
    
    clf = RandomForestClassifier(**params)
    clf.fit(X_train, y_train)
    f1_full = f1_score(y_val, clf.predict(X_val), average='weighted')
    
    importances = clf.feature_importances_
    feats = pd.Series(importances, index=X_train.columns).sort_values(ascending=False)
    top_feats = feats.head(top_n).to_dict()
    
    top_cols = list(top_feats.keys())
    clf_red = RandomForestClassifier(**params)
    clf_red.fit(X_train[top_cols], y_train)
    f1_red = f1_score(y_val, clf_red.predict(X_val[top_cols]), average='weighted')
    
    return {
        "F1 Score (Full)": f1_full,
        "F1 Score (Reduced)": f1_red,
        "Feature Importances": top_feats
    }

# --- Lógica 2: K-Means (CORREGIDA) ---
def run_kmeans_logic(df, user_params):
    cols_drop = ['Class', 'Time', 'Amount']
    X_high = df.drop([c for c in cols_drop if c in df.columns], axis=1)
    y = df['Class']
    
    k = user_params.get('n_clusters', 5)
    
    # --- CAMBIO 1: Leer Ejes Dinámicos ---
    fx = user_params.get('feature_x', 'V10')
    fy = user_params.get('feature_y', 'V14')
    
    kmeans_high = KMeans(n_clusters=k, random_state=42)
    clusters_high = kmeans_high.fit_predict(X_high)
    
    results = {
        "Purity Score": purity_score(y, clusters_high),
        "Silhouette Score": metrics.silhouette_score(X_high, clusters_high, sample_size=10000),
        "Calinski-Harabasz": metrics.calinski_harabasz_score(X_high, clusters_high)
    }

    counter = Counter(clusters_high.tolist())
    # Contamos cuántos de cada cluster son fraudulentos (y == 1)
    bad_counter = Counter(clusters_high[y == 1].tolist())
    
    cluster_report = {}
    for key in sorted(counter.keys()):
        # Creamos el string exacto que pediste
        msg = f"{counter[key]} samples - {bad_counter[key]} are malicious samples"
        label_name = f"Label {key}"
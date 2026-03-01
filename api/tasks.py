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

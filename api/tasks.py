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
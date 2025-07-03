import os
import csv
from datetime import datetime

import pandas as pd
import numpy as np
import pickle
from flask import Flask, render_template, request, redirect, url_for, session, send_file

# Load model
with open('reorder_rf_model.pkl', 'rb') as file:
    model = pickle.load(file)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # In production, use a secure random key

# --- Dummy Admin Credentials ---
USERNAME = 'admin'
PASSWORD = 'password123'

# --- ROUTES ---

# Home → Form Page
@app.route('/')
def home():
    return render_template('index.html')


# Predict Route
@app.route('/predict', methods=['POST'])
def predict():
    try:
        item = request.form['Item_Name']
        opening = int(request.form['Opening_Stock_Qty'])
        closing = int(request.form['Closing_Stock_Qty'])
        replenished = int(request.form['Stock_Replenished'])

        input_data = pd.DataFrame([[opening, closing, replenished]],
                                  columns=['Opening_Stock_Qty', 'Closing_Stock_Qty', 'Stock_Replenished'])
        prediction = model.predict(input_data)[0]
        result = "YES" if prediction == 1 else "NO"

        # Log to CSV
        log_file = '/tmp/prediction_logs.csv'
        log_headers = ['Timestamp', 'Item_Name', 'Opening_Stock_Qty', 'Closing_Stock_Qty', 'Stock_Replenished', 'Prediction']
        log_row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            item, opening, closing, replenished, result
        ]

        file_exists = os.path.isfile(log_file)
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(log_headers)
            writer.writerow(log_row)

        return render_template('result.html',
                               prediction=result,
                               item=item,
                               opening=opening,
                               closing=closing,
                               replenished=replenished)
    except Exception as e:
        return render_template('result.html',
                               prediction=f"Error: {e}",
                               item="(Unknown)",
                               opening=None,
                               closing=None,
                               replenished=None)


# Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if user == USERNAME and pwd == PASSWORD:
            session['logged_in'] = True
            return redirect('/admin')
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')


# Admin Dashboard (protected)
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect('/login')

    log_file = '/tmp/prediction_logs.csv'
    if not os.path.exists(log_file):
        return render_template('admin.html', logs=[])

    df = pd.read_csv(log_file)
    return render_template('admin.html', logs=df.to_dict(orient='records'))


# Download CSV
@app.route('/download-log')
def download_log():
    log_file = '/tmp/prediction_logs.csv'
    if os.path.exists(log_file):
        return send_file(log_file, as_attachment=True)
    else:
        return "<h3>No log file available yet.</h3>", 404


# DO NOT include app.run() — handled by gunicorn in Render

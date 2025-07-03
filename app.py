import os
import csv
from datetime import datetime

import pandas as pd
import numpy as np
import pickle
from flask import Flask, render_template, request, redirect, url_for, session
from flask import send_file  # Already used for download


# Load model
with open('reorder_rf_model.pkl', 'rb') as file:
    model = pickle.load(file)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Use a strong random key in production


# Home route → form page
@app.route('/')
def home():
    return render_template('index.html')

# Predict route → handles form submission
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

        # ✅ Step: Log to CSV (correctly indented)
        log_file = '/tmp/prediction_logs.csv'
        log_headers = ['Timestamp', 'Item_Name', 'Opening_Stock_Qty', 'Closing_Stock_Qty', 'Stock_Replenished', 'Prediction']

        log_row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            item,
            opening,
            closing,
            replenished,
            result
        ]

        file_exists = os.path.isfile(log_file)

        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(log_headers)
            writer.writerow(log_row)

        # ✅ Now render the result page
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
    except Exception as e:
        return render_template('result.html',
                               prediction=f"Error: {e}",
                               item="(Unknown)",
                               opening=None,
                               closing=None,
                               replenished=None)

@app.route('/download-log')
def download_log():
    log_path = '/tmp/prediction_logs.csv'
    if os.path.exists(log_path):
        return send_file(
            log_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='prediction_logs.csv'
        )
    else:
        return "<h3>No log file available yet.</h3>", 404

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect('/login')  # Redirect to login if not logged in

    log_file = '/tmp/prediction_logs.csv'
    if not os.path.exists(log_file):
        return render_template('admin.html', logs=[])
    
    df = pd.read_csv(log_file)
    return render_template('admin.html', logs=df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

# --- Simple Login System ---

# Dummy credentials (you can replace with more secure logic later)
USERNAME = 'admin'
PASSWORD = 'password123'

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

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

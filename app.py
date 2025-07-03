import os
import csv
from datetime import datetime

import pandas as pd
import numpy as np
import pickle
from flask import Flask, render_template, request, send_file

# Load model
with open('reorder_rf_model.pkl', 'rb') as file:
    model = pickle.load(file)

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


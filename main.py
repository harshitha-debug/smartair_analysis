from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

class PollutionPredictor:
    def __init__(self):
        self.models = {}
        self.train_models()
    
    def generate_realistic_data(self):
        data = []
        base_pollution = {'mumbai': 80, 'delhi': 150}
        seasonal_factors = {
            1: 1.4, 2: 1.3, 3: 1.2, 4: 1.1, 5: 1.0, 6: 0.9,
            7: 0.8, 8: 0.8, 9: 0.9, 10: 1.1, 11: 1.3, 12: 1.4
        }
        
        for city in ['mumbai', 'delhi']:
            for year in range(2021, 2029):
                for month in range(1, 13):
                    base_value = base_pollution[city]
                    year_factor = 1 - (year - 2021) * 0.02
                    monthly_factor = seasonal_factors[month]
                    noise = random.uniform(-10, 10)
                    pollution = base_value * year_factor * monthly_factor + noise
                    
                    if city == 'mumbai':
                        pollution = max(40, min(180, pollution))
                    else:
                        pollution = max(80, min(400, pollution))
                    
                    for day in range(1, 29):
                        daily_factor = 1 + (day % 7) * 0.1
                        daily_pollution = pollution * daily_factor + random.uniform(-15, 15)
                        
                        for hour in range(24):
                            if hour in [8, 9, 17, 18]:
                                hourly_factor = 1.3
                            elif hour in [0, 1, 2, 3, 4, 5]:
                                hourly_factor = 0.7
                            else:
                                hourly_factor = 1.0
                                
                            hourly_pollution = daily_pollution * hourly_factor + random.uniform(-10, 10)
                            
                            data.append({
                                'city': city,
                                'year': year,
                                'month': month,
                                'day': day,
                                'hour': hour,
                                'pollution': max(20, hourly_pollution),
                                'temperature': random.uniform(15, 35),
                                'humidity': random.uniform(40, 90),
                                'wind_speed': random.uniform(5, 25),
                                'industrial_index': random.uniform(0.5, 1.5),
                                'traffic_index': random.uniform(0.5, 1.5)
                            })
        
        return pd.DataFrame(data)
    
    def train_models(self):
        print("Training ML models for pollution prediction...")
        df = self.generate_realistic_data()
        
        for city in ['mumbai', 'delhi']:
            city_data = df[df['city'] == city].copy()
            features = ['year', 'month', 'day', 'hour', 'temperature', 'humidity', 'wind_speed', 'industrial_index', 'traffic_index']
            X = city_data[features]
            y = city_data['pollution']
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            
            self.models[city] = {
                'model': model,
                'features': features,
                'accuracy': r2
            }
            print(f"{city.capitalize()} Model - R²: {r2:.4f}")

predictor = PollutionPredictor()

@app.route('/api/predict', methods=['POST'])
def predict_pollution():
    try:
        data = request.get_json()
        city = data.get('city', 'mumbai')
        analysis_type = data.get('analysis_type', 'yearly')
        year = data.get('year', 2024)
        month = data.get('month', 1)
        day = data.get('day', 1)
        
        if city not in predictor.models:
            return jsonify({'error': f'No model for {city}'}), 400
        
        model_info = predictor.models[city]
        predictions = []
        
        if analysis_type == 'yearly':
            for y in range(2021, 2029):
                features = [y, 6, 15, 12, 30, 65, 15, 1.0, 1.0]
                X_pred = np.array([features])
                pollution = model_info['model'].predict(X_pred)[0]
                predictions.append({
                    'year': y,
                    'without_sol_gel': round(pollution, 1),
                    'with_sol_gel': round(pollution * 0.7, 1)
                })
                
        elif analysis_type == 'monthly':
            for m in range(1, 13):
                temp = 25 + (m - 6) * 2
                humidity = 60 + (m - 6) * 5
                features = [year, m, 15, 12, temp, humidity, 15, 1.0, 1.0]
                X_pred = np.array([features])
                pollution = model_info['model'].predict(X_pred)[0]
                predictions.append({
                    'month': m,
                    'without_sol_gel': round(pollution, 1),
                    'with_sol_gel': round(pollution * 0.7, 1)
                })
                
        elif analysis_type == 'daily':
            for d in range(1, 31):
                traffic_idx = 1.0 + (d % 7) * 0.1
                features = [year, month, d, 12, 28, 65, 15, 1.0, traffic_idx]
                X_pred = np.array([features])
                pollution = model_info['model'].predict(X_pred)[0]
                predictions.append({
                    'day': d,
                    'without_sol_gel': round(pollution, 1),
                    'with_sol_gel': round(pollution * 0.7, 1)
                })
                
        elif analysis_type == 'hourly':
            for h in range(24):
                if h in [8, 9, 17, 18]:
                    traffic_idx = 1.5
                    industrial_idx = 1.2
                elif h in [0, 1, 2, 3, 4, 5]:
                    traffic_idx = 0.5
                    industrial_idx = 0.8
                else:
                    traffic_idx = 1.0
                    industrial_idx = 1.0
                
                temp = 20 + (h - 4) * 1.5 if h >= 4 else 20
                humidity = 70 - (h - 6) * 2 if h >= 6 else 70
                features = [year, month, day, h, temp, humidity, 15, industrial_idx, traffic_idx]
                X_pred = np.array([features])
                pollution = model_info['model'].predict(X_pred)[0]
                predictions.append({
                    'hour': h,
                    'without_sol_gel': round(pollution, 1),
                    'with_sol_gel': round(pollution * 0.7, 1)
                })
        
        current_pollution = predictions[-1]['without_sol_gel'] if predictions else 0
        reduced_pollution = predictions[-1]['with_sol_gel'] if predictions else 0
        
        response = {
            'predictions': predictions,
            'current_pollution': current_pollution,
            'reduced_pollution': reduced_pollution,
            'reduction_percent': "30%",
            'model_accuracy': f"{model_info['accuracy']*100:.1f}%",
            'city': city,
            'analysis_type': analysis_type
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        response = {
            'response': "You can chat with our AI assistant using the Chatbase interface below.",
            'chatbase_url': "https://www.chatbase.co/chatbot-iframe/eMCzsWfY19R61-GpXi8LY",
            'type': 'external_chatbot'
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'response': "I'm having trouble connecting to the chatbot. Please try again.",
            'type': 'error'
        })

@app.route('/api/alerts/trigger', methods=['POST'])
def trigger_immediate_alert():
    """Trigger immediate alert check"""
    try:
        print("🚨 Alert trigger received - Sending emails...")
        
        from email_alerts import send_immediate_alerts
        send_immediate_alerts()
        
        return jsonify({
            'status': 'success',
            'message': 'Pollution alerts sent to all subscribed users!'
        })
        
    except Exception as e:
        print(f"❌ Error in trigger_immediate_alert: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_frontend():
    return """
    <html>
    <body>
        <h1>SmartAir Backend is Running!</h1>
        <p>Backend server is running on port 5000</p>
        <p>Use your frontend HTML file to access the application</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("🚀 SmartAir Backend Server Starting...")
    print("📍 Endpoints:")
    print("   POST /api/predict - Get pollution predictions") 
    print("   POST /api/chatbot - AI assistant (Chatbase)")
    print("   POST /api/alerts/trigger - Send immediate alerts")
    print("   GET  / - Health check")
    print("🔮 Models trained and ready!")
    app.run(debug=True, host='0.0.0.0', port=5000)
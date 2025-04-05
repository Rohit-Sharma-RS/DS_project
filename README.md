# 🏏 Cricket Match Predictor

## 📌 Overview
Cricket is often considered unpredictable, but with data-driven insights, we can bring precision to match outcome predictions. This **Cricket Match Predictor** leverages **ELO ratings, recent form, and ensemble modeling** to deliver highly accurate predictions.

This project is an **end-to-end solo-built application** that analyzes every ball faced or bowled, dynamically updating player ELOs based on performance. It also incorporates venue, team, and player analytics alongside a robust chatroom for discussions.

## 🎯 Key Features
- **Ball-by-Ball Player Analysis**: Unlike traditional models, this system assigns dynamic **ELO ratings** to every player based on performance.
- **Form-Weighted Predictions**: Takes into account **recent player form** for more realistic insights.
- **Hybrid Ensemble Model**: Uses **XGBoost, Logistic Regression** for robust, high-accuracy predictions.
- **Venue, Team & Player Analyzer**: Provides deep insights into match conditions.
- **Real-Time Chatroom**: Engage in discussions and analysis with other users.

## 🛠️ Tech Stack
### **Backend & API**
- **FastAPI** – High-performance API for serving predictions
- **PostgreSQL** – Optimized data storage for historical insights
- **Cloud Deployment** – Hosted for real-world accessibility on render

### **Machine Learning & Data Processing**
- **Pandas & NumPy** – Data preprocessing & feature engineering
- **Scikit-Learn & XGBoost** – Core machine learning models

## 📂 Repository Structure
```
📦 Cricket-Match-Predictor
│── 📁 app/                 # Main application backend
│── 📁 logs/                # Logging & error tracking
│── 📁 notebook/            # ML model training notebooks (partially available)
│── 📁 src/                 
│── 📄 main.py              # Entry point for FastAPI app
│── 📄 requirements.txt     # Dependencies
│── 📄 setup.py             # Package setup
│── 📄 test.py              # Unit tests
│── 📄 ipl_predictor.db     # Database for match insights
```

## 🚀 Getting Started
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/your-username/cricket-match-predictor.git
cd DS_project
```

### **2️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3️⃣ Run the API**
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`

### **4️⃣ Model Training (Optional)**
Run the provided Jupyter notebooks in the `notebook/` folder for further analysis it is a partial notebook and not the entire notebook was uploaded.

## 🎯 Future Enhancements
- ✅ Live match predictions with real-time data updates
- ✅ Enhanced UI for better user experience
- ✅ More advanced deep learning techniques

📢 **Feedback and contributions are welcome!** Feel free to fork the repo and improve it. Let's revolutionize **Cricket Analytics** together! 🚀

#CricketAnalytics #MachineLearning #FastAPI #SportsTech


NetGuard AI

NetGuard AI is a full-stack, machine-learning-powered network intrusion and anomaly detection platform built with Python and Flask.

The project allows users to upload network-security datasets, train a machine learning model, analyze network activity, detect potential attacks, calculate risk scores, generate alerts, view analytics, manage model versions, and generate security reports through a modern cybersecurity dashboard.

The main goal of the project is to connect a real machine-learning pipeline with a functional web application instead of using static or hardcoded security data.

Features
1. Network Activity Analyzer

Users can submit network activity and send it to the backend for analysis.

The system:

Validates the submitted data
Loads the currently active ML model
Applies the saved preprocessing pipeline
Predicts the network activity class
Calculates prediction confidence
Determines whether the activity is normal or an attack
Calculates a risk score
Calculates a security score
Generates an explanation based on the submitted features and model output
Stores the analysis in the database
Creates an alert when the activity meets the alert conditions
2. Machine Learning Pipeline

NetGuard AI uses a Random Forest Classifier as its primary machine learning model.

The ML pipeline was designed so that the preprocessing used during prediction is the same preprocessing used during training.

The training process includes:

Uploading a CSV dataset
Inspecting the dataset
Selecting the target column
Selecting feature columns
Detecting numerical and categorical features
Handling missing values
Encoding categorical features
Scaling numerical features
Splitting the dataset into training and testing data
Training the Random Forest model
Evaluating the model
Saving the trained model and preprocessing artifacts
Registering the model in the database
Activating the newly trained model

The project stores model metadata including:

Model version
Dataset name
Number of samples
Number of features
Classes
Accuracy
Precision
Recall
F1 score
Confusion matrix
Classification report
Training configuration
Model paths
Training timestamp
3. Dataset Upload & Training

The application supports CSV datasets for machine learning training.

Uploaded datasets are inspected before training to identify:

Column names
Data types
Dataset structure
Target column
Feature columns
Numerical features
Categorical features
Missing values
Available classes

Only CSV files are accepted by the dataset upload API.

Uploaded files are stored with secure filenames and unique identifiers to avoid filename collisions.

4. Risk Scoring

After the ML model makes a prediction, NetGuard AI calculates a deterministic risk score.

The risk calculation considers:

Whether the activity was classified as an attack
The predicted attack type
The known severity associated with the attack type
The model's prediction confidence

The resulting risk score ranges from:

0 – 100

The system also converts the risk score into a security score.

Alert severity is determined from the calculated risk score:

Low
Medium
High
Critical
5. Automatic Alerts

When suspicious or malicious activity is detected, NetGuard AI can automatically create an alert.

Alerts contain information such as:

Attack type
Risk score
Prediction confidence
Severity
Current status
Related activity
Creation timestamp

Alerts can be:

Open
Acknowledged
Resolved
6. Dashboard

The dashboard displays information retrieved directly from the SQLite database and active ML model.

It provides statistics such as:

Total analyses
Total detected attacks
Attack rate
Open alerts
Total alerts
Model accuracy
Active model version
Recent activity
Average risk score
Attack-type distribution
Seven-day threat trends

The dashboard does not rely on predefined fake statistics. Data is calculated from the application's stored activities, alerts, and model records.

7. Activity History

The Activity History page stores previously analyzed network activities.

Users can:

View analyzed activities
Filter normal activities
Filter attacks
Search prediction types
Change the number of records per page
Navigate through paginated results

Each activity can contain information including:

Timestamp
Prediction
Confidence
Risk score
Protocol
Source IP
Destination IP
Model version
8. Analytics

The analytics section provides visual insights into the network activity stored in the database.

The application can analyze information such as:

Attack distribution
Activity trends
Risk levels
Prediction results
Network activity statistics

The frontend retrieves this information through backend APIs rather than using hardcoded chart values.

9. ML Model Information

The Model Information section provides information about the currently active machine learning model.

It displays:

Model version
Algorithm
Accuracy
Macro F1 score
Macro precision
Macro recall
Training samples
Number of features
Number of classes
Feature importance
Model version history

The active model is loaded from the model records stored in the database.

10. Security Reports

NetGuard AI can generate security reports based on the application's stored data.

Supported report types include:

Executive Summary
Detailed Analysis
Alerts Only
Model Performance

Reports can be generated for different time periods:

Last 24 hours
Last 7 days
Last 30 days
Last 90 days

Supported output formats:

PDF
JSON

Generated reports can also be downloaded from the application.

Technology Stack
Backend
Python
Flask
Flask Blueprints
Flask-SQLAlchemy
Flask-Migrate
SQLAlchemy
Machine Learning
Scikit-learn
Pandas
NumPy
Joblib
Frontend
HTML
CSS
JavaScript
Chart.js
Database
SQLite
Reporting
ReportLab
Environment & Utilities
Python-dotenv
Werkzeug
Project Architecture

The project follows a modular Flask architecture.

netguard_ai/
│
├── app/
│   ├── blueprints/
│   │   ├── activities/
│   │   ├── alerts/
│   │   ├── analytics/
│   │   ├── analyze/
│   │   ├── dashboard/
│   │   ├── dataset/
│   │   ├── model_info/
│   │   ├── pages/
│   │   └── reports/
│   │
│   ├── ml/
│   │   ├── predictor.py
│   │   ├── preprocessing.py
│   │   └── trainer.py
│   │
│   ├── models/
│   │   ├── activity.py
│   │   ├── alert.py
│   │   ├── ml_model_record.py
│   │   └── report.py
│   │
│   ├── services/
│   │   ├── alert_service.py
│   │   ├── explanation_service.py
│   │   ├── ml_service.py
│   │   └── risk_service.py
│   │
│   ├── config.py
│   ├── extensions.py
│   └── __init__.py
│
├── static/
│   └── css/
│       └── main.css
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── analyzer.html
│   ├── history.html
│   ├── alerts.html
│   ├── analytics.html
│   ├── dataset.html
│   ├── model.html
│   └── reports.html
│
├── uploads/
├── logs/
├── netguard.db
├── requirements.txt
└── run.py
How the Project Works

The complete workflow of NetGuard AI can be summarized as:

CSV Dataset
     │
     ▼
Dataset Upload
     │
     ▼
Dataset Inspection
     │
     ▼
Feature & Target Selection
     │
     ▼
Data Preprocessing
     │
     ▼
Train/Test Split
     │
     ▼
Random Forest Training
     │
     ▼
Model Evaluation
     │
     ▼
Save Model + Preprocessor + Metadata
     │
     ▼
Register & Activate Model
     │
     ▼
Network Activity Submitted
     │
     ▼
Saved Preprocessing Pipeline
     │
     ▼
Random Forest Prediction
     │
     ▼
Prediction + Confidence
     │
     ▼
Risk & Security Score
     │
     ├───────────────┐
     ▼               ▼
Explanation       Alert
     │               │
     └───────┬───────┘
             ▼
        SQLite Database
             │
             ▼
 Dashboard / History / Analytics / Reports
API Structure

The application uses REST-style APIs to connect the frontend with the backend.

Important endpoints include:

Method	Endpoint	Purpose
GET	/api/dashboard	Dashboard statistics
POST	/api/analyze	Analyze network activity
GET	/api/activities	Retrieve activity history
GET	/api/activities/<id>	Retrieve a specific activity
GET	/api/alerts	Retrieve alerts
PATCH	/api/alerts/<id>	Update an alert
GET	/api/analytics	Retrieve analytics
POST	/api/dataset/upload	Upload a CSV dataset
POST	/api/dataset/inspect	Inspect an uploaded dataset
POST	/api/dataset/train	Train a Random Forest model
GET	/api/model/performance	Retrieve model performance
GET	/api/model/info	Retrieve model information
POST	/api/report/generate	Generate a security report

API responses use structured JSON containing success, data, messages, and error information where appropriate.

Machine Learning Implementation

The project uses a preprocessing pipeline containing separate handling for numerical and categorical data.

Numerical Features

Numerical data is processed using:

Missing-value imputation
Median strategy
Standard scaling
Categorical Features

Categorical data is processed using:

Missing-value imputation
Most-frequent strategy
One-hot encoding
Unknown-category handling

The preprocessing pipeline is fitted during training and saved using Joblib.

During prediction, the saved pipeline is loaded and reused instead of being fitted again.

This helps maintain consistency between training and inference.

Model Prediction

The prediction system loads:

Random Forest classifier
Preprocessing pipeline
Label encoder
Model metadata

The model produces:

Predicted class
Prediction confidence
Class probabilities

The application then determines whether the predicted class represents normal/benign traffic or an attack.

The prediction result is stored together with the original network activity information.

Database

NetGuard AI uses SQLite through Flask-SQLAlchemy.

The database stores information about:

Network activities
Alerts
Machine learning models
Reports

The database acts as the main source of truth for dashboard statistics, activity history, alerts, analytics, and reporting.

Installation
1. Clone the repository
git clone https://github.com/your-username/netguard-ai.git
cd netguard-ai
2. Create a virtual environment
Windows
python -m venv venv
venv\Scripts\activate
macOS / Linux
python3 -m venv venv
source venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Run the application
python run.py

The application will start on:

http://127.0.0.1:5000
Using the Application
Step 1 — Upload a Dataset

Open the Dataset section and upload a CSV network-security dataset.

Step 2 — Inspect the Dataset

The application analyzes the uploaded dataset and provides information about its columns and structure.

Step 3 — Train the Model

Select the target column and feature columns, then train the Random Forest model.

After successful training, the model is registered and activated automatically.

Step 4 — Analyze Network Activity

Open the Activity Analyzer and submit network activity data.

The application sends the data to the backend and performs ML inference.

Step 5 — Review the Result

The result includes:

Prediction
Attack/normal classification
Confidence
Risk score
Security score
Explanation
Class probabilities
Model version
Step 6 — Monitor Results

The resulting activity is stored in the database and becomes available through:

Dashboard
Activity History
Alerts
Analytics
Reports
Design

The frontend was designed around a modern cybersecurity dashboard aesthetic.

The interface uses:

Dark-themed UI
Responsive layouts
Cards and data panels
Data tables
Interactive charts
Status badges
Loading states
Empty states
Error states
Form validation
Responsive navigation

The design focuses on presenting technical security and ML information in a clean and readable way.

Important Design Principle

A core principle of this project is:

Real Input → Real Backend → Real ML → Real Database → Real Calculations → Real API Response → Dynamic UI

The dashboard and analysis results are designed to be driven by actual application data rather than fabricated statistics or static values.

Project Objectives

This project was developed to demonstrate the integration of multiple areas of software engineering into one application:

Full-stack web development
REST API development
Machine learning
Data preprocessing
Database management
Model versioning
Cybersecurity concepts
Risk assessment
Alert management
Data visualization
Automated reporting
Modular software architecture

The project demonstrates how a machine-learning model can be integrated into a complete web-based cybersecurity workflow.

Future Improvements

Potential future improvements include:

Real-time network packet monitoring
Integration with live network traffic sources
More intrusion-detection algorithms
Isolation Forest-based anomaly detection
SHAP-based model explanations
User authentication and role-based access
Advanced threat intelligence integration
More visualization options
Automated model retraining
Containerized deployment
Cloud deployment
Automated testing and CI/CD
PostgreSQL support for production environments
Disclaimer

NetGuard AI is an educational and development project intended to demonstrate machine learning, cybersecurity analytics, and full-stack application development.

It should not be considered a replacement for production-grade intrusion detection or security monitoring systems without additional validation, testing, hardening, and integration with appropriate security infrastructure.

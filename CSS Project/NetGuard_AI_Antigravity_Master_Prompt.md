# NetGuard AI — Antigravity Master Prompt

Build **NetGuard AI**, a real full-stack, dynamic, ML-powered network intrusion and anomaly detection platform. Use the four supplied specification files as the single source of truth: `01_PROJECT_SPECIFICATION.md`, `02_TECHNICAL_ARCHITECTURE.md`, `03_UI_UX_AND_DYNAMIC_BEHAVIOR.md`, and `04_IMPLEMENTATION_TESTING_AND_RULES.md`.

## Core Requirements
- Build a working application, not a static UI prototype.
- Stack: **Python + Flask + Flask Blueprints + Flask-SQLAlchemy + SQLite + HTML/CSS/JavaScript + Chart.js + Pandas + NumPy + Scikit-learn + Joblib**.
- Keep frontend, REST API, business logic, ML, database, file processing, risk, alerts, and reporting modular and separated.
- Use the database as the source of truth.
- **Never hardcode or fabricate** activities, attacks, alerts, statistics, chart data, timestamps, security/risk scores, confidence, model metrics, predictions, or dataset statistics.
- If there is no data/model, show a proper empty/no-model state. If the backend fails, show the real error.
- Do not claim real-time monitoring or attack classes that are not actually implemented/supported.

## ML Pipeline
- Primary model: **Random Forest Classifier**.
- Optional anomaly detection: **Isolation Forest**, clearly separated from known attack classification.
- Support adaptable CSV datasets: inspect columns, data types, target, categorical/numerical features, missing values, and classes.
- Validate uploads, target column, feature compatibility, file type/size, and training feasibility.
- Prevent data leakage: split train/test first, fit preprocessing only on training data, and reuse the exact same preprocessing during prediction.
- Save model, preprocessing pipeline, feature metadata, class labels, training metadata, and evaluation metrics.
- Centralize prediction logic.
- Confidence must come from actual model output; if unavailable, show “Confidence unavailable”.
- Risk and security scores must be deterministic backend calculations based on actual model/data results.
- Explanations must be based on real model/data evidence, not generated filler.
- Version every trained model and record dataset, timestamp, features, classes, samples, metrics, and model path.

## Main Features
Implement real, API-connected:
1. Dashboard
2. Activity Analyzer
3. Activity/Attack History
4. Alerts
5. Analytics
6. Dataset Upload & Training
7. ML Model Information & Performance
8. Reports
9. Authentication/admin controls where required by the specifications
10. Advanced features only after core functionality is stable

Important API examples:
`GET /api/dashboard`
`POST /api/analyze`
`GET /api/activities`
`GET /api/activities/<id>`
`GET /api/alerts`
`PATCH /api/alerts/<id>`
`GET /api/analytics`
`POST /api/dataset/upload`
`POST /api/dataset/train`
`GET /api/model/performance`
`GET /api/model/info`
`POST /api/report/generate`

Use consistent JSON responses with success/data/message and structured error/code/message.

## UI/UX
Create a premium, modern, futuristic **AI + cybersecurity** interface that is responsive, clean, technical, readable, and professional. Use the supplied Dribbble reference only for **visual inspiration** such as typography, dark theme, cards, spacing, subtle gradients/glows, icons, buttons, inputs, charts, hover effects, and transitions. **Do not copy its layout, pages, workflow, content, branding, or architecture.**

Use a consistent sidebar/top-header application layout and only show navigation for actually implemented features. Dashboard cards, charts, history, alerts, and analysis results must update from real backend data. Support loading, error, empty, validation, and success states. Do not invent trend percentages or visual data.

## Security, Quality & Testing
- Validate all backend inputs.
- Secure file handling; never execute uploaded files.
- Use ORM/database-safe operations.
- Do not expose stack traces or sensitive credentials.
- Use safe password hashing and role protection where authentication exists.
- Add logging for important application, ML, dataset, database, and security events without logging secrets.
- Test unit, integration, API, ML, database, frontend interaction, and end-to-end behavior.
- Mandatory tests: empty database, dynamic data updates, model changes, invalid datasets, missing model, API failure, unsupported classes, preprocessing consistency, and no-hardcoded-data audit.
- Inspect existing code before modifying it and preserve working functionality.

## Implementation Order
1. Project foundation and Flask architecture
2. Database/models
3. ML dataset/training/prediction pipeline
4. Analysis/risk/explanation/alert services
5. APIs
6. Dynamic dashboard
7. History and alerts
8. Analytics
9. Dataset/model management
10. Reports
11. Optional advanced features
12. Full testing and final audit

## Definition of Done
The user can submit real network activity → backend validates it → real ML model predicts → risk/confidence/explanation are calculated → result is stored → dashboard/history/alerts/analytics update from the database. Dataset upload/training, model metadata/performance, reports, error handling, security, and tests work correctly.

**Final rule: Real input → Real backend → Real ML → Real database → Real calculations → Real API response → Dynamic UI. Never replace functionality with fake data. Read all four source files completely before making architectural decisions.**

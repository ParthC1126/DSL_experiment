"""
NetGuard AI — Frontend Page Routes
Serves all HTML templates for the SPA-like interface.
"""
from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
@pages_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@pages_bp.route("/analyzer")
def analyzer():
    return render_template("analyzer.html")


@pages_bp.route("/history")
def history():
    return render_template("history.html")


@pages_bp.route("/alerts")
def alerts():
    return render_template("alerts.html")


@pages_bp.route("/analytics")
def analytics():
    return render_template("analytics.html")


@pages_bp.route("/dataset")
def dataset():
    return render_template("dataset.html")


@pages_bp.route("/model")
def model():
    return render_template("model.html")


@pages_bp.route("/reports")
def reports():
    return render_template("reports.html")

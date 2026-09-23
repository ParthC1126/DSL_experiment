"""
NetGuard AI — Reports API Blueprint
POST /api/report/generate
GET  /api/report/list
GET  /api/report/<id>/download
"""
import json
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, send_file

from ...extensions import db
from ...models.report import Report
from ...models.activity import NetworkActivity
from ...models.alert import Alert
from ...services.ml_service import get_active_model
from sqlalchemy import func

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/report/generate", methods=["POST"])
def generate_report():
    """
    Generate a report based on real database data.
    Body:
    {
        "report_type": "summary" | "detailed" | "alerts_only" | "model_performance",
        "days": int (default 7),
        "format": "json" | "pdf" (default "json")
    }
    """
    data = request.get_json(silent=True) or {}
    report_type = data.get("report_type", "summary")
    days = int(data.get("days", 7))
    fmt = data.get("format", "json")

    if report_type not in Report.REPORT_TYPES:
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": f"report_type must be one of: {Report.REPORT_TYPES}"}
        }), 400

    since = datetime.utcnow() - timedelta(days=days)

    # ── Gather real data ─────────────────────────────────────────
    content = _build_report_content(report_type, since, days)

    # ── Persist report ───────────────────────────────────────────
    title = f"NetGuard AI — {report_type.replace('_', ' ').title()} Report ({days}d)"
    report = Report(
        report_type=report_type,
        title=title,
        date_from=since,
        date_to=datetime.utcnow(),
        content_json=json.dumps(content),
        file_format=fmt,
    )
    db.session.add(report)
    db.session.commit()

    if fmt == "pdf":
        try:
            pdf_path = _generate_pdf(report, content, current_app.config["REPORTS_DIR"])
            report.file_path = pdf_path
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"PDF generation failed: {e}")
            return jsonify({
                "success": False,
                "error": {"code": "PDF_FAILED", "message": f"PDF generation failed: {str(e)}"}
            }), 500

    current_app.logger.info(f"Report {report.id} generated: type={report_type}, format={fmt}")

    return jsonify({
        "success": True,
        "data": {
            "report_id": report.id,
            "title": title,
            "report_type": report_type,
            "format": fmt,
            "generated_at": report.generated_at.isoformat(),
            "content": content if fmt == "json" else None,
            "file_path": report.file_path,
        }
    })


@reports_bp.route("/report/list", methods=["GET"])
def list_reports():
    reports = Report.query.order_by(Report.generated_at.desc()).limit(50).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in reports]})


@reports_bp.route("/report/<int:report_id>/download", methods=["GET"])
def download_report(report_id: int):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "Report not found."}}), 404

    if report.file_format == "pdf" and report.file_path and os.path.isfile(report.file_path):
        return send_file(report.file_path, as_attachment=True, download_name=f"report_{report_id}.pdf")

    # Serve JSON
    return jsonify({"success": True, "data": report.content})


# ── Internal helpers ─────────────────────────────────────────────────────────

def _build_report_content(report_type: str, since: datetime, days: int) -> dict:
    content = {
        "generated_at": datetime.utcnow().isoformat(),
        "period_days": days,
        "from": since.isoformat(),
        "to": datetime.utcnow().isoformat(),
    }

    if report_type in ("summary", "detailed"):
        total = NetworkActivity.query.filter(NetworkActivity.timestamp >= since).count()
        attacks = NetworkActivity.query.filter(
            NetworkActivity.timestamp >= since, NetworkActivity.is_attack == True
        ).count()

        attack_types = (
            NetworkActivity.query
            .filter(NetworkActivity.timestamp >= since, NetworkActivity.is_attack == True)
            .with_entities(NetworkActivity.prediction, func.count(NetworkActivity.id).label("count"))
            .group_by(NetworkActivity.prediction)
            .order_by(func.count(NetworkActivity.id).desc())
            .all()
        )

        content["traffic_summary"] = {
            "total_analyses": total,
            "total_attacks": attacks,
            "normal_traffic": total - attacks,
            "attack_rate": round(attacks / total * 100, 2) if total > 0 else 0,
        }
        content["attack_types"] = [{"type": r.prediction, "count": r.count} for r in attack_types]

    if report_type in ("summary", "detailed", "alerts_only"):
        alerts = Alert.query.filter(Alert.created_at >= since).all()
        content["alerts"] = {
            "total": len(alerts),
            "open": sum(1 for a in alerts if a.status == "open"),
            "critical": sum(1 for a in alerts if a.severity == "critical"),
            "high": sum(1 for a in alerts if a.severity == "high"),
            "medium": sum(1 for a in alerts if a.severity == "medium"),
            "low": sum(1 for a in alerts if a.severity == "low"),
        }
        if report_type == "detailed":
            content["alert_list"] = [a.to_dict() for a in alerts[:100]]

    if report_type in ("summary", "detailed", "model_performance"):
        active = get_active_model()
        if active:
            content["model"] = {
                "version": active.version,
                "accuracy": active.accuracy,
                "f1_macro": active.f1_macro,
                "precision_macro": active.precision_macro,
                "recall_macro": active.recall_macro,
                "classes": active.classes,
                "n_samples": active.n_samples,
                "trained_at": active.trained_at.isoformat() if active.trained_at else None,
            }
        else:
            content["model"] = None

    return content


def _generate_pdf(report: Report, content: dict, reports_dir: str) -> str:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    pdf_path = os.path.join(reports_dir, f"report_{report.id}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(report.title or "NetGuard AI Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated: {content.get('generated_at', '')}", styles["Normal"]))
    story.append(Paragraph(f"Period: last {content.get('period_days', 7)} days", styles["Normal"]))
    story.append(Spacer(1, 20))

    if "traffic_summary" in content:
        ts = content["traffic_summary"]
        story.append(Paragraph("Traffic Summary", styles["Heading2"]))
        data = [["Metric", "Value"]]
        for k, v in ts.items():
            data.append([k.replace("_", " ").title(), str(v)])
        t = Table(data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    if "alerts" in content:
        story.append(Paragraph("Alert Summary", styles["Heading2"]))
        al = content["alerts"]
        data = [["Metric", "Count"]]
        for k, v in al.items():
            data.append([k.title(), str(v)])
        t = Table(data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)

    doc.build(story)
    return pdf_path

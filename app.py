"""
app.py — Flask web server for the AI Learning Companion.

Provides a multi-student, premium web interface for the multi-agent system.
Deployable to pxxl.app.
"""

import os
import json
from datetime import datetime
from PIL import Image
import io
import base64
from dotenv import load_dotenv

load_dotenv()

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from functools import wraps
from main import init_agents, handle_message
from adaptive_bridge import snapshot as adaptive_snapshot, intervention as adaptive_intervention, timeline as adaptive_timeline, submit_attempt as adaptive_submit_attempt, submit_remediation as adaptive_submit_remediation, review as adaptive_review, submit_review as adaptive_submit_review

try:
    from tools.pdf_generator import generate_student_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("WARNING: 'reportlab' not found. PDF Exporting disabled.")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "udene-physics-secret-shared-laptop")

agents, backend, model, db = init_agents()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('profile'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():
    student_id = session.get('student_id')
    stats = db.get_stats(student_id)
    return render_template('index.html', backend=backend, model=model, nickname=session.get('nickname'), streak=stats.get('streak_days', 0))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            nickname = request.form.get('nickname', '').strip()
            pin = request.form.get('pin', '').strip() or None
            if not nickname:
                flash("Nickname is required!", "error")
            else:
                student_id = db.add_student(nickname, pin)
                if student_id == -1:
                    flash("Nickname already taken!", "error")
                else:
                    session['student_id'] = student_id
                    session['nickname'] = nickname
                    flash(f"Welcome, {nickname}! 🚀", "success")
                    return redirect(url_for('index'))
        elif action == 'login':
            nickname = request.form.get('nickname')
            pin = request.form.get('pin', '').strip() or None
            student = db.verify_student(nickname, pin)
            if student:
                session['student_id'] = student['id']
                session['nickname'] = student['nickname']
                flash(f"Welcome back, {nickname}! 🔥", "success")
                return redirect(url_for('index'))
            flash("Invalid nickname or PIN!", "error")
    students = db.get_all_students()
    return render_template('profile.html', students=students)


@app.route('/switch')
def switch_profile():
    session.clear()
    return redirect(url_for('profile'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('profile'))


@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    message = data.get('message', '').strip()
    student_id = session.get('student_id')
    image_data = data.get('image')
    if not message and not image_data:
        return jsonify({"error": "No message or image provided"}), 400
    img_obj = None
    if image_data:
        try:
            if "," in image_data:
                image_data = image_data.split(",")[1]
            img_obj = Image.open(io.BytesIO(base64.b64decode(image_data)))
        except Exception as e:
            return jsonify({"error": f"Invalid image data: {e}"}), 400
    try:
        new_badges = agents["progress"].auto_check_badges(student_id)
        label, response = handle_message(message, agents, db, student_id, image=img_obj)
        stats = db.get_stats(student_id)
        return jsonify({"label": label, "response": response, "backend": backend, "model": model, "streak": stats.get('streak_days', 0), "new_badges": new_badges})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/adaptive/snapshot')
@login_required
def adaptive_snapshot_route():
    try:
        return jsonify(adaptive_snapshot(session['nickname']))
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route('/adaptive/intervention')
@login_required
def adaptive_intervention_route():
    try:
        return jsonify(adaptive_intervention(session['nickname']))
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route('/adaptive/timeline')
@login_required
def adaptive_timeline_route():
    try:
        return jsonify(adaptive_timeline(session['nickname']))
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route('/adaptive/attempt', methods=['POST'])
@login_required
def adaptive_attempt_route():
    data = request.json or {}
    if not isinstance(data.get('conceptId'), str) or not data['conceptId'].strip():
        return jsonify({"error": "conceptId is required"}), 400
    if not isinstance(data.get('reasoning'), str):
        return jsonify({"error": "reasoning is required"}), 400
    if not isinstance(data.get('correct'), bool):
        return jsonify({"error": "correct must be a boolean"}), 400
    try:
        return jsonify(adaptive_submit_attempt(session['nickname'], data['conceptId'], data['correct'], data['reasoning'], data.get('answer'), data.get('problemId'), data.get('confidence'), bool(data.get('hintUsed')), data.get('durationSeconds'), data.get('misconceptionCodes')))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/adaptive/remediation', methods=['POST'])
@login_required
def adaptive_remediation_route():
    data = request.json or {}
    if not isinstance(data.get('interventionId'), int):
        return jsonify({"error": "interventionId must be an integer"}), 400
    if not isinstance(data.get('reasoning'), str) or not isinstance(data.get('answer'), str):
        return jsonify({"error": "reasoning and answer are required"}), 400
    try:
        return jsonify(adaptive_submit_remediation(session['nickname'], data['interventionId'], data['reasoning'], data['answer'], data.get('confidence'), bool(data.get('hintUsed')), data.get('durationSeconds')))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/adaptive/review')
@login_required
def adaptive_review_route():
    try:
        return jsonify(adaptive_review(session['nickname']))
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route('/adaptive/review', methods=['POST'])
@login_required
def adaptive_review_submit_route():
    data = request.json or {}
    if not isinstance(data.get('reasoning'), str) or not isinstance(data.get('answer'), str):
        return jsonify({"error": "reasoning and answer are required"}), 400
    try:
        return jsonify(adaptive_submit_review(session['nickname'], data['reasoning'], data['answer'], data.get('confidence'), bool(data.get('hintUsed')), data.get('durationSeconds')))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/sandbox')
@login_required
def sandbox():
    return render_template('simulation.html')


@app.route('/verify', methods=['POST'])
@login_required
def verify_lesson():
    if session.get('student_id') != 1:
        return jsonify({"error": "Unauthorized. Only a Sage can verify lessons."}), 403
    lesson_id = request.json.get('lesson_id')
    if not lesson_id:
        return jsonify({"error": "Missing lesson_id"}), 400
    db.verify_distilled_lesson(lesson_id)
    return jsonify({"success": True})


@app.route('/report')
@login_required
def get_report():
    return jsonify({"report": agents["progress"].generate_report(session['student_id'])})


@app.route('/curriculum')
@login_required
def get_curriculum():
    return jsonify({"curriculum": agents["physics"].get_curriculum_overview(session['student_id'])})


@app.route('/export/report')
@login_required
def export_report():
    if not PDF_AVAILABLE:
        return jsonify({"error": "PDF Exporting is temporarily disabled on this server (Missing reportlab)."}), 503
    student_id = session.get('student_id')
    nickname = session.get('nickname')
    stats_raw = db.get_stats(student_id)
    stats = {"streak": stats_raw.get('streak_days', 0), "total_interactions": db.conn.execute("SELECT COUNT(*) FROM interactions WHERE student_id = ?", (student_id,)).fetchone()[0], "badges": json.loads(stats_raw.get('badges_json', '[]'))}
    mastery_raw = db.get_all_mastery(student_id)
    mastery_list = [{"topic": m['topic'], "category": m['category'], "score": m['score']} for m in mastery_raw]
    export_dir = os.path.join(os.path.dirname(__file__), "memory", "exports")
    os.makedirs(export_dir, exist_ok=True)
    filename = f"Udene_Report_{nickname}_{datetime.now().strftime('%Y%m%d')}.pdf"
    output_path = os.path.join(export_dir, filename)
    try:
        generate_student_report(nickname, stats, mastery_list, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500


@app.route('/history', methods=['GET'])
@login_required
def get_chat_history():
    student_id = session.get('student_id')
    topic = request.args.get('topic')
    history = db.get_recent_interactions(student_id, limit=30, topic=topic)
    formatted = []
    for inter in reversed(history):
        if inter['user_input']:
            formatted.append({"role": "user", "content": inter['user_input'], "label": "🧑 STUDENT"})
        if inter['agent_response']:
            agent_name = inter['agent']
            label = "🤖 Agent"
            for k, v in agents.items():
                if v.name == agent_name:
                    from main import AGENT_LABELS
                    label = AGENT_LABELS.get(k, label).upper()
                    break
            formatted.append({"role": "assistant", "content": inter['agent_response'], "label": label})
    return jsonify({"history": formatted})


@app.route('/sessions', methods=['GET'])
@login_required
def get_sessions():
    student_id = session.get('student_id')
    interactions = db.get_recent_interactions(student_id, limit=100)
    sessions = []
    seen = set()
    for inter in interactions:
        topic = inter.get('topic') or 'General'
        agent = inter.get('agent') or 'Assistant'
        key = f"{agent}:{topic}"
        if key not in seen:
            sessions.append({"topic": topic, "agent": agent, "timestamp": inter.get('timestamp')})
            seen.add(key)
    return jsonify({"sessions": sessions})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

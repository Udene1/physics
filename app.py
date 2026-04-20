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

# Load environment variables FIRST
load_dotenv()

import sys
# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from functools import wraps
from main import init_agents, handle_message

# Graceful optional imports
try:
    from tools.pdf_generator import generate_student_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("WARNING: 'reportlab' not found. PDF Exporting disabled.")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "udene-physics-secret-shared-laptop")

# Initialize agents once at startup
agents, backend, model, db = init_agents()

# ── Auth Middleware ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('profile'))
        return f(*args, **kwargs)
    return decorated_function

# ── Routes ──────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    """Render the main chat interface."""
    student_id = session.get('student_id')
    stats = db.get_stats(student_id)
    return render_template(
        'index.html', 
        backend=backend, 
        model=model, 
        nickname=session.get('nickname'),
        streak=stats.get('streak_days', 0)
    )

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """Profile selection and creation."""
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
            else:
                flash("Invalid nickname or PIN!", "error")

    students = db.get_all_students()
    return render_template('profile.html', students=students)

@app.route('/switch')
def switch_profile():
    """Clear session and go to profile page."""
    session.clear()
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    """Clear session and go to profile page."""
    session.clear()
    return redirect(url_for('profile'))

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages from the web UI."""
    data = request.json
    message = data.get('message', '').strip()
    student_id = session.get('student_id')
    image_data = data.get('image') # Base64 string if present
    
    if not message and not image_data:
        return jsonify({"error": "No message or image provided"}), 400
    
    # Process image if present
    img_obj = None
    if image_data:
        try:
            # Strip header if present (data:image/png;base64,...)
            if "," in image_data:
                image_data = image_data.split(",")[1]
            img_bytes = base64.b64decode(image_data)
            img_obj = Image.open(io.BytesIO(img_bytes))
        except Exception as e:
            return jsonify({"error": f"Invalid image data: {e}"}), 400

    try:
        # Check for new badges
        new_badges = agents["progress"].auto_check_badges(student_id)
        
        label, response = handle_message(message, agents, db, student_id, image=img_obj)
        stats = db.get_stats(student_id) # Refresh stats after activity
        
        return jsonify({
            "label": label,
            "response": response,
            "backend": backend,
            "model": model,
            "streak": stats.get('streak_days', 0),
            "new_badges": new_badges
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sandbox')
@login_required
def sandbox():
    """Render the simulation sandbox."""
    return render_template('simulation.html')

@app.route('/verify', methods=['POST'])
@login_required
def verify_lesson():
    """Expert route to verify a distilled lesson."""
    # Simple check: only student with ID 1 (Admin/Teacher) can verify for now
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
    """Get the latest progress report for the current student."""
    student_id = session.get('student_id')
    report = agents["progress"].generate_report(student_id)
    return jsonify({"report": report})

@app.route('/curriculum')
@login_required
def get_curriculum():
    """Get the physics curriculum overview for the current student."""
    student_id = session.get('student_id')
    overview = agents["physics"].get_curriculum_overview(student_id)
    return jsonify({"curriculum": overview})

@app.route('/export/report')
@login_required
def export_report():
    """Generate and download a PDF progress report."""
    if not PDF_AVAILABLE:
        return jsonify({"error": "PDF Exporting is temporarily disabled on this server (Missing reportlab)."}), 503
        
    student_id = session.get('student_id')
    nickname = session.get('nickname')
    
    # Get stats and mastery
    stats_raw = db.get_stats(student_id)
    # Convert DB row/dict to what pdf_generator expects
    stats = {
        "streak": stats_raw.get('streak_days', 0),
        "total_interactions": db.conn.execute(
            "SELECT COUNT(*) FROM interactions WHERE student_id = ?", (student_id,)
        ).fetchone()[0],
        "badges": json.loads(stats_raw.get('badges_json', '[]'))
    }
    
    mastery_raw = db.get_all_mastery(student_id)
    mastery_list = [
        {"topic": m['topic'], "category": m['category'], "score": m['score']} 
        for m in mastery_raw
    ]
    
    # Create temp directory for exports if it doesn't exist
    export_dir = os.path.join(os.path.dirname(__file__), "memory", "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    filename = f"Udene_Report_{nickname}_{datetime.now().strftime('%Y%m%d')}.pdf"
    output_path = os.path.join(export_dir, filename)
    
    try:
        generate_student_report(nickname, stats, mastery_list, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500

@app.route('/history', methods=['GET'])
@login_required
def get_chat_history():
    """Fetch and return the recent chat history for the logged-in student."""
    student_id = session.get('student_id')
    history = db.get_recent_interactions(student_id, limit=30)
    # interactions are stored with user_input and agent_response
    # we return them in chronological order
    formatted = []
    for inter in reversed(history):
        if inter['user_input']:
            formatted.append({"role": "user", "content": inter['user_input'], "label": "🧑 STUDENT"})
        if inter['agent_response']:
            # Try to get the agent's full label
            agent_name = inter['agent']
            label = "🤖 Agent"
            for k, v in agents.items():
                if v.name == agent_name:
                    from main import AGENT_LABELS
                    label = AGENT_LABELS.get(k, label).upper()
                    break
            formatted.append({"role": "assistant", "content": inter['agent_response'], "label": label})
    
    return jsonify({"history": formatted})

if __name__ == '__main__':
    # Use environment variables for port to support cloud hosting
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

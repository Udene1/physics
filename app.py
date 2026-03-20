"""
app.py — Flask web server for the AI Learning Companion.

Provides a multi-student, premium web interface for the multi-agent system.
Deployable to pxxl.app.
"""

import os
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from main import init_agents, handle_message

# Load environment variables from .env file
load_dotenv()

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

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages from the web UI."""
    data = request.json
    message = data.get('message', '').strip()
    student_id = session.get('student_id')
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # Check for new badges
        new_badges = agents["progress"].auto_check_badges(student_id)
        
        label, response = handle_message(message, agents, db, student_id)
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

from tools.pdf_generator import generate_student_report

# Ensure export directory exists
os.makedirs("memory/exports", exist_ok=True)

@app.route('/download_report')
@login_required
def download_report():
    student_id = session.get('student_id')
    nickname = session.get('nickname')
    
    # 1. Gather Data
    stats = db.generate_summary(student_id)
    mastery_list = db.get_all_mastery(student_id)
    
    # 2. File Path
    filename = f"Report_{nickname}_{datetime.now().strftime('%Y%m%d')}.pdf"
    filepath = os.path.join("memory/exports", filename)
    
    # 3. Generate PDF
    try:
        generate_student_report(nickname, stats, mastery_list, filepath)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500

if __name__ == '__main__':
    # Use environment variables for port to support cloud hosting
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

"""
app.py — Flask web server for the AI Learning Companion.

Provides a modern web interface for the multi-agent system.
Deployable to pxxl.app.
"""

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from main import init_agents, handle_message

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize agents once at startup
# Note: In production with multiple workers, we'd want to handle 
# shared state (DB) carefully, but for this local-first app, it works.
agents, backend, model, db = init_agents()

@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html', backend=backend, model=model)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the web UI."""
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        label, response = handle_message(message, agents, db)
        return jsonify({
            "label": label,
            "response": response,
            "backend": backend,
            "model": model
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/report')
def get_report():
    """Get the latest progress report."""
    report = agents["progress"].generate_report()
    return jsonify({"report": report})

@app.route('/curriculum')
def get_curriculum():
    """Get the physics curriculum overview."""
    overview = agents["physics"].get_curriculum_overview()
    return jsonify({"curriculum": overview})

if __name__ == '__main__':
    # Use environment variables for port to support cloud hosting
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
import os
import sys
from datetime import datetime

# Ensure correct module paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.firebase_manager import FirebaseManager as DatabaseManager
from agent.knowledge_base import KnowledgeBase
from agent.help_request_handler import HelpRequestHandler
from agent.livekit_agent import LiveAgent

app = Flask(__name__)
CORS(app)

# Initialize core services
db = DatabaseManager()
kb = KnowledgeBase(db)

def supervisor_notify(req):
    """Called when a new help request is created."""
    print(f"[SUPERVISOR HOOK] Need help answering: {req['question']} (id={req['request_id']})")

handler = HelpRequestHandler(db, kb, notify_callback=supervisor_notify)
agent = LiveAgent(db, notify_callback=supervisor_notify)

# -----------------------------------------------------------
# HTML Dashboard
# -----------------------------------------------------------
INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Frontdesk — Supervisor Panel</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 18px; background:#f3f4f6; color:#111827;}
    h1 { font-size:20px; }
    .card { background:white; padding:16px; border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom:12px;}
    table { width:100%; border-collapse:collapse; }
    th, td { text-align:left; padding:8px; border-bottom:1px solid #e5e7eb; }
    .btn { padding:6px 10px; border-radius:6px; text-decoration:none; color:white; background:#2563eb; }
    .btn-ghost { background: #111827; opacity:0.06; color: #111827; padding:6px 8px; border-radius:6px; }
    .muted { color:#6b7280; font-size:13px; }
    form { margin:0; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Frontdesk Engineering Test — Supervisor</h1>
    <div class="muted">View and resolve pending help requests below.</div>
    <p>
      <a class="btn" href="{{ url_for('index') }}">Refresh</a>
      <a class="btn" href="{{ url_for('demo_call') }}" style="background:#059669">Simulate Incoming Call (demo)</a>
    </p>
  </div>

  <div class="card">
    <h2>Pending Requests</h2>
    {% if pending %}
    <table>
      <thead><tr><th>Request ID</th><th>Question</th><th>Caller</th><th>Created</th><th>Action</th></tr></thead>
      <tbody>
      {% for r in pending %}
        <tr>
          <td style="font-family:monospace">{{ r.request_id }}</td>
          <td>{{ r.question }}</td>
          <td>{{ r.caller_phone }}</td>
          <td>{{ r.created_at }}</td>
          <td>
            <form method="post" action="{{ url_for('resolve') }}">
              <input type="hidden" name="request_id" value="{{ r.request_id }}">
              <input type="text" name="answer" placeholder="Type answer..." required style="min-width:220px;padding:6px;">
              <button class="btn" type="submit">Resolve</button>
            </form>
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
      <div class="muted">No pending requests.</div>
    {% endif %}
  </div>

  <div class="card">
    <h2>Resolved / Unresolved History (last 100)</h2>
    <table>
      <thead><tr><th>ID</th><th>Q</th><th>Status</th><th>Answer</th><th>Resolved At</th></tr></thead>
      <tbody>
      {% for r in history %}
        <tr>
          <td style="font-family:monospace">{{ r.request_id }}</td>
          <td>{{ r.question }}</td>
          <td>{{ r.status }}</td>
          <td>{{ r.answer or '-' }}</td>
          <td>{{ r.resolved_at or '-' }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Learned Answers</h2>
    {% if knowledge %}
      <table>
        <thead><tr><th>Question</th><th>Answer</th><th>Category</th><th>Added</th></tr></thead>
        <tbody>
        {% for k in knowledge %}
          <tr>
            <td>{{ k.question }}</td>
            <td>{{ k.answer }}</td>
            <td>{{ k.category }}</td>
            <td>{{ k.created_at }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    {% else %}
      <div class="muted">None yet.</div>
    {% endif %}
  </div>
</body>
</html>
"""

# -----------------------------------------------------------
# Routes
# -----------------------------------------------------------
@app.route('/')
def index():
    agent.check_timeouts()
    pending = db.get_requests_by_status('pending')
    all_reqs = db.list_requests(limit=200)
    history = [r for r in all_reqs if r.get('status') != 'pending']
    knowledge = db.list_knowledge()
    return render_template_string(INDEX_HTML, pending=pending, history=history, knowledge=knowledge)


@app.route('/demo_call')
def demo_call():
    return redirect(url_for('simulate_call', phone='7569677466', q='hi'))


@app.route('/simulate_call')
def simulate_call():
    phone = request.args.get('phone', '7569677466')
    q = request.args.get('q', 'hi')
    res = asyncio_run(agent.receive_call(phone, q))
    return redirect(url_for('index'))


def asyncio_run(coro):
    import asyncio
    try:
        return asyncio.get_event_loop().run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


@app.route('/resolve', methods=['POST'])
def resolve():
    req_id = request.form.get('request_id')
    answer = request.form.get('answer')
    if not req_id or not answer:
        return "request_id and answer required", 400

    resolved = handler.resolve_request(req_id, answer, resolver='supervisor')
    if not resolved:
        return "request not found", 404

    print(f"[SUPERVISOR] Resolved {req_id}. Sent to {resolved.get('caller_phone')}: {answer}")
    return redirect(url_for('index'))


@app.route('/api/requests', methods=['GET'])
def api_list():
    status = request.args.get('status')
    if status:
        reqs = db.get_requests_by_status(status)
    else:
        reqs = db.list_requests()
    return jsonify(reqs)


@app.route('/api/requests/<request_id>/resolve', methods=['POST'])
def api_resolve(request_id):
    body = request.json or {}
    answer = body.get('answer')
    if not answer:
        return jsonify({'error': 'answer required'}), 400
    resolved = handler.resolve_request(request_id, answer, resolver='supervisor')
    if not resolved:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': 'ok', 'resolved': resolved})


@app.route('/api/knowledge', methods=['GET'])
def api_knowledge():
    return jsonify(db.list_knowledge())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('SUPERVISOR_PORT', 5000)), debug=True)

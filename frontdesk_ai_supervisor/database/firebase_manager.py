import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from uuid import uuid4

DEFAULT_DB_FILE = os.getenv('LOCAL_DB_FILE', 'frontdesk_local_db.json')


class FirebaseManager:
    """
    Lightweight local JSON DB used as default. Schema:
    {
      "requests": [ {request} ],
      "knowledge": [ {question, answer, category, created_at} ],
      "messages": [ {message, created_at} ]
    }
    """

    def __init__(self, credentials_path: str = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_file = os.path.join(base_dir, DEFAULT_DB_FILE)
        provided = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if provided and os.path.exists(provided):
            print(
                "[DB] Firebase credentials provided but default manager uses local JSON. "
                "You can extend this class to use firebase-admin."
            )
        if not os.path.exists(self.db_file):
            self._write({'requests': [], 'knowledge': [], 'messages': []})

    # --------------------------------------------------------------------------
    # Internal I/O methods
    # --------------------------------------------------------------------------
    def _read(self) -> Dict:
        try:
            with open(self.db_file, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file is corrupted or missing, reset to clean state
            self._write({'requests': [], 'knowledge': [], 'messages': []})
            return {'requests': [], 'knowledge': [], 'messages': []}

    def _write(self, data: Dict):
        with open(self.db_file, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    def _validate_request(self, request: dict) -> bool:
        """Validate request has required fields and is not empty"""
        if not request or not isinstance(request, dict):
            return False
        required_fields = ['request_id', 'question', 'caller_phone', 'status']
        return all(field in request and request[field] for field in required_fields)

    # --------------------------------------------------------------------------
    # Requests
    # --------------------------------------------------------------------------
    def add_request(self, request: dict) -> dict:
        if not self._validate_request(request):
            raise ValueError("Invalid request object: missing required fields")

        data = self._read()
        data.setdefault('requests', []).append(request)
        self._write(data)
        return request

    def create_request(self, request_data: dict) -> dict:
        """
        Create a new help request entry with automatic fields.
        Used by the LiveAgent during incoming calls.
        """
        if not request_data.get("caller_phone") or not request_data.get("question"):
            raise ValueError("caller_phone and question are required to create a request")

        request = {
            "request_id": str(uuid4()),
            "caller_phone": request_data["caller_phone"],
            "question": request_data["question"],
            "status": request_data.get("status", "pending"),
            "created_at": datetime.utcnow().isoformat(),
            "timeout_at": (datetime.utcnow() + timedelta(seconds=300)).isoformat(),
            "answer": None,
            "resolved_at": None,
            "resolved_by": None,
            "category": request_data.get("category", "general"),
        }

        data = self._read()
        data.setdefault('requests', []).append(request)
        self._write(data)
        print(f"[DB] Created new request {request['request_id']} for {request['caller_phone']}")
        return request

    def get_request(self, request_id: str) -> Optional[dict]:
        data = self._read()
        for r in data.get('requests', []):
            if self._validate_request(r) and r.get('request_id') == request_id:
                return r
        return None

    def update_request(self, request_id: str, payload: dict) -> bool:
        if not self._validate_request(payload):
            raise ValueError("Invalid request payload")

        data = self._read()
        updated = False
        for idx, r in enumerate(data.get('requests', [])):
            if self._validate_request(r) and r.get('request_id') == request_id:
                data['requests'][idx] = payload
                updated = True
                break
        if updated:
            self._write(data)
        return updated

    def get_requests_by_status(self, status: str) -> List[dict]:
        data = self._read()
        return [r for r in data.get('requests', [])
                if self._validate_request(r) and r.get('status') == status]

    def list_requests(self, limit: int = 100) -> List[dict]:
        data = self._read()
        valid_requests = [r for r in data.get('requests', []) if self._validate_request(r)]
        return valid_requests[-limit:]

    # --------------------------------------------------------------------------
    # Knowledge
    # --------------------------------------------------------------------------
    def add_to_knowledge_base(self, entry: dict):
        if not entry.get('question') or not entry.get('answer'):
            raise ValueError("Knowledge entry must have question and answer")

        data = self._read()
        data.setdefault('knowledge', []).append({
            'question': entry.get('question'),
            'answer': entry.get('answer'),
            'category': entry.get('category', 'general'),
            'created_at': datetime.utcnow().isoformat()
        })
        self._write(data)

    def search_knowledge(self, question: str) -> Optional[str]:
        if not question:
            return None

        data = self._read()
        q = question.lower()
        # simple substring match (most recent first)
        for item in reversed(data.get('knowledge', [])):
            if item.get('question') and item.get('answer'):
                item_q = item.get('question').lower()
                if item_q in q or q in item_q:
                    return item.get('answer')
        return None

    def list_knowledge(self) -> List[dict]:
        data = self._read()
        return [k for k in data.get('knowledge', [])
                if k.get('question') and k.get('answer')]

    # --------------------------------------------------------------------------
    # Messages
    # --------------------------------------------------------------------------
    def log_message(self, msg: dict):
        if not msg:
            return

        data = self._read()
        data.setdefault('messages', []).append({
            'message': msg,
            'created_at': datetime.utcnow().isoformat()
        })
        self._write(data)

    # --------------------------------------------------------------------------
    # Maintenance
    # --------------------------------------------------------------------------
    def clear(self):
        """Clear all data - useful for testing"""
        self._write({'requests': [], 'knowledge': [], 'messages': []})

    def cleanup_invalid_entries(self):
        """Remove any invalid/empty entries from the database"""
        data = self._read()

        # Clean requests
        data['requests'] = [r for r in data.get('requests', []) if self._validate_request(r)]

        # Clean knowledge
        data['knowledge'] = [k for k in data.get('knowledge', [])
                             if k.get('question') and k.get('answer')]

        # Clean messages
        data['messages'] = [m for m in data.get('messages', []) if m.get('message')]

        self._write(data)
        print(
            f"[DB] Cleanup complete. Valid entries - Requests: {len(data['requests'])}, "
            f"Knowledge: {len(data['knowledge'])}, Messages: {len(data['messages'])}"
        )

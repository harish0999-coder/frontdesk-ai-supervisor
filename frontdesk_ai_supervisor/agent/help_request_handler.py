from typing import Optional, List
import uuid
from datetime import datetime, timedelta


class HelpRequestHandler:
    """
    Create pending requests, resolve them, mark timeouts as unresolved.
    """

    def __init__(self, db_manager, knowledge_base, notify_callback=None, timeout_seconds: int = 300):
        self.db = db_manager
        self.kb = knowledge_base
        self.notify_callback = notify_callback
        self.timeout_seconds = timeout_seconds

    def create_request(self, question: str, caller_phone: str, session_id: str, category: str = 'general') -> dict:
        """
        Create a new help request.
        Returns the created request object.
        """
        if not question or not caller_phone:
            raise ValueError("Question and caller_phone are required")

        request_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        timeout_at = (datetime.utcnow() + timedelta(seconds=self.timeout_seconds)).isoformat()

        payload = {
            'request_id': request_id,
            'session_id': session_id,
            'question': question,
            'caller_phone': caller_phone,
            'category': category,
            'status': 'pending',
            'created_at': now,
            'timeout_at': timeout_at,
            'answer': None,
            'resolved_at': None,
            'resolved_by': None
        }

        try:
            self.db.add_request(payload)
        except Exception as e:
            print(f"[ERROR] Failed to create request: {e}")
            raise

        # Notify human (console/webhook)
        if self.notify_callback:
            try:
                self.notify_callback(payload)
            except Exception as e:
                print(f"[WARN] Notification callback failed: {e}")

        return payload

    def resolve_request(self, request_id: str, answer: str, resolver: str = 'supervisor') -> Optional[dict]:
        """
        Resolve a pending request with an answer.
        Updates the knowledge base and sends follow-up to caller.
        Returns the resolved request object.
        """
        if not request_id or not answer:
            raise ValueError("request_id and answer are required")

        req = self.db.get_request(request_id)
        if not req:
            return None

        # Update request
        req['answer'] = answer
        req['status'] = 'resolved'
        req['resolved_at'] = datetime.utcnow().isoformat()
        req['resolved_by'] = resolver

        try:
            self.db.update_request(request_id, req)
        except Exception as e:
            print(f"[ERROR] Failed to update request: {e}")
            raise

        # Update knowledge base
        try:
            self.kb.learn_answer(req['question'], answer, req.get('category', 'general'))
        except Exception as e:
            print(f"[WARN] Failed to update knowledge base: {e}")
            # Continue even if KB update fails

        # Send follow-up to caller (simulated)
        try:
            follow_up = {
                'to': req['caller_phone'],
                'message': f"Answer to your question: {answer}"
            }
            self.db.log_message(follow_up)
        except Exception as e:
            print(f"[WARN] Failed to log follow-up message: {e}")

        return req

    def mark_timeouts(self) -> List[dict]:
        """
        Check all pending requests and mark timed-out ones as unresolved.
        Returns list of timed-out requests.
        """
        pending = self.db.get_requests_by_status('pending')
        now = datetime.utcnow()
        timed_out = []

        for r in pending:
            timeout_at_str = r.get('timeout_at')
            if not timeout_at_str:
                continue

            try:
                timeout_at = datetime.fromisoformat(timeout_at_str)
            except (ValueError, TypeError) as e:
                print(f"[WARN] Invalid timeout_at format for request {r.get('request_id')}: {e}")
                continue

            if timeout_at < now:
                r['status'] = 'unresolved'
                r['resolved_at'] = datetime.utcnow().isoformat()
                r['resolved_by'] = None

                try:
                    self.db.update_request(r['request_id'], r)
                    timed_out.append(r)
                except Exception as e:
                    print(f"[ERROR] Failed to mark request {r['request_id']} as timed out: {e}")

        return timed_out

    def get_pending_requests(self) -> List[dict]:
        """Get all pending requests"""
        return self.db.get_requests_by_status('pending')

    def get_request(self, request_id: str) -> Optional[dict]:
        """Get a specific request by ID"""
        return self.db.get_request(request_id)

    def get_resolved_requests(self) -> List[dict]:
        """Get all resolved requests"""
        return self.db.get_requests_by_status('resolved')

    def get_unresolved_requests(self) -> List[dict]:
        """Get all unresolved (timed out) requests"""
        return self.db.get_requests_by_status('unresolved')
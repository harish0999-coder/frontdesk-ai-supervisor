from typing import Optional
import re


class KnowledgeBase:
    """
    Basic knowledge base layer that tries static rules first then dynamic DB ones.
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self.static_info = {
            "hours": "We're open Monday to Saturday, 9 AM to 7 PM, and closed on Sundays.",
            "location": "123 Beauty Street, Downtown.",
            "services": "Haircuts, coloring, highlights, styling, manicures, pedicures, and facials.",
            "booking": "Book online at example.com/book or call 555-0123.",
            "prices_haircut": "Haircuts start at $25.",
            "prices_color": "Coloring services start at $60.",
            "cancellation": "Cancel or reschedule at least 24 hours in advance."
        }

    def lookup(self, question: str) -> Optional[str]:
        """
        Look up an answer to a question. Checks static KB first, then dynamic.
        Returns answer string if found, None otherwise.
        """
        if not question:
            return None

        q = question.lower().strip()

        # Check static knowledge base first
        static_answer = self._check_static(q)
        if static_answer:
            return static_answer

        # Check dynamic knowledge base (learned answers)
        dynamic_answer = self.db.search_knowledge(question)
        if dynamic_answer:
            return dynamic_answer

        return None

    def _check_static(self, question_lower: str) -> Optional[str]:
        """Check static knowledge base with keyword matching"""
        q = question_lower

        # Hours/Opening times
        if any(keyword in q for keyword in ["hour", "open", "opening", "close", "timing", "time"]):
            if not any(k in q for k in ["book", "appointment"]):  # avoid matching "book opening"
                return self.static_info["hours"]

        # Location/Address
        if any(keyword in q for keyword in ["where", "location", "address", "find you", "directions"]):
            return f"We're located at {self.static_info['location']}"

        # Services offered
        if any(keyword in q for keyword in ["service", "what do you", "what can", "offer", "provide", "do you do"]):
            # Check if asking about specific service not in our list
            if not any(specific in q for specific in ["tattoo", "piercing", "botox", "laser"]):
                return self.static_info["services"]

        # Booking/Reservation
        if any(keyword in q for keyword in ["book", "booking", "reserve", "reservation", "appointment", "schedule"]):
            if not any(k in q for k in ["cancel", "change", "reschedule"]):  # don't match cancellation
                return self.static_info["booking"]

        # Haircut prices
        if re.search(r"\b(haircut|cut|trim)\b", q) and any(k in q for k in ["price", "cost", "much", "charge", "fee"]):
            return self.static_info["prices_haircut"]

        # Color prices
        if re.search(r"\b(color|dye|highlight|tint)\b", q) and any(
                k in q for k in ["price", "cost", "much", "charge", "fee"]):
            return self.static_info["prices_color"]

        # Cancellation policy
        if any(keyword in q for keyword in ["cancel", "reschedule", "change appointment", "modify appointment"]):
            return self.static_info["cancellation"]

        return None

    def learn_answer(self, question: str, answer: str, category: str = 'general'):
        """
        Learn a new answer by storing it in the dynamic knowledge base.
        Called when supervisor resolves a request.
        """
        if not question or not answer:
            raise ValueError("Question and answer are required")

        try:
            self.db.add_to_knowledge_base({
                'question': question,
                'answer': answer,
                'category': category
            })
        except Exception as e:
            print(f"[KB] Error learning answer: {e}")
            raise

    def get_all_knowledge(self) -> list:
        """Get all learned knowledge entries"""
        return self.db.list_knowledge()
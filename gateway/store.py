import logging
import threading
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone

from gateway.models.review import AuditLog, PullRequestReview

logger = logging.getLogger(__name__)


class ReviewStore:
    """
    Thread-safe in-memory & file-backed store for PR reviews, audit logs,
    and webhook idempotency tracking.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._reviews: Dict[str, PullRequestReview] = {}
        self._processed_events: Dict[str, str] = {}  # idempotency key -> review_id
        self._logs: List[AuditLog] = []

    def get_review(self, review_id_or_pr: str) -> Optional[PullRequestReview]:
        with self._lock:
            # Direct match by review id (e.g. pr-142 or rev_...)
            if review_id_or_pr in self._reviews:
                return self._reviews[review_id_or_pr]
            
            # Match by PR number (numeric string or pr-X)
            clean_id = review_id_or_pr.replace("pr-", "")
            for rev in self._reviews.values():
                if str(rev.meta.prNumber) == clean_id or rev.meta.id == review_id_or_pr:
                    return rev
            return None

    def list_reviews(self) -> List[PullRequestReview]:
        with self._lock:
            # Return sorted by updatedAt descending
            return sorted(
                list(self._reviews.values()),
                key=lambda r: r.meta.updatedAt,
                reverse=True,
            )

    def save_review(self, review: PullRequestReview):
        with self._lock:
            self._reviews[review.meta.id] = review
            # Also key by pr number for quick lookup
            self._reviews[f"pr-{review.meta.prNumber}"] = review

    def is_event_processed(self, idempotency_key: str) -> Optional[str]:
        with self._lock:
            return self._processed_events.get(idempotency_key)

    def record_processed_event(self, idempotency_key: str, review_id: str):
        with self._lock:
            self._processed_events[idempotency_key] = review_id

    def add_log(
        self,
        service: str,
        level: str,
        message: str,
        review_id: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        log_entry = AuditLog(
            id=f"log-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            service=service,
            level=level,
            message=message,
            review_id=review_id,
            request_id=request_id,
            details=details,
        )
        with self._lock:
            self._logs.insert(0, log_entry)
            # Keep up to 1000 logs
            if len(self._logs) > 1000:
                self._logs.pop()

    def get_logs(self, limit: int = 100) -> List[AuditLog]:
        with self._lock:
            return list(self._logs[:limit])


# Global singleton instance
store = ReviewStore()

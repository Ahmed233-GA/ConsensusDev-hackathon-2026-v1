import logging
import threading
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone

from gateway.models.review import AuditLog, PullRequestReview
from gateway.database import (
    save_review_record,
    get_all_reviews_from_db,
    get_review_by_id_from_db,
    save_audit_log_to_db,
    get_audit_logs_from_db,
)

logger = logging.getLogger("gateway.store")


class ReviewStore:
    """
    Thread-safe store for PR reviews, audit logs, and webhook idempotency tracking.
    SQLite database serves as the source of truth for persistent historical records.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._reviews: Dict[str, PullRequestReview] = {}
        self._processed_events: Dict[str, str] = {}  # idempotency key -> review_id
        self._logs: List[AuditLog] = []

    def get_review(self, review_id_or_pr: str) -> Optional[PullRequestReview]:
        with self._lock:
            # 1. Direct match by review id (e.g. pr-142 or rev_...)
            if review_id_or_pr in self._reviews:
                return self._reviews[review_id_or_pr]
            
            # 2. Match by PR number in memory
            clean_id = review_id_or_pr.replace("pr-", "")
            for rev in self._reviews.values():
                if str(rev.meta.prNumber) == clean_id or rev.meta.id == review_id_or_pr:
                    return rev

        # 3. Fallback to Database persistence
        try:
            target_id = review_id_or_pr if review_id_or_pr.startswith("pr-") else f"pr-{review_id_or_pr}"
            db_data = get_review_by_id_from_db(target_id)
            if not db_data and not review_id_or_pr.startswith("pr-"):
                db_data = get_review_by_id_from_db(review_id_or_pr)
            
            if db_data:
                canonical = PullRequestReview(**db_data)
                with self._lock:
                    self._reviews[canonical.meta.id] = canonical
                    self._reviews[f"pr-{canonical.meta.prNumber}"] = canonical
                return canonical
        except Exception as e:
            logger.warning(f"Failed to fetch review '{review_id_or_pr}' from database: {e}")

        return None

    def list_reviews(self) -> List[PullRequestReview]:
        # Fetch from database as primary persistent source of truth
        try:
            db_records = get_all_reviews_from_db()
            if db_records:
                reviews_list = []
                with self._lock:
                    for item in db_records:
                        try:
                            rev = PullRequestReview(**item)
                            reviews_list.append(rev)
                            self._reviews[rev.meta.id] = rev
                            self._reviews[f"pr-{rev.meta.prNumber}"] = rev
                        except Exception as parse_err:
                            logger.error(f"Error parsing DB review record: {parse_err}")
                return reviews_list
        except Exception as e:
            logger.warning(f"Failed to query reviews from DB: {e}")

        with self._lock:
            return sorted(
                list(self._reviews.values()),
                key=lambda r: r.meta.updatedAt,
                reverse=True,
            )

    def save_review(self, review: PullRequestReview):
        with self._lock:
            self._reviews[review.meta.id] = review
            self._reviews[f"pr-{review.meta.prNumber}"] = review

        # Persist automatically to SQLite database
        try:
            dump_data = review.model_dump() if hasattr(review, "model_dump") else review.dict()
            save_review_record(dump_data)
        except Exception as e:
            logger.error(f"Failed to persist review '{review.meta.id}' to database: {e}")

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
        log_id = f"log-{uuid.uuid4().hex[:8]}"
        now_ts = datetime.now(timezone.utc).isoformat()
        log_entry = AuditLog(
            id=log_id,
            timestamp=now_ts,
            service=service,
            level=level,
            message=message,
            review_id=review_id,
            request_id=request_id,
            details=details,
        )
        with self._lock:
            self._logs.insert(0, log_entry)
            if len(self._logs) > 1000:
                self._logs.pop()

        # Persist automatically to DB
        try:
            save_audit_log_to_db(
                service=service,
                level=level,
                message=message,
                review_id=review_id,
                request_id=request_id,
                metadata=details,
            )
        except Exception as e:
            logger.error(f"Failed to persist audit log to DB: {e}")

    def get_logs(self, limit: int = 100) -> List[AuditLog]:
        try:
            db_logs = get_audit_logs_from_db(limit=limit)
            if db_logs:
                parsed_logs = []
                for l in db_logs:
                    parsed_logs.append(
                        AuditLog(
                            id=l.get("id"),
                            timestamp=l.get("timestamp"),
                            service=l.get("service"),
                            level=l.get("level"),
                            message=l.get("message"),
                            review_id=l.get("review_id"),
                            request_id=l.get("request_id"),
                            details=l.get("metadata") if isinstance(l.get("metadata"), dict) else None,
                        )
                    )
                return parsed_logs
        except Exception as e:
            logger.warning(f"Failed to query audit logs from DB: {e}")

        with self._lock:
            return list(self._logs[:limit])


# Global singleton instance
store = ReviewStore()

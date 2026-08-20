import os
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session
from gateway.models.db import Base, User, ReviewRecord, FindingRecord, ApprovalEventRecord, AuditLogRecord

logger = logging.getLogger("gateway.database")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///consensusdev.db")

# For SQLite, enable check_same_thread=False for FastAPI concurrency
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Idempotently create all database tables.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully at {DATABASE_URL}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db() -> Session:
    """
    FastAPI dependency to provide a transactional database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# Database Repository Functions
# ==========================================

def save_review_record(review_dict: Dict[str, Any], db: Optional[Session] = None) -> ReviewRecord:
    """
    Save or update a PullRequestReview canonical dictionary in the database.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        meta = review_dict.get("meta", {})
        consensus = review_dict.get("consensus", {})
        findings_data = review_dict.get("findings", [])

        review_id = meta.get("id") or f"pr-{meta.get('prNumber', 0)}"
        pr_number = meta.get("prNumber", 0)
        title = meta.get("title", f"PR #{pr_number}")
        author_obj = meta.get("author", {})
        author = author_obj.get("name") or author_obj.get("username") or "unknown"
        source_branch = meta.get("sourceBranch", "main")
        target_branch = meta.get("targetBranch", "main")
        commit_hash = meta.get("commitHash", "")
        short_hash = meta.get("shortHash", commit_hash[:7] if commit_hash else "0000000")
        repo = meta.get("repo", "ConsensusDev")
        consensus_decision = consensus.get("decision", "rejected")
        score = consensus.get("score", 0)
        status = review_dict.get("status", "COMPLETED")
        merged = bool(review_dict.get("merged", False))
        review_time = float(review_dict.get("reviewTimeSeconds", 0.0))

        raw_payload = json.dumps(review_dict)

        existing = db.query(ReviewRecord).filter(ReviewRecord.id == review_id).first()
        if existing:
            existing.pr_number = pr_number
            existing.title = title
            existing.author = author
            existing.source_branch = source_branch
            existing.target_branch = target_branch
            existing.commit_hash = commit_hash
            existing.short_hash = short_hash
            existing.repo = repo
            existing.consensus_decision = consensus_decision
            existing.score = score
            existing.status = status
            existing.merged = merged
            existing.review_time_seconds = review_time
            existing.raw_payload = raw_payload
            existing.updated_at = datetime.now(timezone.utc)
            record = existing
        else:
            record = ReviewRecord(
                id=review_id,
                pr_number=pr_number,
                title=title,
                author=author,
                source_branch=source_branch,
                target_branch=target_branch,
                commit_hash=commit_hash,
                short_hash=short_hash,
                repo=repo,
                consensus_decision=consensus_decision,
                score=score,
                status=status,
                merged=merged,
                review_time_seconds=review_time,
                raw_payload=raw_payload,
            )
            db.add(record)

        # Clear existing findings and persist new ones
        db.query(FindingRecord).filter(FindingRecord.review_id == review_id).delete()
        for idx, f in enumerate(findings_data):
            f_dict = f if isinstance(f, dict) else f.dict() if hasattr(f, "dict") else {}
            f_id = f_dict.get("id") or f"find-{review_id}-{idx+1}"
            finding_rec = FindingRecord(
                id=f_id,
                review_id=review_id,
                severity=f_dict.get("severity", "high"),
                tool=f_dict.get("tool", "Scanner"),
                rule_id=f_dict.get("ruleId") or f_dict.get("rule_id", "VULN_RULE"),
                engine=f_dict.get("engine", "fallback_regex_ast"),
                file=f_dict.get("file", "app.py"),
                line=int(f_dict.get("line", 1)),
                description=f_dict.get("description", ""),
                recommendation=f_dict.get("recommendation"),
            )
            db.add(finding_rec)

        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving review record {review_dict.get('meta', {}).get('id')}: {e}")
        raise
    finally:
        if should_close:
            db.close()


def get_all_reviews_from_db(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all review records from the database ordered by updated_at descending.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        records = db.query(ReviewRecord).order_by(desc(ReviewRecord.updated_at)).all()
        return [r.to_canonical_dict() for r in records]
    finally:
        if should_close:
            db.close()


def get_review_by_id_from_db(review_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific review record by ID from the database.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        record = db.query(ReviewRecord).filter(ReviewRecord.id == review_id).first()
        if record:
            return record.to_canonical_dict()
        return None
    finally:
        if should_close:
            db.close()


def save_audit_log_to_db(
    service: str,
    level: str,
    message: str,
    event: Optional[str] = None,
    actor: str = "system",
    review_id: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> AuditLogRecord:
    """
    Persist an audit log entry in the database.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        import uuid
        log_id = f"log-{uuid.uuid4().hex[:12]}"
        meta_str = json.dumps(metadata) if metadata else None

        record = AuditLogRecord(
            id=log_id,
            service=service,
            level=level,
            event=event,
            actor=actor,
            review_id=review_id,
            request_id=request_id,
            message=message,
            metadata_json=meta_str,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        db.rollback()
        logger.error(f"Error persisting audit log: {e}")
        raise
    finally:
        if should_close:
            db.close()


def get_audit_logs_from_db(limit: int = 100, db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Retrieve recent audit logs from the database.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        records = db.query(AuditLogRecord).order_by(desc(AuditLogRecord.timestamp)).limit(limit).all()
        return [r.to_dict() for r in records]
    finally:
        if should_close:
            db.close()


def get_dashboard_stats_from_db(db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Calculate real aggregated statistics directly from the reviews table.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        total_reviews = db.query(func.count(ReviewRecord.id)).scalar() or 0
        if total_reviews == 0:
            return {
                "totalReviews": 0,
                "approvedCount": 0,
                "rejectedCount": 0,
                "approvalRate": 0.0,
                "avgScore": 0.0,
                "avgReviewTimeSeconds": 0.0,
                "totalFindings": 0,
                "activeAgents": 4,
                "systemStatus": "ONLINE",
            }

        approved_count = db.query(func.count(ReviewRecord.id)).filter(ReviewRecord.consensus_decision == "approved").scalar() or 0
        rejected_count = db.query(func.count(ReviewRecord.id)).filter(ReviewRecord.consensus_decision.in_(["rejected", "blocked"])).scalar() or 0
        avg_score = db.query(func.avg(ReviewRecord.score)).scalar() or 0.0
        avg_review_time = db.query(func.avg(ReviewRecord.review_time_seconds)).scalar() or 0.0
        total_findings = db.query(func.count(FindingRecord.id)).scalar() or 0

        approval_rate = (approved_count / total_reviews * 100.0) if total_reviews > 0 else 0.0

        return {
            "totalReviews": total_reviews,
            "approvedCount": approved_count,
            "rejectedCount": rejected_count,
            "approvalRate": round(approval_rate, 1),
            "avgScore": round(float(avg_score), 1),
            "avgReviewTimeSeconds": round(float(avg_review_time), 2),
            "totalFindings": total_findings,
            "activeAgents": 4,
            "systemStatus": "ONLINE",
        }
    finally:
        if should_close:
            db.close()

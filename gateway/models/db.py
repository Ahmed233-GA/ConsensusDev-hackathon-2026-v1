from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """
    Operator / Admin account for ConsensusDev authentication.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="admin", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class ReviewRecord(Base):
    """
    Persistent record of a Pull Request review evaluation.
    """
    __tablename__ = "reviews"

    id = Column(String(64), primary_key=True, index=True)  # e.g. "pr-101"
    pr_number = Column(Integer, index=True, nullable=False)
    title = Column(String(256), nullable=False)
    author = Column(String(128), nullable=False)
    source_branch = Column(String(128), nullable=False)
    target_branch = Column(String(128), default="main", nullable=False)
    commit_hash = Column(String(64), nullable=False)
    short_hash = Column(String(16), nullable=False)
    repo = Column(String(256), nullable=False)
    consensus_decision = Column(String(32), nullable=False)  # "approved", "rejected", "blocked"
    score = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="COMPLETED", nullable=False)
    merged = Column(Boolean, default=False, nullable=False)
    review_time_seconds = Column(Float, default=0.0, nullable=False)
    raw_payload = Column(Text, nullable=False)  # Full JSON of canonical PullRequestReview model
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    findings = relationship("FindingRecord", back_populates="review", cascade="all, delete-orphan")
    approval_events = relationship("ApprovalEventRecord", back_populates="review", cascade="all, delete-orphan")

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Deserialize stored raw canonical review payload."""
        try:
            return json.loads(self.raw_payload)
        except Exception:
            return {
                "meta": {
                    "id": self.id,
                    "prNumber": self.pr_number,
                    "title": self.title,
                    "author": {"name": self.author, "username": self.author},
                    "commitHash": self.commit_hash,
                    "shortHash": self.short_hash,
                    "sourceBranch": self.source_branch,
                    "targetBranch": self.target_branch,
                    "repo": self.repo,
                    "createdAt": self.created_at.isoformat() if self.created_at else None,
                },
                "consensus": {
                    "score": self.score,
                    "decision": self.consensus_decision,
                    "gates": {"security": "passed", "qa": "passed", "evidence": "verified"},
                    "summary": f"Review for PR #{self.pr_number}",
                    "blocking_reasons": [],
                },
                "agents": [],
                "findings": [],
                "merged": self.merged,
                "reviewTimeSeconds": self.review_time_seconds,
                "status": "APPROVED" if self.consensus_decision == "approved" else "BLOCKED",
            }


class FindingRecord(Base):
    """
    Security vulnerability or code quality finding associated with a review.
    """
    __tablename__ = "findings"

    id = Column(String(64), primary_key=True, index=True)
    review_id = Column(String(64), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(String(32), default="high", nullable=False)  # "critical", "high", "medium", "low"
    tool = Column(String(64), nullable=False)
    rule_id = Column(String(64), nullable=False)
    engine = Column(String(64), default="fallback_regex_ast", nullable=False)
    file = Column(String(256), default="app.py", nullable=False)
    line = Column(Integer, default=1, nullable=False)
    description = Column(Text, default="", nullable=False)
    recommendation = Column(Text, nullable=True)

    review = relationship("ReviewRecord", back_populates="findings")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "review_id": self.review_id,
            "severity": self.severity,
            "tool": self.tool,
            "ruleId": self.rule_id,
            "engine": self.engine,
            "file": self.file,
            "line": self.line,
            "description": self.description,
            "recommendation": self.recommendation,
        }


class ApprovalEventRecord(Base):
    """
    Human-in-the-loop (HITL) manual approval or override event.
    """
    __tablename__ = "approval_events"

    id = Column(String(64), primary_key=True, index=True)
    review_id = Column(String(64), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    actor = Column(String(128), nullable=False)
    action = Column(String(32), nullable=False)  # "approved", "rejected", "overridden"
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    review = relationship("ReviewRecord", back_populates="approval_events")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "review_id": self.review_id,
            "actor": self.actor,
            "action": self.action,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class AuditLogRecord(Base):
    """
    Persistent audit log record for security, lifecycle, and orchestration events.
    """
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    service = Column(String(64), nullable=False)
    level = Column(String(16), default="INFO", nullable=False)
    event = Column(String(64), nullable=True)
    actor = Column(String(128), default="system", nullable=False)
    review_id = Column(String(64), nullable=True, index=True)
    request_id = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        meta = None
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except Exception:
                meta = self.metadata_json

        return {
            "id": self.id,
            "service": self.service,
            "level": self.level,
            "event": self.event,
            "actor": self.actor,
            "review_id": self.review_id,
            "request_id": self.request_id,
            "message": self.message,
            "metadata": meta,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

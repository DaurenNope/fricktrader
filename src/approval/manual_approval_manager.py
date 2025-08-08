"""
Manual Approval System for Trading Signals
Intercepts Freqtrade signals and queues them for manual review
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import time
from enum import Enum

logger = logging.getLogger(__name__)

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class SignalApproval:
    """Data class for signal approval requests"""
    id: Optional[int] = None
    pair: str = ""
    signal_type: str = ""  # 'BUY', 'SELL'
    technical_score: float = 0.0
    onchain_score: float = 0.0
    sentiment_score: float = 0.0
    composite_score: float = 0.0
    price: float = 0.0
    volume: float = 0.0
    analysis_data: Dict = None
    reasoning: str = ""
    timestamp: datetime = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: str = ""
    approval_timestamp: datetime = None
    approval_reason: str = ""
    executed: bool = False
    trade_id: Optional[int] = None
    expires_at: datetime = None

class ManualApprovalManager:
    """
    Manages manual approval of trading signals
    
    Features:
    - Signal interception and queuing
    - SQLite storage for persistence
    - Automatic expiration of old signals
    - Batch approval capabilities
    - Detailed signal analysis
    """
    
    def __init__(self, db_path: str = "signal_approvals.db", config: Optional[Dict] = None):
        self.db_path = db_path
        self.config = config or {}
        self.lock = threading.Lock()
        
        # Configuration
        self.signal_expiry_hours = self.config.get('signal_expiry_hours', 4)  # 4 hours default
        self.auto_cleanup_interval = self.config.get('auto_cleanup_interval', 3600)  # 1 hour
        
        # Initialize database
        self._init_database()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_signals, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("✅ Manual Approval Manager initialized")
    
    def _init_database(self):
        """Initialize SQLite database for signal approvals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS signal_approvals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        technical_score REAL DEFAULT 0.0,
                        onchain_score REAL DEFAULT 0.0,
                        sentiment_score REAL DEFAULT 0.0,
                        composite_score REAL DEFAULT 0.0,
                        price REAL DEFAULT 0.0,
                        volume REAL DEFAULT 0.0,
                        analysis_data TEXT,  -- JSON
                        reasoning TEXT DEFAULT '',
                        timestamp DATETIME NOT NULL,
                        status TEXT DEFAULT 'pending',
                        approved_by TEXT DEFAULT '',
                        approval_timestamp DATETIME,
                        approval_reason TEXT DEFAULT '',
                        executed BOOLEAN DEFAULT FALSE,
                        trade_id INTEGER,
                        expires_at DATETIME NOT NULL
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON signal_approvals(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON signal_approvals(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON signal_approvals(expires_at)")
                
                conn.commit()
                logger.info("📊 Signal approvals database initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def intercept_signal(self, signal_data: Dict) -> bool:
        """
        Intercept a trading signal and queue it for manual approval
        
        Args:
            signal_data: Dictionary containing signal information
            
        Returns:
            False to block automatic execution, True to allow
        """
        try:
            with self.lock:
                # Create signal approval object
                approval = SignalApproval(
                    pair=signal_data.get('pair', ''),
                    signal_type=signal_data.get('signal_type', ''),
                    technical_score=signal_data.get('technical_score', 0.0),
                    onchain_score=signal_data.get('onchain_score', 0.0),
                    sentiment_score=signal_data.get('sentiment_score', 0.0),
                    composite_score=signal_data.get('composite_score', 0.0),
                    price=signal_data.get('price', 0.0),
                    volume=signal_data.get('volume', 0.0),
                    analysis_data=signal_data.get('analysis_data', {}),
                    reasoning=signal_data.get('reasoning', ''),
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours)
                )
                
                # Store in database
                approval_id = self._store_approval(approval)
                
                if approval_id:
                    logger.info(f"🔒 Signal intercepted for manual approval: {approval.pair} {approval.signal_type} (ID: {approval_id})")
                    
                    # Send notification (could be email, webhook, etc.)
                    self._send_approval_notification(approval)
                    
                    return False  # Block automatic execution
                else:
                    logger.error("Failed to store signal approval")
                    return True  # Allow execution if storage fails
                    
        except Exception as e:
            logger.error(f"Error intercepting signal: {e}")
            return True  # Allow execution on error
    
    def _store_approval(self, approval: SignalApproval) -> Optional[int]:
        """Store signal approval in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO signal_approvals (
                        pair, signal_type, technical_score, onchain_score, sentiment_score,
                        composite_score, price, volume, analysis_data, reasoning,
                        timestamp, status, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    approval.pair, approval.signal_type, approval.technical_score,
                    approval.onchain_score, approval.sentiment_score, approval.composite_score,
                    approval.price, approval.volume, json.dumps(approval.analysis_data or {}),
                    approval.reasoning, approval.timestamp, approval.status.value, approval.expires_at
                ))
                
                approval_id = cursor.lastrowid
                conn.commit()
                return approval_id
                
        except Exception as e:
            logger.error(f"Error storing approval: {e}")
            return None
    
    def get_pending_signals(self) -> List[SignalApproval]:
        """Get all pending signal approvals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM signal_approvals 
                    WHERE status = 'pending' AND expires_at > ?
                    ORDER BY timestamp DESC
                """, (datetime.now(),))
                
                rows = cursor.fetchall()
                approvals = []
                
                for row in rows:
                    approval = SignalApproval(
                        id=row['id'],
                        pair=row['pair'],
                        signal_type=row['signal_type'],
                        technical_score=row['technical_score'],
                        onchain_score=row['onchain_score'],
                        sentiment_score=row['sentiment_score'],
                        composite_score=row['composite_score'],
                        price=row['price'],
                        volume=row['volume'],
                        analysis_data=json.loads(row['analysis_data'] or '{}'),
                        reasoning=row['reasoning'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        status=ApprovalStatus(row['status']),
                        approved_by=row['approved_by'],
                        approval_timestamp=datetime.fromisoformat(row['approval_timestamp']) if row['approval_timestamp'] else None,
                        approval_reason=row['approval_reason'],
                        executed=bool(row['executed']),
                        trade_id=row['trade_id'],
                        expires_at=datetime.fromisoformat(row['expires_at'])
                    )
                    approvals.append(approval)
                
                return approvals
                
        except Exception as e:
            logger.error(f"Error getting pending signals: {e}")
            return []
    
    def approve_signal(self, signal_id: int, approved_by: str = "user", reason: str = "") -> bool:
        """
        Approve a signal for execution
        
        Args:
            signal_id: ID of the signal to approve
            approved_by: Who approved the signal
            reason: Reason for approval
            
        Returns:
            True if approved successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update approval status
                cursor.execute("""
                    UPDATE signal_approvals 
                    SET status = 'approved', approved_by = ?, approval_timestamp = ?, approval_reason = ?
                    WHERE id = ? AND status = 'pending'
                """, (approved_by, datetime.now(), reason, signal_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"✅ Signal {signal_id} approved by {approved_by}")
                    
                    # Execute the trade (this would integrate with Freqtrade)
                    self._execute_approved_trade(signal_id)
                    
                    return True
                else:
                    logger.warning(f"Signal {signal_id} not found or already processed")
                    return False
                    
        except Exception as e:
            logger.error(f"Error approving signal {signal_id}: {e}")
            return False
    
    def reject_signal(self, signal_id: int, rejected_by: str = "user", reason: str = "") -> bool:
        """
        Reject a signal
        
        Args:
            signal_id: ID of the signal to reject
            rejected_by: Who rejected the signal
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update rejection status
                cursor.execute("""
                    UPDATE signal_approvals 
                    SET status = 'rejected', approved_by = ?, approval_timestamp = ?, approval_reason = ?
                    WHERE id = ? AND status = 'pending'
                """, (rejected_by, datetime.now(), reason, signal_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"❌ Signal {signal_id} rejected by {rejected_by}: {reason}")
                    return True
                else:
                    logger.warning(f"Signal {signal_id} not found or already processed")
                    return False
                    
        except Exception as e:
            logger.error(f"Error rejecting signal {signal_id}: {e}")
            return False
    
    def batch_approve(self, signal_ids: List[int], approved_by: str = "user", reason: str = "") -> int:
        """
        Approve multiple signals at once
        
        Returns:
            Number of signals successfully approved
        """
        approved_count = 0
        
        for signal_id in signal_ids:
            if self.approve_signal(signal_id, approved_by, reason):
                approved_count += 1
        
        logger.info(f"✅ Batch approved {approved_count}/{len(signal_ids)} signals")
        return approved_count
    
    def _execute_approved_trade(self, signal_id: int):
        """
        Execute an approved trade
        This would integrate with Freqtrade's trading engine
        """
        try:
            # Get signal details
            approval = self._get_approval_by_id(signal_id)
            if not approval:
                return
            
            # Mark as executed (placeholder - real implementation would call Freqtrade)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE signal_approvals 
                    SET executed = TRUE
                    WHERE id = ?
                """, (signal_id,))
                conn.commit()
            
            logger.info(f"🚀 Executed approved trade: {approval.pair} {approval.signal_type}")
            
        except Exception as e:
            logger.error(f"Error executing approved trade {signal_id}: {e}")
    
    def _get_approval_by_id(self, signal_id: int) -> Optional[SignalApproval]:
        """Get approval by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM signal_approvals WHERE id = ?", (signal_id,))
                row = cursor.fetchone()
                
                if row:
                    return SignalApproval(
                        id=row['id'],
                        pair=row['pair'],
                        signal_type=row['signal_type'],
                        technical_score=row['technical_score'],
                        onchain_score=row['onchain_score'],
                        sentiment_score=row['sentiment_score'],
                        composite_score=row['composite_score'],
                        price=row['price'],
                        volume=row['volume'],
                        analysis_data=json.loads(row['analysis_data'] or '{}'),
                        reasoning=row['reasoning'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        status=ApprovalStatus(row['status']),
                        expires_at=datetime.fromisoformat(row['expires_at'])
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting approval {signal_id}: {e}")
            return None
    
    def _cleanup_expired_signals(self):
        """Background thread to clean up expired signals"""
        while True:
            try:
                time.sleep(self.auto_cleanup_interval)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Mark expired signals
                    cursor.execute("""
                        UPDATE signal_approvals 
                        SET status = 'expired'
                        WHERE status = 'pending' AND expires_at <= ?
                    """, (datetime.now(),))
                    
                    expired_count = cursor.rowcount
                    
                    if expired_count > 0:
                        conn.commit()
                        logger.info(f"🕐 Marked {expired_count} signals as expired")
                
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
    
    def _send_approval_notification(self, approval: SignalApproval):
        """
        Send notification about new signal requiring approval
        This could be email, webhook, push notification, etc.
        """
        try:
            # Placeholder for notification system
            logger.info(f"📧 Notification sent for signal approval: {approval.pair} {approval.signal_type}")
            
        except Exception as e:
            logger.error(f"Error sending approval notification: {e}")
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Get statistics about signal approvals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get counts by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM signal_approvals 
                    GROUP BY status
                """)
                
                status_counts = dict(cursor.fetchall())
                
                # Get recent activity
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM signal_approvals 
                    WHERE timestamp >= ?
                """, (datetime.now() - timedelta(hours=24),))
                
                recent_count = cursor.fetchone()[0]
                
                return {
                    'status_counts': status_counts,
                    'recent_24h': recent_count,
                    'pending_count': status_counts.get('pending', 0),
                    'approved_count': status_counts.get('approved', 0),
                    'rejected_count': status_counts.get('rejected', 0),
                    'expired_count': status_counts.get('expired', 0)
                }
                
        except Exception as e:
            logger.error(f"Error getting approval stats: {e}")
            return {}
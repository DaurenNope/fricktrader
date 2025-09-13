"""
Manual Approval System

Provides manual approval workflows for trading signals,
ensuring human oversight of automated trading decisions.
"""

from .manual_approval_manager import (ApprovalStatus, ManualApprovalManager,
                                      SignalApproval)

__all__ = ["ManualApprovalManager", "ApprovalStatus", "SignalApproval"]

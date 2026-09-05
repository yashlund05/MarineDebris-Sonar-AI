from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class PromotionAuditRecord(BaseModel):
    timestamp: str
    action: str
    status: str
    target_model_id: str
    overall_pass: bool
    rejection_reasons: List[str]
    allowed_actions: List[str]

class PromotionAuditResponse(BaseModel):
    current_production_model_id: str
    current_production_sha256: str
    promotion_policy: str
    audit_records: List[PromotionAuditRecord]

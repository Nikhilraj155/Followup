import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict

class StructuredLogger:
    def __init__(self, name: str = "followup_ai"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_event(self, event_type: str, details: Dict[str, Any], level: str = "info"):
        # Sanitize sensitive fields before logging
        sanitized = {}
        sensitive_keys = {"token", "access_token", "refresh_token", "password", "api_key", "secret", "credentials"}
        for k, v in details.items():
            if any(s in k.lower() for s in sensitive_keys):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = v

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": sanitized
        }
        
        msg = json.dumps(payload)
        if level == "error":
            self.logger.error(msg)
        elif level == "warning":
            self.logger.warning(msg)
        else:
            self.logger.info(msg)

logger = StructuredLogger()

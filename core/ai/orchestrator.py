import json
import time
from .clients import get_ai_client

class AIOrchestrator:
    def __init__(self):
        self.client = get_ai_client()
        self.last_analysis_time = 0
        self.cooldown_seconds = 30 # Data Throttling: لا ترسل طلبات أكثر من مرة كل 30 ثانية
        
    def should_analyze(self, cpu_percent, ram_percent):
        """يقرر ما إذا كان الوضع يستدعي تحليلاً من الذكاء الاصطناعي"""
        now = time.time()
        if (now - self.last_analysis_time) < self.cooldown_seconds:
            return False
            
        # اختناق (Anomaly) إذا كان المعالج أو الذاكرة فوق 85%
        if cpu_percent > 85.0 or ram_percent > 85.0:
            return True
            
        return False

    def trigger_analysis(self, system_metrics, top_processes):
        """يقوم بصياغة القالب وإرساله للنموذج"""
        self.last_analysis_time = time.time()
        
        # تحضير قالب JSON كما طلب في المواصفات
        payload = {
            "system_status": {
                "cpu_avg": round(system_metrics.get("cpu_percent", 0), 1),
                "ram_usage_gb": round(system_metrics.get("ram_used_mb", 0) / 1024, 2),
                "ram_percent": round(system_metrics.get("ram_percent", 0), 1)
            },
            "top_offending_processes": top_processes[:5] # نرسل أعلى 5 عمليات فقط لتخفيف الحجم
        }
        
        payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
        return self.client.analyze(payload_str)

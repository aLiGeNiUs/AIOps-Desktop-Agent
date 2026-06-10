import json
import requests

class AIBaseClient:
    def analyze(self, payload_json: str) -> str:
        raise NotImplementedError()

class OllamaClient(AIBaseClient):
    def __init__(self, config):
        self.url = config.get("url", "http://localhost:11434/api/generate")
        self.model = config.get("model", "qwen2.5:0.5b")

    def analyze(self, payload_json: str) -> str:
        prompt = (
            "تحليل أداء النظام:\n"
            "بناءً على بيانات الحالة المرفقة بصيغة JSON، قم بإجراء تشخيص فوري للمشكلة ومسبباتها.\n"
            "تعليمات هامة جداً: يجب أن تكون الإجابة باللغة العربية فقط (Arabic Language Only). لا تستخدم اللغة الصينية أو الإنجليزية.\n"
            "أجب باختصار شديد وفي بضعة أسطر وبصيغة مهيكلة تحتوي على النقاط التالية فقط:\n"
            "1. التشخيص (Diagnosis): ما هي المشكلة الحالية؟\n"
            "2. التنبؤ بالاختناق (Prediction): ما هو التهديد المتوقع للأداء في حال استمرار الوضع؟\n"
            "3. التوصية بالحل (Recommendation): الإجراء البرمجي المقترح فوراً (مثال: إيقاف العملية رقم PID).\n\n"
            f"البيانات:\n{payload_json}"
        )
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(self.url, json=data, timeout=60)
            if response.status_code == 200:
                return response.json().get("response", "لا توجد استجابة صالحة.")
            else:
                error_msg = ""
                try:
                    error_msg = response.json().get("error", "")
                except:
                    error_msg = response.text
                return f"خطأ من Ollama ({response.status_code}): {error_msg}"
        except Exception as e:
            return f"فشل الاتصال بـ Ollama: {str(e)}"

class GeminiClient(AIBaseClient):
    def __init__(self, config):
        self.url = config.get("url", "")
        self.api_key = config.get("api_key", "")

    def analyze(self, payload_json: str) -> str:
        if not self.api_key:
            return "مفتاح API الخاص بـ Gemini غير متوفر في الإعدادات."
            
        url_with_key = f"{self.url}?key={self.api_key}"
        prompt = (
            "تحليل أداء النظام:\n"
            "بناءً على بيانات الحالة المرفقة بصيغة JSON، قم بإجراء تشخيص فوري للمشكلة ومسبباتها.\n"
            "تعليمات هامة جداً: يجب أن تكون الإجابة باللغة العربية فقط (Arabic Language Only). لا تستخدم اللغة الصينية أو الإنجليزية.\n"
            "أجب باختصار شديد وفي بضعة أسطر وبصيغة مهيكلة تحتوي على النقاط التالية فقط:\n"
            "1. التشخيص (Diagnosis): ما هي المشكلة الحالية؟\n"
            "2. التنبؤ بالاختناق (Prediction): ما هو التهديد المتوقع للأداء في حال استمرار الوضع؟\n"
            "3. التوصية بالحل (Recommendation): الإجراء البرمجي المقترح فوراً (مثال: إيقاف العملية رقم PID).\n\n"
            f"البيانات:\n{payload_json}"
        )
        
        data = {
            "contents": [{"parts":[{"text": prompt}]}]
        }
        
        try:
            response = requests.post(url_with_key, json=data, timeout=60)
            if response.status_code == 200:
                res_data = response.json()
                try:
                    return res_data['candidates'][0]['content']['parts'][0]['text']
                except KeyError:
                    return "استجابة غير متوقعة من Gemini."
            else:
                return f"خطأ من Gemini: {response.status_code}"
        except Exception as e:
            return f"فشل الاتصال بـ Gemini: {str(e)}"

def get_ai_client(config_path="config.json") -> AIBaseClient:
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            
        provider = config.get("ai_provider", "ollama")
        if provider == "gemini":
            return GeminiClient(config.get("gemini", {}))
        else:
            return OllamaClient(config.get("ollama", {}))
    except Exception:
        # Fallback to default Ollama
        return OllamaClient({"url": "http://localhost:11434/api/generate", "model": "qwen2.5:0.5b"})

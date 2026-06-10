# AIOps Desktop Agent 🤖💻

*(English documentation is available below)*

تطبيق سطح مكتب ذكي لمراقبة أداء نظام Linux بشكل لحظي، مدعوم بالذكاء الاصطناعي (Ollama/Gemini) لتشخيص المشاكل واقتراح الحلول الآمنة.

![AIOps Desktop Agent](https://via.placeholder.com/1000x700.png?text=AIOps+Desktop+Agent+Screenshot)

## الميزات الرئيسية (Features)
- 📊 **مراقبة لحظية (Real-time Monitoring):** رسم بياني فائق السرعة لاستهلاك الذاكرة والمعالج عبر نواة لينكس مباشرة (`/proc`).
- 🧠 **تحليل بالذكاء الاصطناعي (AI Insights):** يتصل بنماذج الذكاء الاصطناعي (مثل `qwen2.5:0.5b` عبر Ollama أو Gemini) لتحليل البيانات عند ارتفاع الضغط واستنتاج أسباب الاختناق.
- 🛡️ **القائمة البيضاء (Whitelisting):** حماية ذكية تمنع إغلاق عمليات النظام الأساسية (مثل `systemd` أو الواجهة الرسومية) لتجنب انهيار النظام.
- 🛑 **إنهاء آمن ومتدرج (Graceful Termination):** ميزة "الإصلاح الذكي" ترسل إشارة `SIGTERM` اللطيفة أولاً، وفي حال عدم الاستجابة يتم الإنهاء الإجباري `SIGKILL`.
- 🔍 **تفاصيل معمقة (Process Deep-Dive):** انقر نقراً مزدوجاً على أي عملية في الجدول لرؤية الأمر البرمجي الدقيق الذي شغلها.
- 🔔 **تنبيهات سطح المكتب:** إشعارات النظام للتنبيه في حال اكتشاف الذكاء الاصطناعي لاختناق بينما التطبيق يعمل في الخلفية.

## المتطلبات (Requirements)
للحصول على أفضل تجربة، نوصي بتثبيت `Ollama` محلياً للحفاظ على خصوصية بياناتك:
```bash
# تثبيت Ollama
curl -fsSL https://ollama.com/install.sh | sh

# تحميل النموذج الافتراضي الخفيف
ollama pull qwen2.5:0.5b
```

## التثبيت (Installation)

### الطريقة الأولى: من الكود المصدري (للمطورين)
```bash
git clone https://github.com/YourUsername/aiops-desktop-agent.git
cd aiops-desktop-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### الطريقة الثانية: التثبيت السريع كبرنامج مستقل (للمستخدمين)
يمكنك استخدام سكربت `install.sh` لتجميع التطبيق وتثبيته في قائمة برامج نظامك:
```bash
chmod +x install.sh
./install.sh
```

## عن المطور (About the Author)
**I Am knowledgist Hacker**  
حياتي مكرسة لنشر المعرفة في العلوم والتقنية، الذكاء الإصطناعي والأمن السيبراني.

© 2026 The hackers Ali Al-Kazaly (علي عاصف) – aLi GeNiUs  
🔗 [YouTube Channel: aLiGeNiUs.TheHackers](https://www.youtube.com/@aLiGeNiUs.TheHackers)

---

# AIOps Desktop Agent (English)

A smart desktop application for real-time Linux system performance monitoring, powered by AI (Ollama/Gemini) to diagnose bottlenecks and suggest safe fixes.

## Key Features
- 📊 **Real-time Monitoring:** Ultra-fast graphing of CPU and RAM usage directly from the Linux kernel (`/proc`).
- 🧠 **AI Insights:** Connects to AI models (e.g., `qwen2.5:0.5b` via Ollama) to analyze high-load scenarios and identify root causes.
- 🛡️ **Whitelisting:** Smart protection that prevents accidental termination of critical system processes.
- 🛑 **Graceful Termination:** "Smart Fix" sends a polite `SIGTERM` first before resorting to `SIGKILL`.
- 🔍 **Process Deep-Dive:** Double-click any process in the table to see its exact command-line arguments.
- 🔔 **Desktop Notifications:** System tray alerts when AI detects an issue.

## Installation & Build
You can run it directly using Python (see Arabic instructions above) or build it as a standalone Linux application:
```bash
chmod +x install.sh
./install.sh
```

## License
MIT License. See `LICENSE` file for more details.

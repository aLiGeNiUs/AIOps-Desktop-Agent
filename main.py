import os
import sys
import time
import signal

# Force pyqtgraph to use PySide6
os.environ['QT_API'] = 'pyside6'

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QStyle
from PySide6.QtCore import QThread, Signal, Slot, QObject, QTimer
from PySide6.QtGui import QIcon
import logging
import re

from core.reader import SystemMetricsReader
from core.process_tree import ProcessTreeReader
from ui.dashboard import DashboardWindow
from ai.orchestrator import AIOrchestrator

class AIWorker(QObject):
    """خيط عامل مستقل للذكاء الاصطناعي لمنع تجميد الواجهة"""
    result_ready = Signal(str)

    def __init__(self):
        super().__init__()
        self.orchestrator = AIOrchestrator()

    @Slot(dict, list)
    def analyze_data(self, system_metrics, top_processes):
        # This runs in the ai_thread
        result = self.orchestrator.trigger_analysis(system_metrics, top_processes)
        self.result_ready.emit(result)


class DataWorker(QThread):
    """خيط عامل لقراءة بيانات النواة وإرسالها للواجهة"""
    metrics_updated = Signal(dict, list)
    trigger_ai = Signal(dict, list)

    def __init__(self):
        super().__init__()
        self.running = True
        self.sys_reader = SystemMetricsReader()
        self.proc_reader = ProcessTreeReader()
        
        # Adaptive sampling
        self.default_sleep = 3.0
        self.fast_sleep = 0.5
        self.current_sleep = self.default_sleep
        
        # Reference to orchestrator logic just to check if we should trigger AI
        # We don't make the API call here.
        self.orchestrator = AIOrchestrator()

    def run(self):
        while self.running:
            # 1. Read Data
            sys_metrics = self.sys_reader.read_all()
            procs = self.proc_reader.update_processes()
            
            # 2. Emit to UI
            self.metrics_updated.emit(sys_metrics, procs)
            
            # 3. Adaptive Sampling & AI Trigger Logic
            cpu_pct = sys_metrics.get("cpu_percent", 0)
            ram_pct = sys_metrics.get("ram_percent", 0)
            
            if cpu_pct > 85.0 or ram_pct > 85.0:
                self.current_sleep = self.fast_sleep
            else:
                self.current_sleep = self.default_sleep
                
            if self.orchestrator.should_analyze(cpu_pct, ram_pct):
                self.trigger_ai.emit(sys_metrics, procs)
                
            time.sleep(self.current_sleep)

    def stop(self):
        self.running = False
        self.wait()

def main():
    # Setup Logging
    logging.basicConfig(filename='aiops_history.log', level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("بدء تشغيل AIOps Desktop Agent")

    app = QApplication(sys.argv)
    
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # 1. UI Window
    window = DashboardWindow()
    
    # 2. Data Worker (QThread)
    data_worker = DataWorker()
    
    # 3. AI Worker (QObject moved to QThread)
    ai_thread = QThread()
    ai_worker = AIWorker()
    ai_worker.moveToThread(ai_thread)
    
    # Keep reference so it doesn't get GC'd
    app._ai_thread = ai_thread
    app._ai_worker = ai_worker
    
    # Connections
    data_worker.metrics_updated.connect(window.update_dashboard)
    data_worker.trigger_ai.connect(ai_worker.analyze_data)
    window.force_ai_signal.connect(ai_worker.analyze_data)
    # System Tray setup
    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(window.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
    tray_icon.show()
    
    def on_ai_result(insight_text):
        window.update_ai_insights(insight_text)
        logging.info("تم استلام تقرير جديد من الذكاء الاصطناعي.")
        
        match = re.search(r'(?:PID|العملية)\s*:?\s*(\d+)', insight_text, re.IGNORECASE)
        if match:
            pid = match.group(1)
            # Show notification
            tray_icon.showMessage("تنبيه AIOps", f"الذكاء الاصطناعي يقترح إصلاحاً للعملية {pid}. راجع التطبيق.", QSystemTrayIcon.Warning, 5000)
            
    ai_worker.result_ready.connect(on_ai_result)
    
    # Smart Fix Connection (Graceful Termination)
    @Slot(int)
    def handle_kill_process(pid):
        try:
            logging.info(f"محاولة إغلاق آمن للعملية {pid} باستخدام SIGTERM")
            os.kill(pid, signal.SIGTERM)
            
            def check_and_kill():
                try:
                    os.kill(pid, 0) # Check if alive
                    logging.warning(f"العملية {pid} لم تستجب لـ SIGTERM. يتم الآن إرسال SIGKILL...")
                    os.kill(pid, signal.SIGKILL)
                    window.ai_console.append(f"\n[تم الإغلاق] العملية {pid} أُغلقت إجبارياً.")
                except ProcessLookupError:
                    logging.info(f"العملية {pid} استجابت بنجاح لـ SIGTERM وتم إغلاقها.")
                    window.ai_console.append(f"\n[تم الإغلاق] العملية {pid} أُغلقت بنجاح وبأمان.")
                except PermissionError:
                    window.ai_console.append(f"\n[خطأ] لا توجد صلاحيات لإنهاء العملية {pid}.")
            
            # Wait 3 seconds before checking if it needs SIGKILL
            QTimer.singleShot(3000, check_and_kill)
            
        except PermissionError:
            window.ai_console.append(f"\n[خطأ] فشل في إرسال أمر الإغلاق للعملية {pid}: لا تملك صلاحيات كافية (Permission Denied).")
            logging.error(f"PermissionError while trying to kill {pid}")
        except ProcessLookupError:
            window.ai_console.append(f"\n[خطأ] العملية {pid} غير موجودة.")
            logging.error(f"ProcessLookupError: {pid} not found")
            
    window.kill_process_signal.connect(handle_kill_process)

    # Start threads
    ai_thread.start()
    data_worker.start()
    
    window.show()
    
    # Cleanup on exit
    exit_code = app.exec()
    data_worker.stop()
    ai_thread.quit()
    ai_thread.wait()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

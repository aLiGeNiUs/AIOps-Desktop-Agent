import re
import os
import json
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QTextEdit, QPushButton, QMessageBox, QSplitter,
                               QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from .plotter import PerformancePlotter

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إعدادات الذكاء الاصطناعي")
        self.resize(450, 250)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        self.config_path = "config.json"
        
        layout = QFormLayout(self)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["ollama", "gemini"])
        
        self.ollama_url = QLineEdit()
        self.ollama_model = QLineEdit()
        
        self.gemini_url = QLineEdit()
        self.gemini_key = QLineEdit()
        
        layout.addRow("المزود (Provider):", self.provider_combo)
        layout.addRow("Ollama URL:", self.ollama_url)
        layout.addRow("Ollama Model:", self.ollama_model)
        layout.addRow("Gemini URL:", self.gemini_url)
        layout.addRow("Gemini API Key:", self.gemini_key)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.save_config)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        self.load_config()
        
    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            self.provider_combo.setCurrentText(config.get("ai_provider", "ollama"))
            self.ollama_url.setText(config.get("ollama", {}).get("url", ""))
            self.ollama_model.setText(config.get("ollama", {}).get("model", ""))
            self.gemini_url.setText(config.get("gemini", {}).get("url", ""))
            self.gemini_key.setText(config.get("gemini", {}).get("api_key", ""))
        except Exception:
            pass
            
    def save_config(self):
        config = {
            "ai_provider": self.provider_combo.currentText(),
            "ollama": {
                "url": self.ollama_url.text(),
                "model": self.ollama_model.text()
            },
            "gemini": {
                "url": self.gemini_url.text(),
                "api_key": self.gemini_key.text()
            }
        }
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            QMessageBox.information(self, "تم الحفظ", "تم حفظ الإعدادات بنجاح.\nيرجى إعادة تشغيل التطبيق ليتم تطبيق المزود الجديد.")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في حفظ الإعدادات: {str(e)}")
        self.accept()

class DashboardWindow(QMainWindow):
    # Signals for communicating with main thread/workers
    kill_process_signal = Signal(int)
    force_ai_signal = Signal(dict, list)
    
    WHITELIST = ['systemd', 'Xorg', 'gnome-shell', 'python3', 'antigravity', 'kthreadd', 'bash', 'dbus-daemon']

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIOps Desktop Agent")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #11111b; color: #cdd6f4;")
        
        self.current_ai_recommendation_pid = None
        self.latest_metrics = {}
        self.latest_processes = []
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 1. Top Section: Indicators and Plot
        top_layout = QHBoxLayout()
        
        # Circular Indicators (simplified as labels for fast rendering)
        indicators_layout = QVBoxLayout()
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.cpu_label.setStyleSheet("color: #f38ba8;")
        
        self.ram_label = QLabel("RAM: 0%")
        self.ram_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.ram_label.setStyleSheet("color: #89b4fa;")
        
        indicators_layout.addWidget(self.cpu_label)
        indicators_layout.addWidget(self.ram_label)
        indicators_layout.addStretch()
        
        top_layout.addLayout(indicators_layout, 1)
        
        # Plotter
        self.plotter = PerformancePlotter()
        top_layout.addWidget(self.plotter, 3)
        
        main_layout.addLayout(top_layout, 1)
        
        # Splitter for Bottom Section
        splitter = QSplitter(Qt.Horizontal)
        
        # 2. Bottom Left: Process Table
        self.process_table = QTableWidget(0, 4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "RAM (MB)"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setStyleSheet("QTableWidget { background-color: #1e1e2e; gridline-color: #313244; }")
        self.process_table.cellDoubleClicked.connect(self.on_process_double_clicked)
        splitter.addWidget(self.process_table)
        
        # 3. Bottom Right: AI Insights
        ai_layout_widget = QWidget()
        ai_layout = QVBoxLayout(ai_layout_widget)
        ai_layout.setContentsMargins(0,0,0,0)
        
        # Header layout for AI section
        ai_header_layout = QHBoxLayout()
        ai_title = QLabel("AI Insights Console")
        ai_title.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.force_ai_btn = QPushButton("تحليل الآن (Force)")
        self.force_ai_btn.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 5px;")
        self.force_ai_btn.clicked.connect(self.on_force_ai_clicked)
        
        self.settings_btn = QPushButton("⚙️ إعدادات")
        self.settings_btn.setStyleSheet("background-color: #f9e2af; color: #11111b; font-weight: bold; padding: 5px;")
        self.settings_btn.clicked.connect(self.on_settings_clicked)
        
        self.about_btn = QPushButton("ℹ️ عن التطبيق")
        self.about_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 5px;")
        self.about_btn.clicked.connect(self.show_about_dialog)
        
        ai_header_layout.addWidget(ai_title)
        ai_header_layout.addStretch()
        ai_header_layout.addWidget(self.force_ai_btn)
        ai_header_layout.addWidget(self.settings_btn)
        ai_header_layout.addWidget(self.about_btn)
        
        self.ai_console = QTextEdit()
        self.ai_console.setReadOnly(True)
        self.ai_console.setStyleSheet("background-color: #1e1e2e; border: 1px solid #f38ba8;")
        self.ai_console.setPlaceholderText("في انتظار تحليل الذكاء الاصطناعي... \n(يتم التحليل التلقائي فقط إذا تجاوز استهلاك المعالج أو الذاكرة 85%)")
        
        self.smart_fix_btn = QPushButton("الإصلاح الذكي (Smart Fix)")
        self.smart_fix_btn.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 10px;")
        self.smart_fix_btn.setEnabled(False)
        self.smart_fix_btn.clicked.connect(self.on_smart_fix_clicked)
        
        ai_layout.addLayout(ai_header_layout)
        ai_layout.addWidget(self.ai_console)
        ai_layout.addWidget(self.smart_fix_btn)
        
        splitter.addWidget(ai_layout_widget)
        
        # Set default proportions: 40% for Table, 60% for AI Console
        splitter.setSizes([400, 600])
        
        # Bottom section gets 4x more vertical space than Top section
        main_layout.addWidget(splitter, 4)

    @Slot(dict, list)
    def update_dashboard(self, system_metrics, processes):
        self.latest_metrics = system_metrics
        self.latest_processes = processes
        
        # Update labels
        self.cpu_label.setText(f"CPU: {system_metrics['cpu_percent']:.1f}%")
        self.ram_label.setText(f"RAM: {system_metrics['ram_percent']:.1f}%\n({system_metrics['ram_used_mb']/1024:.1f} GB)")
        
        # Update Plot
        self.plotter.update_plot(system_metrics['cpu_percent'], system_metrics['ram_percent'])
        
        # Update Table (In-place updates if possible, or fast rewrite)
        self.process_table.setRowCount(min(len(processes), 50)) # Show top 50 only
        for row, proc in enumerate(processes[:50]):
            self.process_table.setItem(row, 0, QTableWidgetItem(str(proc['pid'])))
            self.process_table.setItem(row, 1, QTableWidgetItem(proc['name']))
            self.process_table.setItem(row, 2, QTableWidgetItem(f"{proc['cpu_percent']:.1f}"))
            self.process_table.setItem(row, 3, QTableWidgetItem(f"{proc['ram_mb']:.1f}"))

    @Slot(str)
    def update_ai_insights(self, insight_text):
        self.ai_console.setPlainText(insight_text)
        
        # Try to parse a PID to kill from the text using simple regex
        # Look for "PID: 1234" or "PID 1234" or "العملية 1234"
        match = re.search(r'(?:PID|العملية)\s*:?\s*(\d+)', insight_text, re.IGNORECASE)
        if match:
            pid = int(match.group(1))
            
            # Check whitelist
            proc_name = "Unknown"
            for p in self.latest_processes:
                if p['pid'] == pid:
                    proc_name = p['name']
                    break
                    
            if proc_name in self.WHITELIST:
                self.current_ai_recommendation_pid = None
                self.smart_fix_btn.setEnabled(False)
                self.smart_fix_btn.setText("إصلاح ذكي (العملية محمية 🛡️)")
                self.ai_console.append(f"\n\n[حماية النظام] اقترح الذكاء الاصطناعي إنهاء '{proc_name}' (PID {pid}) ولكنها محمية ولن يتم إنهاؤها.")
                logging.warning(f"الذكاء الاصطناعي اقترح إنهاء عملية محمية: {proc_name} (PID {pid})")
            else:
                self.current_ai_recommendation_pid = pid
                self.smart_fix_btn.setEnabled(True)
                self.smart_fix_btn.setText(f"الإصلاح الذكي (إنهاء العملية {pid})")
                logging.info(f"تم تفعيل الإصلاح الذكي للعملية: {proc_name} (PID {pid})")
        else:
            self.current_ai_recommendation_pid = None
            self.smart_fix_btn.setEnabled(False)
            self.smart_fix_btn.setText("الإصلاح الذكي (لا يتوفر إجراء)")

    def on_force_ai_clicked(self):
        if self.latest_metrics and self.latest_processes:
            self.ai_console.setPlainText("جاري طلب التحليل من الذكاء الاصطناعي...")
            self.force_ai_signal.emit(self.latest_metrics, self.latest_processes)
            
    def on_settings_clicked(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_about_dialog(self):
        about_text = (
            "<h3>AIOps Desktop Agent</h3>"
            "<p><b>الإصدار التفصيلي:</b> v1.0.0 (Build 2026.06)</p>"
            "<hr>"
            "<p>I Am knowledgist Hacker<br>"
            "حياتي مكرسة لنشر المعرفة في العلوم والتقنية<br>"
            "الذكاء الإصطناعي و اﻷمن السيبراني</p>"
            "<p>© 2026 The hackers Ali Al-Kazaly (علي عاصف) – aLi GeNiUs</p>"
            "<p>🔗 <a href='https://www.youtube.com/@aLiGeNiUs.TheHackers'>https://www.youtube.com/@aLiGeNiUs.TheHackers</a></p>"
        )
        QMessageBox.about(self, "عن التطبيق", about_text)

    def on_smart_fix_clicked(self):
        if self.current_ai_recommendation_pid:
            # Human in the loop confirmation
            reply = QMessageBox.question(self, 'تأكيد الإصلاح الذكي', 
                                         f"هل أنت متأكد أنك تريد إنهاء العملية رقم {self.current_ai_recommendation_pid} بناءً على توصية الذكاء الاصطناعي؟",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.kill_process_signal.emit(self.current_ai_recommendation_pid)
                self.ai_console.append("\n\n[جاري إرسال أمر الإنهاء الآمن...]")
                self.smart_fix_btn.setEnabled(False)
                logging.info(f"المستخدم وافق على إنهاء العملية {self.current_ai_recommendation_pid}")

    def on_process_double_clicked(self, row, column):
        pid_item = self.process_table.item(row, 0)
        name_item = self.process_table.item(row, 1)
        if not pid_item:
            return
            
        pid = int(pid_item.text())
        name = name_item.text()
        
        from core.process_tree import ProcessTreeReader
        details = ProcessTreeReader.get_process_details(pid)
        
        msg = f"معلومات العملية (PID: {pid})\nالاسم: {name}\n\nالمستخدم: {details['user']} (UID: {details['uid']})\n\nالأمر (Command):\n{details['cmdline']}"
        QMessageBox.information(self, "تفاصيل العملية", msg)

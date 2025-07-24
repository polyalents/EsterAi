#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Desktop Application
Приложение для генерации текста и изображений с помощью нейросетей
Версия: 1.0.0
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ui.main_window import MainWindow
    from utils.config import Config
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все файлы созданы правильно")
    sys.exit(1)


class AIDesktopApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_application()
        self.main_window = None
        
    def setup_application(self):
        """Настройка основных параметров приложения"""
        # Информация о приложении
        self.app.setApplicationName("AI Desktop Generator")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("AI Creative Studio")
        
        # Настройка темной темы
        self.setup_dark_theme()
        
        # Настройка шрифтов
        self.setup_fonts()
        
        # Обработка высокого DPI
        self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        self.app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
    def setup_dark_theme(self):
        """Применение темной темы"""
        dark_style = """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #3c3c3c;
            background-color: #2d2d30;
        }
        
        QTabWidget::tab-bar {
            left: 5px;
        }
        
        QTabBar::tab {
            background-color: #3c3c3c;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #007acc;
        }
        
        QTabBar::tab:hover {
            background-color: #4c4c4c;
        }
        
        QPushButton {
            background-color: #0e639c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #1177bb;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #3c3c3c;
            color: #808080;
        }
        
        QTextEdit, QPlainTextEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 8px;
        }
        
        QLineEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 6px;
        }
        
        QComboBox {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 6px;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-style: solid;
            border-width: 3px;
            border-color: transparent transparent #ffffff transparent;
        }
        
        QSlider::groove:horizontal {
            background-color: #3c3c3c;
            height: 6px;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background-color: #007acc;
            width: 16px;
            border-radius: 8px;
            margin: -5px 0;
        }
        
        QProgressBar {
            background-color: #3c3c3c;
            color: #ffffff;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 4px;
        }
        
        QLabel {
            color: #ffffff;
        }
        
        QGroupBox {
            color: #ffffff;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QScrollBar:vertical {
            background-color: #2d2d30;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #484848;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #5a5a5a;
        }
        
        QMenuBar {
            background-color: #2d2d30;
            color: #ffffff;
        }
        
        QMenuBar::item:selected {
            background-color: #3e3e42;
        }
        
        QMenu {
            background-color: #2d2d30;
            color: #ffffff;
            border: 1px solid #3c3c3c;
        }
        
        QMenu::item:selected {
            background-color: #007acc;
        }
        """
        
        self.app.setStyleSheet(dark_style)
        
    def setup_fonts(self):
        """Настройка шрифтов"""
        # Основной шрифт для интерфейса
        font = QFont("Segoe UI", 9)
        self.app.setFont(font)
        
    def run(self):
        """Запуск приложения"""
        try:
            # Создаем главное окно
            self.main_window = MainWindow()
            self.main_window.show()
            
            # Центрируем окно на экране
            self.center_window()
            
            return self.app.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                None, 
                "Критическая ошибка", 
                f"Не удалось запустить приложение:\n{str(e)}\n\nПроверьте, что все файлы созданы правильно."
            )
            return 1
            
    def center_window(self):
        """Центрирование окна на экране"""
        if self.main_window:
            screen = self.app.primaryScreen().geometry()
            window = self.main_window.geometry()
            x = (screen.width() - window.width()) // 2
            y = (screen.height() - window.height()) // 2
            self.main_window.move(x, y)


def main():
    """Точка входа в приложение"""
    # Обработка аргументов командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("AI Desktop Generator v1.0.0")
            print("Использование: python main.py [опции]")
            print("\nОпции:")
            print("  --help, -h     Показать эту справку")
            print("  --version, -v  Показать версию")
            return 0
        elif sys.argv[1] in ['--version', '-v']:
            print("AI Desktop Generator v1.0.0")
            return 0
    
    # Проверка зависимостей
    try:
        import torch
        import transformers
        import diffusers
        from PIL import Image
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("\n🔧 Установите зависимости:")
        print("pip install -r requirements.txt")
        return 1
    
    # Создание и запуск приложения
    try:
        app = AIDesktopApp()
        return app.run()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
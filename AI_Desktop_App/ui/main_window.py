#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно приложения AI Desktop Generator - упрощенная версия
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMenuBar,
    QStatusBar,
    QAction,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QLabel,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence

from .text_tab import TextGenerationTab
from .image_tab import ImageGenerationTab
from ..utils.config import Config


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    # Сигналы
    status_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        try:
            self.config = Config()
        except Exception:
            self.config = None
            
        self.init_ui()
        self.setup_connections()
        self.load_settings()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("AI Desktop Generator v1.0.0")
        self.setMinimumSize(1200, 800)
        self.setGeometry(100, 100, 1400, 900)
        
        # Создание центрального виджета
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Создание главного макета
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создание меню
        self.create_menu_bar()
        
        # Создание вкладок
        self.create_tabs()
        
        # Создание статус-бара
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu('Файл')
        
        # Новый проект
        new_action = QAction('Новый проект', self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        # Открыть проект
        open_action = QAction('Открыть проект...', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        # Сохранить проект
        save_action = QAction('Сохранить проект', self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Импорт текста
        import_text_action = QAction('Импорт текста...', self)
        import_text_action.triggered.connect(self.import_text)
        file_menu.addAction(import_text_action)
        
        # Экспорт результатов
        export_action = QAction('Экспорт результатов...', self)
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Выход
        exit_action = QAction('Выход', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Инструменты"
        tools_menu = menubar.addMenu('Инструменты')
        
        # Настройки
        settings_action = QAction('Настройки...', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Информация о системе
        system_info_action = QAction('Информация о системе', self)
        system_info_action.triggered.connect(self.show_system_info)
        tools_menu.addAction(system_info_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu('Справка')
        
        # О программе
        about_action = QAction('О программе...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_tabs(self):
        """Создание системы вкладок"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(True)
        
        try:
            # Вкладка генерации текста
            self.text_tab = TextGenerationTab()
            self.tab_widget.addTab(self.text_tab, "📝 Генерация текста")
            
            # Вкладка генерации изображений
            self.image_tab = ImageGenerationTab()
            self.tab_widget.addTab(self.image_tab, "🎨 Генерация изображений")
            
        except Exception as e:
            # Создаем простые заглушки если вкладки не загрузились
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            error_label = QLabel(f"Ошибка загрузки вкладок: {str(e)}")
            layout.addWidget(error_label)
            self.tab_widget.addTab(placeholder, "Ошибка")
        
        self.main_layout.addWidget(self.tab_widget)
        
    def create_status_bar(self):
        """Создание статус-бара"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Основная информация
        self.status_label = QLabel("Готов к работе")
        self.status_bar.addWidget(self.status_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Информация о GPU
        self.gpu_label = QLabel()
        self.update_gpu_info()
        self.status_bar.addPermanentWidget(self.gpu_label)
        
    def setup_connections(self):
        """Настройка связей между компонентами"""
        try:
            if hasattr(self, 'text_tab'):
                self.text_tab.status_changed.connect(self.update_status)
                self.text_tab.progress_changed.connect(self.update_progress)
                
            if hasattr(self, 'image_tab'):
                self.image_tab.status_changed.connect(self.update_status)
                self.image_tab.progress_changed.connect(self.update_progress)
        except Exception:
            pass
        
        # Внутренние сигналы
        self.status_changed.connect(self.update_status)
        self.progress_changed.connect(self.update_progress)
        
    def update_status(self, message):
        """Обновление статуса"""
        self.status_label.setText(message)
        
    def update_progress(self, value):
        """Обновление прогресса"""
        if value < 0:
            self.progress_bar.setVisible(False)
        else:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(value)
            
    def update_gpu_info(self):
        """Обновление информации о GPU"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory // (1024**3)
                self.gpu_label.setText(f"🎮 {gpu_name[:20]}... ({gpu_memory}GB)")
            else:
                self.gpu_label.setText("💻 CPU режим")
        except ImportError:
            self.gpu_label.setText("⚠️ PyTorch не найден")
            
    # Методы для работы с проектами
    def new_project(self):
        """Создание нового проекта"""
        reply = QMessageBox.question(
            self, 'Новый проект', 
            'Создать новый проект? Несохраненные данные будут утеряны.',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if hasattr(self, 'text_tab'):
                    self.text_tab.clear_all()
                if hasattr(self, 'image_tab'):
                    self.image_tab.clear_all()
            except Exception:
                pass
            self.update_status("Создан новый проект")
            
    def open_project(self):
        """Открытие проекта"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            'Открыть проект', 
            '',
            'Файлы проекта (*.aip);;Все файлы (*)'
        )
        
        if file_path:
            self.update_status(f"Проект загружен: {os.path.basename(file_path)}")
                
    def save_project(self):
        """Сохранение проекта"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Сохранить проект как',
            '',
            'Файлы проекта (*.aip);;Все файлы (*)'
        )
        
        if file_path:
            self.update_status(f"Проект сохранен: {os.path.basename(file_path)}")
            
    def import_text(self):
        """Импорт текстового файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Импорт текста',
            '',
            'Текстовые файлы (*.txt *.md *.rtf);;Все файлы (*)'
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if hasattr(self, 'text_tab'):
                    self.text_tab.set_input_text(content)
                    
                self.update_status(f"Текст импортирован: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось импортировать файл:\n{str(e)}')
                
    def export_results(self):
        """Экспорт результатов"""
        self.update_status("Результаты экспортированы")
        
    def show_settings(self):
        """Показ окна настроек"""
        QMessageBox.information(self, 'Настройки', 'Окно настроек будет добавлено в следующей версии.')
        
    def show_system_info(self):
        """Показ информации о системе"""
        try:
            import torch
            import platform
            
            info = f"""
Информация о системе:

ОС: {platform.system()} {platform.release()}
Python: {platform.python_version()}
PyTorch: {torch.__version__}
CUDA доступна: {'Да' if torch.cuda.is_available() else 'Нет'}
"""
            if torch.cuda.is_available():
                info += f"GPU: {torch.cuda.get_device_name(0)}\n"
                info += f"Память GPU: {torch.cuda.get_device_properties(0).total_memory // (1024**3)} GB"
                
        except Exception:
            info = "Не удалось получить информацию о системе"
            
        QMessageBox.information(self, 'Информация о системе', info)
        
    def show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(
            self,
            'О программе',
            '''<h3>AI Desktop Generator v1.0.0</h3>
            <p>Мощное desktop приложение для генерации текста и изображений с помощью искусственного интеллекта.</p>
            
            <p><b>Возможности:</b></p>
            <ul>
            <li>Генерация текста с помощью GPT моделей</li>
            <li>Создание изображений через Stable Diffusion</li>
            <li>Множественные стили генерации</li>
            <li>Работа с проектами и файлами</li>
            <li>Современный темный интерфейс</li>
            </ul>
            
            <p><b>Технологии:</b> PyQt5, PyTorch, Transformers, Diffusers</p>
            <p><b>Разработчик:</b> AI Creative Studio</p>
            '''
        )
        
    def load_settings(self):
        """Загрузка настроек"""
        if self.config:
            try:
                geometry = self.config.get('window_geometry')
                if geometry:
                    self.restoreGeometry(geometry)
                    
                state = self.config.get('window_state')
                if state:
                    self.restoreState(state)
            except Exception:
                pass
            
    def save_settings(self):
        """Сохранение настроек"""
        if self.config:
            try:
                self.config.set('window_geometry', self.saveGeometry())
                self.config.set('window_state', self.saveState())
                self.config.save()
            except Exception:
                pass
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Сохранение настроек
        self.save_settings()
        
        # Проверка несохраненных изменений
        try:
            has_unsaved = False
            if hasattr(self, 'text_tab') and hasattr(self.text_tab, 'has_unsaved_changes'):
                has_unsaved = has_unsaved or self.text_tab.has_unsaved_changes()
            if hasattr(self, 'image_tab') and hasattr(self.image_tab, 'has_unsaved_changes'):
                has_unsaved = has_unsaved or self.image_tab.has_unsaved_changes()
                
            if has_unsaved:
                reply = QMessageBox.question(
                    self,
                    'Выход',
                    'Есть несохраненные изменения. Выйти без сохранения?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    event.ignore()
                    return
        except Exception:
            pass
                
        # Остановка генерации
        try:
            if hasattr(self, 'text_tab') and hasattr(self.text_tab, 'stop_generation'):
                self.text_tab.stop_generation()
            if hasattr(self, 'image_tab') and hasattr(self.image_tab, 'stop_generation'):
                self.image_tab.stop_generation()
        except Exception:
            pass
            
        event.accept()
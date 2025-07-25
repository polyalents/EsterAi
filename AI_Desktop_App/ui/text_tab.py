#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вкладка для генерации текста - упрощенная версия
"""

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QTextEdit, QPlainTextEdit, QPushButton, QComboBox,
                            QLabel, QSlider, QSpinBox, QGroupBox, QCheckBox,
                            QFileDialog, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from ..models.text_generator import TextGenerator


class TextGenerationWorker(QThread):
    """Рабочий поток для генерации текста"""
    
    progress_changed = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    text_generated = pyqtSignal(str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, generator, prompt, settings):
        super().__init__()
        self.generator = generator
        self.prompt = prompt
        self.settings = settings
        self._stop_requested = False
        
    def run(self):
        """Основной метод генерации"""
        try:
            self.status_changed.emit("Генерация текста...")
            self.progress_changed.emit(10)
            
            if self._stop_requested:
                return
                
            # Генерация текста
            generated_text = self.generator.generate(
                prompt=self.prompt,
                max_length=self.settings['max_length'],
                temperature=self.settings['temperature'],
                style=self.settings['style'],
                callback=self._progress_callback
            )
            
            if not self._stop_requested:
                self.text_generated.emit(generated_text)
                self.status_changed.emit("Генерация завершена")
                self.progress_changed.emit(100)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            
        finally:
            self.finished.emit()
            
    def _progress_callback(self, progress):
        """Обратный вызов для обновления прогресса"""
        if not self._stop_requested:
            self.progress_changed.emit(int(progress * 100))
            
    def stop(self):
        """Остановка генерации"""
        self._stop_requested = True


class TextGenerationTab(QWidget):
    """Вкладка генерации текста"""
    
    # Сигналы
    status_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.generator = TextGenerator()
        self.generation_worker = None
        self._unsaved_changes = False
        
        self.init_ui()
        self.setup_connections()
        self.load_demo_model()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Создание основного сплиттера
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Левая панель - настройки
        self.create_settings_panel(splitter)
        
        # Правая панель - ввод и вывод
        self.create_text_panel(splitter)
        
        # Настройка пропорций
        splitter.setSizes([300, 700])
        
    def create_settings_panel(self, parent):
        """Создание панели настроек"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Группа стилей
        style_group = QGroupBox("Стиль генерации")
        style_layout = QVBoxLayout(style_group)
        
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Нейтральный",
            "Креативный",
            "Технический", 
            "Художественный",
            "Научный",
            "Деловой",
            "Разговорный",
            "Поэтический",
            "Без ограничений"
        ])
        style_layout.addWidget(self.style_combo)
        
        layout.addWidget(style_group)
        
        # Группа параметров
        params_group = QGroupBox("Параметры генерации")
        params_layout = QVBoxLayout(params_group)
        
        # Длина текста
        length_label = QLabel("Максимальная длина:")
        params_layout.addWidget(length_label)
        
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(50, 2000)
        self.length_spinbox.setValue(500)
        self.length_spinbox.setSuffix(" символов")
        params_layout.addWidget(self.length_spinbox)
        
        # Температура (креативность)
        temp_label = QLabel("Креативность:")
        params_layout.addWidget(temp_label)
        
        temp_layout = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(1, 20)
        self.temperature_slider.setValue(7)
        temp_layout.addWidget(self.temperature_slider)
        
        self.temp_value_label = QLabel("0.7")
        temp_layout.addWidget(self.temp_value_label)
        
        params_layout.addLayout(temp_layout)
        
        layout.addWidget(params_group)
        
        # Группа модели
        model_group = QGroupBox("Модель")
        model_layout = QVBoxLayout(model_group)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Demo Mode",
            "GPT-J 6B (Рекомендуется)",
            "GPT-Neo 2.7B (Быстрая)",
            "GPT-Neo 1.3B (Легковесная)",
            "DialoGPT (Диалоги)"
        ])
        model_layout.addWidget(self.model_combo)
        
        self.model_status_label = QLabel("Demo режим активен")
        self.model_status_label.setStyleSheet("color: #4ade80;")
        model_layout.addWidget(self.model_status_label)
        
        layout.addWidget(model_group)
        
        # Кнопки управления
        buttons_layout = QVBoxLayout()
        
        self.generate_button = QPushButton("🚀 Генерировать")
        self.generate_button.setMinimumHeight(40)
        buttons_layout.addWidget(self.generate_button)
        
        self.stop_button = QPushButton("⏹️ Остановить")
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)
        
        buttons_layout.addSpacing(10)
        
        self.load_model_button = QPushButton("📥 Загрузить модель")
        buttons_layout.addWidget(self.load_model_button)
        
        self.clear_button = QPushButton("🗑️ Очистить всё")
        buttons_layout.addWidget(self.clear_button)
        
        layout.addLayout(buttons_layout)
        
        # Добавляем растягивающее пространство
        layout.addStretch()
        
        parent.addWidget(settings_widget)
        
    def create_text_panel(self, parent):
        """Создание панели текста"""
        text_widget = QWidget()
        layout = QVBoxLayout(text_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Создание вертикального сплиттера для ввода и вывода
        text_splitter = QSplitter(Qt.Vertical)
        
        # Панель ввода
        input_group = QGroupBox("Входной текст / промпт")
        input_layout = QVBoxLayout(input_group)
        
        # Панель инструментов для ввода
        input_toolbar = QHBoxLayout()
        
        self.load_text_button = QPushButton("📁 Загрузить")
        input_toolbar.addWidget(self.load_text_button)
        
        self.clear_input_button = QPushButton("🗑️ Очистить")
        input_toolbar.addWidget(self.clear_input_button)
        
        input_toolbar.addStretch()
        
        input_char_label = QLabel("Символов: 0")
        input_toolbar.addWidget(input_char_label)
        self.input_char_label = input_char_label
        
        input_layout.addLayout(input_toolbar)
        
        # Поле ввода
        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText(
            "Введите исходный текст или промпт для генерации...\n\n"
            "Примеры промптов:\n"
            "• 'Напиши рассказ о путешествии в космос'\n"
            "• 'Создай техническое описание робота'\n"
            "• 'Сочини стихотворение о природе'"
        )
        
        # Настройка шрифта для ввода
        font = QFont("Consolas", 11)
        self.input_text.setFont(font)
        
        input_layout.addWidget(self.input_text)
        text_splitter.addWidget(input_group)
        
        # Панель вывода
        output_group = QGroupBox("Сгенерированный текст")
        output_layout = QVBoxLayout(output_group)
        
        # Панель инструментов для вывода
        output_toolbar = QHBoxLayout()
        
        self.save_text_button = QPushButton("💾 Сохранить")
        output_toolbar.addWidget(self.save_text_button)
        
        self.copy_text_button = QPushButton("📋 Копировать")
        output_toolbar.addWidget(self.copy_text_button)
        
        self.clear_output_button = QPushButton("🗑️ Очистить")
        output_toolbar.addWidget(self.clear_output_button)
        
        output_toolbar.addStretch()
        
        output_char_label = QLabel("Символов: 0")
        output_toolbar.addWidget(output_char_label)
        self.output_char_label = output_char_label
        
        output_layout.addLayout(output_toolbar)
        
        # Поле вывода
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(font)
        
        output_layout.addWidget(self.output_text)
        text_splitter.addWidget(output_group)
        
        # Настройка пропорций сплиттера
        text_splitter.setSizes([300, 400])
        
        layout.addWidget(text_splitter)
        
        parent.addWidget(text_widget)
        
    def setup_connections(self):
        """Настройка связей"""
        # Слайдер температуры
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temp_value_label.setText(f"{v/10:.1f}")
        )
        
        # Кнопки
        self.generate_button.clicked.connect(self.start_generation)
        self.stop_button.clicked.connect(self.stop_generation)
        self.load_model_button.clicked.connect(self.load_model)
        self.clear_button.clicked.connect(self.clear_all)
        
        # Кнопки текста
        self.load_text_button.clicked.connect(self.load_text_file)
        self.clear_input_button.clicked.connect(self.clear_input)
        self.save_text_button.clicked.connect(self.save_text_file)
        self.copy_text_button.clicked.connect(self.copy_output)
        self.clear_output_button.clicked.connect(self.clear_output)
        
        # Отслеживание изменений
        self.input_text.textChanged.connect(self.on_text_changed)
        self.input_text.textChanged.connect(self.update_input_stats)
        self.output_text.textChanged.connect(self.update_output_stats)
        
        # Изменение модели
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        
    def load_demo_model(self):
        """Загрузка демо модели при старте"""
        try:
            self.generator.load_model("Demo Mode")
            self.model_status_label.setText("Demo режим активен")
            self.model_status_label.setStyleSheet("color: #4ade80;")
        except Exception as e:
            self.model_status_label.setText(f"Ошибка: {str(e)}")
            self.model_status_label.setStyleSheet("color: #ff6b6b;")
        
    def on_text_changed(self):
        """Обработка изменения текста"""
        self._unsaved_changes = True
        
    def update_input_stats(self):
        """Обновление статистики ввода"""
        text = self.input_text.toPlainText()
        char_count = len(text)
        self.input_char_label.setText(f"Символов: {char_count}")
        
    def update_output_stats(self):
        """Обновление статистики вывода"""
        text = self.output_text.toPlainText()
        char_count = len(text)
        self.output_char_label.setText(f"Символов: {char_count}")
        
    def on_model_changed(self):
        """Обработка изменения модели"""
        if self.model_combo.currentText() != "Demo Mode":
            self.model_status_label.setText("Модель не загружена")
            self.model_status_label.setStyleSheet("color: #ff6b6b;")
        
    def start_generation(self):
        """Начало генерации"""
        prompt = self.input_text.toPlainText().strip()
        
        if not prompt:
            QMessageBox.warning(self, "Предупреждение", "Введите текст или промпт для генерации!")
            return
            
        if not self.generator.is_loaded():
            QMessageBox.warning(self, "Предупреждение", "Загрузите модель перед генерацией!")
            return
            
        # Настройки генерации
        settings = {
            'max_length': self.length_spinbox.value(),
            'temperature': self.temperature_slider.value() / 10.0,
            'style': self.style_combo.currentText()
        }
        
        # Создание и запуск рабочего потока
        self.generation_worker = TextGenerationWorker(self.generator, prompt, settings)
        self.generation_worker.progress_changed.connect(self.progress_changed.emit)
        self.generation_worker.status_changed.connect(self.status_changed.emit)
        self.generation_worker.text_generated.connect(self.on_text_generated)
        self.generation_worker.error_occurred.connect(self.on_generation_error)
        self.generation_worker.finished.connect(self.on_generation_finished)
        
        # Обновление интерфейса
        self.generate_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Запуск
        self.generation_worker.start()
        
    def stop_generation(self):
        """Остановка генерации"""
        if self.generation_worker and self.generation_worker.isRunning():
            self.generation_worker.stop()
            self.status_changed.emit("Остановка генерации...")
            
    def on_text_generated(self, text):
        """Обработка сгенерированного текста"""
        self.output_text.setPlainText(text)
        self._unsaved_changes = True
        
    def on_generation_error(self, error):
        """Обработка ошибки генерации"""
        QMessageBox.critical(self, "Ошибка генерации", f"Произошла ошибка:\n{error}")
        
    def on_generation_finished(self):
        """Завершение генерации"""
        self.generate_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_changed.emit(-1)  # Скрыть прогресс-бар
        
    def load_model(self):
        """Загрузка модели"""
        model_name = self.model_combo.currentText()
        
        try:
            self.status_changed.emit("Загрузка модели...")
            self.load_model_button.setEnabled(False)
            
            success = self.generator.load_model(model_name)
            
            if success:
                self.model_status_label.setText("Модель загружена")
                self.model_status_label.setStyleSheet("color: #4ade80;")
                self.status_changed.emit("Модель успешно загружена")
            else:
                self.model_status_label.setText("Ошибка загрузки")
                self.model_status_label.setStyleSheet("color: #ff6b6b;")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить модель:\n{str(e)}")
            
        finally:
            self.load_model_button.setEnabled(True)
            
    def load_text_file(self):
        """Загрузка текстового файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить текст",
            "",
            "Текстовые файлы (*.txt *.md *.rtf);;Все файлы (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.setPlainText(content)
                self.status_changed.emit(f"Загружен файл: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
                
    def save_text_file(self):
        """Сохранение текста в файл"""
        if not self.output_text.toPlainText().strip():
            QMessageBox.warning(self, "Предупреждение", "Нет текста для сохранения!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить текст",
            "generated_text.txt",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.output_text.toPlainText())
                self.status_changed.emit(f"Текст сохранен: {os.path.basename(file_path)}")
                self._unsaved_changes = False
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
                
    def copy_output(self):
        """Копирование вывода в буфер обмена"""
        text = self.output_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_changed.emit("Текст скопирован в буфер обмена")
        else:
            QMessageBox.information(self, "Информация", "Нет текста для копирования!")
            
    def clear_input(self):
        """Очистка ввода"""
        self.input_text.clear()
        
    def clear_output(self):
        """Очистка вывода"""
        self.output_text.clear()
        
    def clear_all(self):
        """Очистка всего"""
        reply = QMessageBox.question(
            self, 
            'Очистка', 
            'Очистить весь текст? Несохраненные данные будут утеряны.',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.input_text.clear()
            self.output_text.clear()
            self._unsaved_changes = False
            
    def set_input_text(self, text):
        """Установка текста ввода"""
        self.input_text.setPlainText(text)
        
    def has_unsaved_changes(self):
        """Проверка несохраненных изменений"""
        return self._unsaved_changes

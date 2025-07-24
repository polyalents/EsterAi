#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вкладка для генерации изображений - упрощенная версия
"""

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QPlainTextEdit, QPushButton, QComboBox,
                            QLabel, QSlider, QSpinBox, QGroupBox,
                            QFileDialog, QMessageBox, QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage

try:
    from models.image_generator import ImageGenerator
except ImportError:
    import sys
    sys.path.append('..')
    from models.image_generator import ImageGenerator


class ImageGenerationWorker(QThread):
    """Рабочий поток для генерации изображений"""
    
    progress_changed = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    image_generated = pyqtSignal(object)  # PIL Image
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, generator, prompt, negative_prompt, settings):
        super().__init__()
        self.generator = generator
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.settings = settings
        self._stop_requested = False
        
    def run(self):
        """Основной метод генерации"""
        try:
            self.status_changed.emit("Генерация изображения...")
            self.progress_changed.emit(10)
            
            if self._stop_requested:
                return
                
            # Генерация изображения
            generated_image = self.generator.generate(
                prompt=self.prompt,
                negative_prompt=self.negative_prompt,
                width=self.settings['width'],
                height=self.settings['height'],
                steps=self.settings['steps'],
                guidance_scale=self.settings['guidance_scale'],
                style=self.settings['style'],
                callback=self._progress_callback
            )
            
            if not self._stop_requested:
                self.image_generated.emit(generated_image)
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


class ImageViewer(QLabel):
    """Виджет для отображения изображения"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.setMaximumSize(600, 600)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #3c3c3c;
                border-radius: 8px;
                background-color: #1a1a1a;
            }
        """)
        self.setText("Изображение появится здесь")
        self._original_pixmap = None
        
    def set_image(self, image):
        """Установка изображения"""
        if image:
            # Конвертация PIL Image в QPixmap
            image_qt = image.convert('RGB')
            w, h = image_qt.size
            rgb_image = image_qt.tobytes('raw', 'RGB')
            qimage = QImage(rgb_image, w, h, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimage)
            self._original_pixmap = pixmap
            self._update_display()
        else:
            self.clear()
            self._original_pixmap = None
            self.setText("Изображение появится здесь")
            
    def _update_display(self):
        """Обновление отображения с масштабированием"""
        if self._original_pixmap:
            scaled_pixmap = self._original_pixmap.scaled(
                self.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
            
    def resizeEvent(self, event):
        """Обработка изменения размера"""
        super().resizeEvent(event)
        if self._original_pixmap:
            self._update_display()


class ImageGenerationTab(QWidget):
    """Вкладка генерации изображений"""
    
    # Сигналы
    status_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.generator = ImageGenerator()
        self.generation_worker = None
        self._unsaved_changes = False
        self._current_image = None
        
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
        
        # Центральная панель - промпты
        self.create_prompt_panel(splitter)
        
        # Правая панель - изображение
        self.create_image_panel(splitter)
        
        # Настройка пропорций
        splitter.setSizes([300, 400, 500])
        
    def create_settings_panel(self, parent):
        """Создание панели настроек"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Группа стилей
        style_group = QGroupBox("Стиль изображения")
        style_layout = QVBoxLayout(style_group)
        
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Реалистичный",
            "Художественный",
            "Аниме",
            "Цифровое искусство",
            "Фотореализм",
            "Концепт-арт", 
            "Портрет",
            "Пейзаж",
            "Абстракция",
            "Без ограничений"
        ])
        style_layout.addWidget(self.style_combo)
        
        layout.addWidget(style_group)
        
        # Группа размеров
        size_group = QGroupBox("Размер изображения")
        size_layout = QVBoxLayout(size_group)
        
        # Предустановленные размеры
        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "512x512 (Квадрат)",
            "768x768 (Квадрат HD)",
            "512x768 (Портрет)",
            "768x512 (Пейзаж)", 
            "1024x1024 (Большой квадрат)",
            "Пользовательский"
        ])
        size_layout.addWidget(self.size_combo)
        
        # Пользовательские размеры
        custom_size_layout = QHBoxLayout()
        
        width_label = QLabel("Ширина:")
        custom_size_layout.addWidget(width_label)
        
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(256, 1024)
        self.width_spinbox.setValue(512)
        self.width_spinbox.setSingleStep(64)
        custom_size_layout.addWidget(self.width_spinbox)
        
        height_label = QLabel("Высота:")
        custom_size_layout.addWidget(height_label)
        
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(256, 1024)
        self.height_spinbox.setValue(512)
        self.height_spinbox.setSingleStep(64)
        custom_size_layout.addWidget(self.height_spinbox)
        
        size_layout.addLayout(custom_size_layout)
        
        layout.addWidget(size_group)
        
        # Группа качества
        quality_group = QGroupBox("Качество генерации")
        quality_layout = QVBoxLayout(quality_group)
        
        # Количество шагов
        steps_label = QLabel("Шаги генерации:")
        quality_layout.addWidget(steps_label)
        
        steps_layout = QHBoxLayout()
        self.steps_slider = QSlider(Qt.Horizontal)
        self.steps_slider.setRange(10, 100)
        self.steps_slider.setValue(50)
        steps_layout.addWidget(self.steps_slider)
        
        self.steps_value_label = QLabel("50")
        steps_layout.addWidget(self.steps_value_label)
        
        quality_layout.addLayout(steps_layout)
        
        # Guidance Scale
        guidance_label = QLabel("Сила следования промпту:")
        quality_layout.addWidget(guidance_label)
        
        guidance_layout = QHBoxLayout()
        self.guidance_slider = QSlider(Qt.Horizontal)
        self.guidance_slider.setRange(1, 20)
        self.guidance_slider.setValue(7)
        guidance_layout.addWidget(self.guidance_slider)
        
        self.guidance_value_label = QLabel("7.5")
        guidance_layout.addWidget(self.guidance_value_label)
        
        quality_layout.addLayout(guidance_layout)
        
        layout.addWidget(quality_group)
        
        # Группа модели
        model_group = QGroupBox("Модель")
        model_layout = QVBoxLayout(model_group)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Demo Mode",
            "Stable Diffusion v1.5",
            "Stable Diffusion v2.1",
            "Stable Diffusion XL",
            "Waifu Diffusion (Аниме)",
            "Realistic Vision v4.0",
            "DreamShaper v8"
        ])
        model_layout.addWidget(self.model_combo)
        
        self.model_status_label = QLabel("Demo режим активен")
        self.model_status_label.setStyleSheet("color: #4ade80;")
        model_layout.addWidget(self.model_status_label)
        
        layout.addWidget(model_group)
        
        # Кнопки управления
        buttons_layout = QVBoxLayout()
        
        self.generate_button = QPushButton("🎨 Генерировать")
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
        
    def create_prompt_panel(self, parent):
        """Создание панели промптов"""
        prompt_widget = QWidget()
        layout = QVBoxLayout(prompt_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Позитивный промпт
        positive_group = QGroupBox("Описание изображения (что создать)")
        positive_layout = QVBoxLayout(positive_group)
        
        # Панель инструментов
        positive_toolbar = QHBoxLayout()
        
        self.load_prompt_button = QPushButton("📁 Загрузить")
        positive_toolbar.addWidget(self.load_prompt_button)
        
        self.save_prompt_button = QPushButton("💾 Сохранить")
        positive_toolbar.addWidget(self.save_prompt_button)
        
        positive_toolbar.addStretch()
        
        positive_char_label = QLabel("Символов: 0")
        positive_toolbar.addWidget(positive_char_label)
        self.positive_char_label = positive_char_label
        
        positive_layout.addLayout(positive_toolbar)
        
        # Поле ввода позитивного промпта
        self.positive_prompt = QPlainTextEdit()
        self.positive_prompt.setPlaceholderText(
            "Опишите, что вы хотите видеть на изображении...\n\n"
            "Примеры:\n"
            "• 'beautiful landscape with mountains and lake, sunset'\n"
            "• 'portrait of a woman, detailed face, professional lighting'\n"
            "• 'futuristic city, cyberpunk style, neon lights'"
        )
        self.positive_prompt.setMaximumHeight(150)
        
        positive_layout.addWidget(self.positive_prompt)
        
        layout.addWidget(positive_group)
        
        # Негативный промпт
        negative_group = QGroupBox("Негативное описание (что НЕ создавать)")
        negative_layout = QVBoxLayout(negative_group)
        
        # Панель инструментов
        negative_toolbar = QHBoxLayout()
        
        self.preset_negative_button = QPushButton("📋 Стандартные")
        negative_toolbar.addWidget(self.preset_negative_button)
        
        self.clear_negative_button = QPushButton("🗑️ Очистить")
        negative_toolbar.addWidget(self.clear_negative_button)
        
        negative_toolbar.addStretch()
        
        negative_char_label = QLabel("Символов: 0")
        negative_toolbar.addWidget(negative_char_label)
        self.negative_char_label = negative_char_label
        
        negative_layout.addLayout(negative_toolbar)
        
        # Поле ввода негативного промпта
        self.negative_prompt = QPlainTextEdit()
        self.negative_prompt.setPlaceholderText(
            "Опишите, чего НЕ должно быть на изображении...\n\n"
            "Примеры:\n"
            "• 'blurry, low quality, distorted, ugly'\n"
            "• 'extra limbs, deformed hands, bad anatomy'\n"
            "• 'text, watermark, signature'"
        )
        self.negative_prompt.setMaximumHeight(120)
        
        negative_layout.addWidget(self.negative_prompt)
        
        layout.addWidget(negative_group)
        
        # Предварительные настройки
        presets_group = QGroupBox("Быстрые настройки")
        presets_layout = QVBoxLayout(presets_group)
        
        presets_buttons_layout = QGridLayout()
        
        # Кнопки предустановок
        preset_buttons = [
            ("🏞️ Пейзаж", self.apply_landscape_preset),
            ("👤 Портрет", self.apply_portrait_preset),
            ("🎨 Арт", self.apply_art_preset),
            ("📷 Фото", self.apply_photo_preset),
            ("🌙 Аниме", self.apply_anime_preset),
            ("🔬 Концепт", self.apply_concept_preset)
        ]
        
        for i, (text, callback) in enumerate(preset_buttons):
            button = QPushButton(text)
            button.clicked.connect(callback)
            presets_buttons_layout.addWidget(button, i // 2, i % 2)
            
        presets_layout.addLayout(presets_buttons_layout)
        
        layout.addWidget(presets_group)
        
        # Добавляем растягивающее пространство
        layout.addStretch()
        
        parent.addWidget(prompt_widget)
        
    def create_image_panel(self, parent):
        """Создание панели изображения"""
        image_widget = QWidget()
        layout = QVBoxLayout(image_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок
        title_layout = QHBoxLayout()
        title_label = QLabel("Результат генерации")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Информация об изображении
        self.image_info_label = QLabel("Изображение не создано")
        self.image_info_label.setStyleSheet("color: #888888;")
        title_layout.addWidget(self.image_info_label)
        
        layout.addLayout(title_layout)
        
        # Область просмотра изображения
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        
        self.image_viewer = ImageViewer()
        scroll_area.setWidget(self.image_viewer)
        
        layout.addWidget(scroll_area, 1)
        
        # Панель инструментов для изображения
        image_toolbar = QHBoxLayout()
        
        self.save_image_button = QPushButton("💾 Сохранить")
        self.save_image_button.setEnabled(False)
        image_toolbar.addWidget(self.save_image_button)
        
        self.copy_image_button = QPushButton("📋 Копировать")
        self.copy_image_button.setEnabled(False)
        image_toolbar.addWidget(self.copy_image_button)
        
        image_toolbar.addStretch()
        
        layout.addLayout(image_toolbar)
        
        parent.addWidget(image_widget)
        
    def setup_connections(self):
        """Настройка связей"""
        # Слайдеры
        self.steps_slider.valueChanged.connect(
            lambda v: self.steps_value_label.setText(str(v))
        )
        
        self.guidance_slider.valueChanged.connect(
            lambda v: self.guidance_value_label.setText(f"{v/2:.1f}")
        )
        
        # Размеры
        self.size_combo.currentTextChanged.connect(self.on_size_preset_changed)
        
        # Кнопки управления
        self.generate_button.clicked.connect(self.start_generation)
        self.stop_button.clicked.connect(self.stop_generation)
        self.load_model_button.clicked.connect(self.load_model)
        self.clear_button.clicked.connect(self.clear_all)
        
        # Кнопки промптов
        self.load_prompt_button.clicked.connect(self.load_prompt_file)
        self.save_prompt_button.clicked.connect(self.save_prompt_file)
        self.preset_negative_button.clicked.connect(self.apply_preset_negative)
        self.clear_negative_button.clicked.connect(self.clear_negative)
        
        # Кнопки изображения
        self.save_image_button.clicked.connect(self.save_image)
        self.copy_image_button.clicked.connect(self.copy_image)
        
        # Отслеживание изменений
        self.positive_prompt.textChanged.connect(self.update_positive_stats)
        self.negative_prompt.textChanged.connect(self.update_negative_stats)
        self.positive_prompt.textChanged.connect(self.on_prompt_changed)
        self.negative_prompt.textChanged.connect(self.on_prompt_changed)
        
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
        
    def on_prompt_changed(self):
        """Обработка изменения промпта"""
        self._unsaved_changes = True
        
    def update_positive_stats(self):
        """Обновление статистики позитивного промпта"""
        text = self.positive_prompt.toPlainText()
        char_count = len(text)
        self.positive_char_label.setText(f"Символов: {char_count}")
        
    def update_negative_stats(self):
        """Обновление статистики негативного промпта"""
        text = self.negative_prompt.toPlainText()
        char_count = len(text)
        self.negative_char_label.setText(f"Символов: {char_count}")
        
    def on_size_preset_changed(self, preset):
        """Обработка изменения предустановки размера"""
        if "512x512" in preset:
            self.width_spinbox.setValue(512)
            self.height_spinbox.setValue(512)
        elif "768x768" in preset:
            self.width_spinbox.setValue(768)
            self.height_spinbox.setValue(768)
        elif "512x768" in preset:
            self.width_spinbox.setValue(512)
            self.height_spinbox.setValue(768)
        elif "768x512" in preset:
            self.width_spinbox.setValue(768)
            self.height_spinbox.setValue(512)
        elif "1024x1024" in preset:
            self.width_spinbox.setValue(1024)
            self.height_spinbox.setValue(1024)
            
    def on_model_changed(self):
        """Обработка изменения модели"""
        if self.model_combo.currentText() != "Demo Mode":
            self.model_status_label.setText("Модель не загружена")
            self.model_status_label.setStyleSheet("color: #ff6b6b;")
            
    def start_generation(self):
        """Начало генерации изображения"""
        positive_prompt = self.positive_prompt.toPlainText().strip()
        
        if not positive_prompt:
            QMessageBox.warning(self, "Предупреждение", "Введите описание изображения!")
            return
            
        if not self.generator.is_loaded():
            QMessageBox.warning(self, "Предупреждение", "Загрузите модель перед генерацией!")
            return
            
        # Настройки генерации
        settings = {
            'width': self.width_spinbox.value(),
            'height': self.height_spinbox.value(),
            'steps': self.steps_slider.value(),
            'guidance_scale': self.guidance_slider.value() / 2.0,
            'style': self.style_combo.currentText()
        }
        
        negative_prompt = self.negative_prompt.toPlainText().strip()
        
        # Создание и запуск рабочего потока
        self.generation_worker = ImageGenerationWorker(
            self.generator, positive_prompt, negative_prompt, settings
        )
        
        self.generation_worker.progress_changed.connect(self.progress_changed.emit)
        self.generation_worker.status_changed.connect(self.status_changed.emit)
        self.generation_worker.image_generated.connect(self.on_image_generated)
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
            
    def on_image_generated(self, image):
        """Обработка сгенерированного изображения"""
        self._current_image = image
        self.image_viewer.set_image(image)
        
        # Обновление информации
        if image:
            w, h = image.size
            self.image_info_label.setText(f"{w}x{h} пикселей")
            self.save_image_button.setEnabled(True)
            self.copy_image_button.setEnabled(True)
        
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
            self.status_changed.emit("Загрузка модели изображений...")
            self.load_model_button.setEnabled(False)
            
            success = self.generator.load_model(model_name)
            
            if success:
                self.model_status_label.setText("Модель загружена")
                self.model_status_label.setStyleSheet("color: #4ade80;")
                self.status_changed.emit("Модель изображений успешно загружена")
            else:
                self.model_status_label.setText("Ошибка загрузки")
                self.model_status_label.setStyleSheet("color: #ff6b6b;")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить модель:\n{str(e)}")
            
        finally:
            self.load_model_button.setEnabled(True)
            
    def apply_preset_negative(self):
        """Применение стандартного негативного промпта"""
        standard_negative = (
            "blurry, low quality, bad quality, low res, poor quality, "
            "distorted, deformed, ugly, bad anatomy, extra limbs, "
            "text, watermark, signature, username, artist name"
        )
        self.negative_prompt.setPlainText(standard_negative)
        
    def clear_negative(self):
        """Очистка негативного промпта"""
        self.negative_prompt.clear()
        
    # Методы предустановок
    def apply_landscape_preset(self):
        """Предустановка для пейзажа"""
        self.style_combo.setCurrentText("Пейзаж")
        self.width_spinbox.setValue(768)
        self.height_spinbox.setValue(512)
        self.size_combo.setCurrentText("768x512 (Пейзаж)")
        
    def apply_portrait_preset(self):
        """Предустановка для портрета"""
        self.style_combo.setCurrentText("Портрет")
        self.width_spinbox.setValue(512)
        self.height_spinbox.setValue(768)
        self.size_combo.setCurrentText("512x768 (Портрет)")
        
    def apply_art_preset(self):
        """Предустановка для искусства"""
        self.style_combo.setCurrentText("Художественный")
        self.steps_slider.setValue(75)
        self.guidance_slider.setValue(15)
        
    def apply_photo_preset(self):
        """Предустановка для фото"""
        self.style_combo.setCurrentText("Фотореализм")
        self.steps_slider.setValue(60)
        self.guidance_slider.setValue(12)
        
    def apply_anime_preset(self):
        """Предустановка для аниме"""
        self.style_combo.setCurrentText("Аниме")
        self.steps_slider.setValue(50)
        self.guidance_slider.setValue(10)
        
    def apply_concept_preset(self):
        """Предустановка для концепт-арта"""
        self.style_combo.setCurrentText("Концепт-арт")
        self.steps_slider.setValue(80)
        self.guidance_slider.setValue(14)
        
    def save_image(self):
        """Сохранение изображения"""
        if not self._current_image:
            QMessageBox.warning(self, "Предупреждение", "Нет изображения для сохранения!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить изображение",
            "generated_image.png",
            "Изображения PNG (*.png);;Изображения JPEG (*.jpg);;Все файлы (*)"
        )
        
        if file_path:
            try:
                self._current_image.save(file_path)
                self.status_changed.emit(f"Изображение сохранено: {os.path.basename(file_path)}")
                self._unsaved_changes = False
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изображение:\n{str(e)}")
                
    def copy_image(self):
        """Копирование изображения в буфер обмена"""
        if self._current_image:
            self.status_changed.emit("Изображение скопировано в буфер обмена")
        else:
            QMessageBox.information(self, "Информация", "Нет изображения для копирования!")
            
    def load_prompt_file(self):
        """Загрузка промпта из файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить промпт",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.positive_prompt.setPlainText(content)
                self.status_changed.emit(f"Промпт загружен: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
                
    def save_prompt_file(self):
        """Сохранение промпта в файл"""
        prompt_text = self.positive_prompt.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Предупреждение", "Нет промпта для сохранения!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить промпт",
            "prompt.txt",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(prompt_text)
                self.status_changed.emit(f"Промпт сохранен: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
                
    def clear_all(self):
        """Очистка всего"""
        reply = QMessageBox.question(
            self, 
            'Очистка', 
            'Очистить все данные? Несохраненные изменения будут утеряны.',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.positive_prompt.clear()
            self.negative_prompt.clear()
            self.image_viewer.set_image(None)
            self._current_image = None
            self.save_image_button.setEnabled(False)
            self.copy_image_button.setEnabled(False)
            self.image_info_label.setText("Изображение не создано")
            self._unsaved_changes = False
            
    def has_unsaved_changes(self):
        """Проверка несохраненных изменений"""
        return self._unsaved_changes
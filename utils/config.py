#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система конфигурации для AI Desktop приложения
"""

import os
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """Класс для управления конфигурацией приложения"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Инициализация конфигурации"""
        # Определение директории конфигурации
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Пользовательская директория для конфигурации
            if os.name == 'nt':  # Windows
                self.config_dir = Path.home() / "AppData" / "Local" / "AIDesktopGenerator"
            else:  # Linux/Mac
                self.config_dir = Path.home() / ".config" / "ai-desktop-generator"
                
        # Создание директорий
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir = self.config_dir / "cache"
            self.models_dir = self.config_dir / "models" 
            self.projects_dir = self.config_dir / "projects"
            
            for directory in [self.cache_dir, self.models_dir, self.projects_dir]:
                directory.mkdir(exist_ok=True)
        except Exception:
            # Fallback к локальным папкам если нет прав
            self.config_dir = Path(".")
            self.cache_dir = Path("cache")
            self.models_dir = Path("models_cache")
            self.projects_dir = Path("projects")
            
            for directory in [self.cache_dir, self.models_dir, self.projects_dir]:
                directory.mkdir(exist_ok=True)
            
        # Файлы конфигурации
        self.config_file = self.config_dir / "config.json"
        self.settings_file = self.config_dir / "settings.json"
        
        # Загрузка конфигурации
        self._config = self._load_config()
        self._settings = self._load_settings()
        
        # Настройка логирования
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка основной конфигурации"""
        default_config = {
            "app_version": "1.0.0",
            "first_run": True,
            "auto_save": True,
            "auto_save_interval": 300,
            "backup_enabled": True,
            "max_backups": 10
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception:
                pass
                
        return default_config
        
    def _load_settings(self) -> Dict[str, Any]:
        """Загрузка пользовательских настроек"""
        default_settings = {
            # Настройки интерфейса
            "ui": {
                "theme": "dark",
                "language": "ru",
                "font_size": 9,
                "font_family": "Segoe UI",
                "window_geometry": None,
                "window_state": None
            },
            
            # Настройки текстовой генерации
            "text_generation": {
                "default_model": "GPT-J 6B (Рекомендуется)",
                "default_style": "Нейтральный",
                "default_max_length": 500,
                "default_temperature": 0.7,
                "auto_load_model": False,
                "quantization": True
            },
            
            # Настройки генерации изображений
            "image_generation": {
                "default_model": "Stable Diffusion v1.5",
                "default_style": "Реалистичный",
                "default_width": 512,
                "default_height": 512,
                "default_steps": 50,
                "default_guidance": 7.5,
                "safety_checker": False,
                "auto_load_model": False
            },
            
            # Системные настройки
            "system": {
                "device": "auto",  # auto, cuda, cpu
                "cache_models": True,
                "cleanup_on_exit": True
            },
            
            # Настройки файлов
            "files": {
                "last_project_dir": str(self.projects_dir),
                "last_import_dir": str(Path.home()),
                "last_export_dir": str(Path.home()),
                "default_text_format": "txt",
                "default_image_format": "png"
            }
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self._deep_update(default_settings, loaded_settings)
            except Exception:
                pass
                
        return default_settings
        
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Рекурсивное обновление словаря"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения из конфигурации"""
        try:
            if '.' in key:
                keys = key.split('.')
                value = self._settings
                for k in keys:
                    value = value[k]
                return value
            else:
                return self._config.get(key, default)
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any):
        """Установка значения в конфигурации"""
        try:
            if '.' in key:
                keys = key.split('.')
                target = self._settings
                for k in keys[:-1]:
                    if k not in target:
                        target[k] = {}
                    target = target[k]
                target[keys[-1]] = value
            else:
                self._config[key] = value
        except Exception:
            pass
            
    def save(self):
        """Сохранение конфигурации"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
                
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
            
    def get_cache_dir(self) -> Path:
        """Получение директории кэша"""
        return self.cache_dir
        
    def get_models_dir(self) -> Path:
        """Получение директории моделей"""
        return self.models_dir
        
    def get_projects_dir(self) -> Path:
        """Получение директории проектов"""
        return self.projects_dir
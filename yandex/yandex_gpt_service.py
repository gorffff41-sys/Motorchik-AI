#!/usr/bin/env python3
"""
Сервис для работы с YandexGPT
"""

import os
import sys
import time
import json
import logging
import torch
from typing import Dict, List, Optional, Any
from datetime import datetime

# Добавляем путь к корневой директории
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger("yandex_gpt_service")

class YandexGPTService:
    """Сервис для работы с YandexGPT"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.model = None
        self.tokenizer = None
        self.device = None
        self.available = False
        self.model_name = "yandex/YandexGPT-5-Lite-8B-instruct"
        
        logger.info("🤖 Инициализация YandexGPT сервиса...")
        self._init_model()
    
    def _init_model(self):
        """Инициализация модели YandexGPT"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            logger.info("📦 Загрузка токенизатора YandexGPT...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_fast=False
            )
            logger.info("✅ Токенизатор загружен")
            
            logger.info("📦 Загрузка модели YandexGPT...")
            # Определяем доступность CUDA
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"🔧 Используется устройство: {self.device}")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                device_map="auto" if self.device == "cuda" else None,
                torch_dtype="auto" if self.device == "cuda" else torch.float32,
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            logger.info("✅ Модель загружена")
            self.available = True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации YandexGPT: {e}")
            self.available = False
    
    def generate_response(self, query: str, user_id: str = "default", context: Optional[Dict] = None) -> Dict[str, Any]:
        """Генерация ответа с помощью YandexGPT"""
        if not self.available:
            logger.warning("❌ YandexGPT недоступен")
            return {
                "success": False,
                "message": "YandexGPT недоступен",
                "type": "yandex_error"
            }
        
        try:
            logger.info(f"🧠 YandexGPT: Начало обработки запроса")
            logger.info(f"🧠 YandexGPT: Запрос: {query}")
            logger.info(f"🧠 YandexGPT: User ID: {user_id}")
            
            # Создание промпта
            prompt = self._create_prompt(query, context)
            logger.info(f"🧠 YandexGPT: Создан промпт длиной {len(prompt)} символов")
            
            # Генерация ответа
            response = self._generate_text(prompt)
            logger.info(f"🧠 YandexGPT: Ответ сгенерирован длиной {len(response)} символов")
            
            return {
                "success": True,
                "message": response,
                "type": "yandex_response",
                "model": self.model_name,
                "device": self.device
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при генерации ответа YandexGPT: {e}")
            return {
                "success": False,
                "message": f"Ошибка при генерации ответа: {str(e)}",
                "type": "yandex_error"
            }
    
    def _create_prompt(self, query: str, context: Optional[Dict] = None) -> str:
        """Создание промпта для YandexGPT"""
        
        prompt = f"""
Ты - эксперт по автомобилям МОТОРЧИК. Пользователь задал следующий вопрос: "{query}"

"""
        
        # Добавляем контекст, если есть
        if context:
            if context.get('cars'):
                prompt += f"Доступные автомобили:\n"
                for i, car in enumerate(context['cars'][:5], 1):
                    prompt += f"{i}. {car.get('mark', 'N/A')} {car.get('model', 'N/A')}\n"
                    prompt += f"   Цена: {car.get('price', 'N/A')} ₽\n"
                    prompt += f"   Год: {car.get('manufacture_year', 'N/A')}\n"
                    prompt += f"   Цвет: {car.get('color', 'N/A')}\n"
                    prompt += f"   Город: {car.get('city', 'N/A')}\n\n"
        
        prompt += f"""
Пожалуйста, предоставь полезный и информативный ответ на запрос пользователя. 
Будь дружелюбным и профессиональным. Если информации недостаточно, предложи альтернативные варианты поиска.
Отвечай на русском языке.
"""
        
        return prompt
    
    def _generate_text(self, prompt: str) -> str:
        """Генерация текста с помощью модели"""
        
        # Формируем сообщения в формате чата
        messages = [{"role": "user", "content": prompt}]
        
        # Применяем шаблон чата
        input_ids = self.tokenizer.apply_chat_template(
            messages, tokenize=True, return_tensors="pt"
        )
        
        if self.device == "cuda":
            input_ids = input_ids.to(self.device)
        
        # Генерируем ответ
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids, 
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Декодируем ответ
        response = self.tokenizer.decode(outputs[0][input_ids.size(1):], skip_special_tokens=True)
        
        return response.strip()
    
    def is_available(self) -> bool:
        """Проверка доступности сервиса"""
        return self.available
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса сервиса"""
        return {
            "available": self.available,
            "model_name": self.model_name,
            "device": self.device,
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None
        }

# Создаем глобальный экземпляр сервиса
yandex_gpt_service = YandexGPTService()

def get_yandex_gpt_service() -> YandexGPTService:
    """Получение глобального экземпляра сервиса"""
    return yandex_gpt_service 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Временный сервис для работы с Mistral API
"""

import os
import requests
import json
import logging

logger = logging.getLogger(__name__)

class MistralService:
    """Сервис для работы с Mistral API"""
    
    def __init__(self):
        # Ключ больше не хранится в коде; при необходимости берется из переменных окружения
        self.api_key = os.environ.get("MISTRAL_API_KEY", "")
        self.base_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = "mistral-large-latest"
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """
        Генерирует ответ через Mistral API
        
        Args:
            prompt: Пользовательский запрос
            system_prompt: Системный промт (опционально)
            
        Returns:
            str: Сгенерированный ответ
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Mistral API error: {response.status_code} - {response.text}")
                return "Извините, произошла ошибка при обработке запроса."
                
        except Exception as e:
            logger.error(f"Ошибка при обращении к Mistral API: {e}")
            return "Извините, произошла ошибка при обработке запроса."

# Глобальный экземпляр сервиса
mistral_service = MistralService()

def generate_mistral_response(prompt: str, system_prompt: str = None) -> str:
    """
    Удобная функция для генерации ответа через Mistral
    
    Args:
        prompt: Пользовательский запрос
        system_prompt: Системный промт (опционально)
        
    Returns:
        str: Сгенерированный ответ
    """
    return mistral_service.generate_response(prompt, system_prompt)

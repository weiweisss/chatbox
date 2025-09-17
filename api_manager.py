import openai
import json
import os
from typing import List, Dict

class APIManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.clients = {}  # 存储不同AI的客户端
        self.current_ai_id = None
        self.update_config(config_manager)
        
    def update_config(self, config_manager):
        """更新API配置"""
        self.config_manager = config_manager
        # 重新加载所有AI配置
        self.clients = {}
        default_ai_id, default_ai_config = config_manager.get_default_ai()
        if default_ai_id and default_ai_config:
            self.current_ai_id = default_ai_id
            self._create_client(default_ai_id, default_ai_config)
            
    def _create_client(self, ai_id, ai_config):
        """为指定AI创建客户端"""
        api_key = ai_config.get("api_key", "")
        base_url = ai_config.get("base_url", "https://api.openai.com/v1")
        
        if api_key:
            self.clients[ai_id] = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
        elif ai_id in self.clients:
            del self.clients[ai_id]
            
    def switch_ai(self, ai_id):
        """切换当前使用的AI"""
        if ai_id in self.config_manager.get_ais():
            self.current_ai_id = ai_id
            # 如果还没有为这个AI创建客户端，则创建一个
            if ai_id not in self.clients:
                ai_config = self.config_manager.get_ai(ai_id)
                if ai_config:
                    self._create_client(ai_id, ai_config)
            return True
        return False
        
    def get_current_ai_config(self):
        """获取当前AI配置"""
        if self.current_ai_id:
            return self.config_manager.get_ai(self.current_ai_id)
        return None
        
    def get_current_ai_name(self):
        """获取当前AI名称"""
        ai_config = self.get_current_ai_config()
        if ai_config:
            return ai_config.get("name", "未知AI")
        return "未选择AI"
        
    def get_response(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """获取AI响应"""
        if not self.current_ai_id or self.current_ai_id not in self.clients:
            # 尝试使用默认AI
            default_ai_id, default_ai_config = self.config_manager.get_default_ai()
            if default_ai_id and default_ai_config:
                self.current_ai_id = default_ai_id
                if default_ai_id not in self.clients:
                    self._create_client(default_ai_id, default_ai_config)
            else:
                raise Exception("未配置AI或API密钥未设置")
                
        if self.current_ai_id not in self.clients:
            raise Exception("AI客户端未正确初始化")
            
        try:
            # 获取当前AI配置
            ai_config = self.config_manager.get_ai(self.current_ai_id)
            if not ai_config:
                raise Exception("无法获取AI配置")
                
            model = ai_config.get("model", "gpt-3.5-turbo")
            client = self.clients[self.current_ai_id]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except openai.APIError as e:
            raise Exception(f"API调用错误: {str(e)}")
        except Exception as e:
            raise Exception(f"请求失败: {str(e)}")
            
    def refresh_ai_list(self):
        """刷新AI列表"""
        # 清除所有客户端
        self.clients = {}
        # 重新创建当前AI的客户端
        if self.current_ai_id:
            ai_config = self.config_manager.get_ai(self.current_ai_id)
            if ai_config:
                self._create_client(self.current_ai_id, ai_config)
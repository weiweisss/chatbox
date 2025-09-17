import json
import os
import sys
import uuid
from datetime import datetime

# Determine the base path for data files, works for script and frozen exe
if getattr(sys, 'frozen', False):
    # Running as a bundled exe
    APP_BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as a .py script
    APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(APP_BASE_DIR, 'data')

class ConfigManager:
    def __init__(self):
        self.config_file = os.path.join(DATA_DIR, "config.json")
        self.config = {}
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        # 确保数据目录存在
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(self.config_file):
            # 创建默认AI配置
            default_ai_id = str(uuid.uuid4())
            self.config = {
                "default_ai": default_ai_id,
                "autostart": False,
                "ais": {
                    default_ai_id: {
                        "name": "显示名称",
                        "api_key": "",
                        "base_url": "https://api.openai.com/v1",
                        "model": "gpt-3.5-turbo"
                    }
                }
            }
            self.save_config()
        else:
            # 读取现有配置
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                
            # 确保配置结构正确
            if "ais" not in self.config:
                # 迁移旧配置格式
                default_ai_id = str(uuid.uuid4())
                self.config["ais"] = {
                    default_ai_id: {
                        "name": "默认AI",
                        "api_key": self.config.get("api_key", ""),
                        "base_url": self.config.get("base_url", "https://api.openai.com/v1"),
                        "model": self.config.get("model", "gpt-3.5-turbo")
                    }
                }
                self.config["default_ai"] = default_ai_id
                # 移除旧配置项
                self.config.pop("api_key", None)
                self.config.pop("base_url", None)
                self.config.pop("model", None)
                self.save_config()
                
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
            
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self.save_config()
        
    def update(self, config_dict):
        """批量更新配置"""
        self.config.update(config_dict)
        self.save_config()
        
    # AI配置管理方法
    def get_ais(self):
        """获取所有AI配置"""
        return self.config.get("ais", {})
        
    def get_ai(self, ai_id):
        """获取指定AI配置"""
        return self.config.get("ais", {}).get(ai_id)
        
    def add_ai(self, name, api_key, base_url, model):
        """添加新的AI配置"""
        ai_id = str(uuid.uuid4())
        if "ais" not in self.config:
            self.config["ais"] = {}
            
        self.config["ais"][ai_id] = {
            "name": name,
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        }
        
        # 如果还没有默认AI，设置这个为默认
        if "default_ai" not in self.config or not self.config["default_ai"]:
            self.config["default_ai"] = ai_id
            
        self.save_config()
        return ai_id
        
    def update_ai(self, ai_id, name, api_key, base_url, model):
        """更新AI配置"""
        if "ais" not in self.config:
            self.config["ais"] = {}
            
        self.config["ais"][ai_id] = {
            "name": name,
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        }
        self.save_config()
        
    def delete_ai(self, ai_id):
        """删除AI配置"""
        if "ais" in self.config and ai_id in self.config["ais"]:
            del self.config["ais"][ai_id]
            
            # 如果删除的是默认AI，设置新的默认AI
            if self.config.get("default_ai") == ai_id:
                if self.config["ais"]:
                    self.config["default_ai"] = next(iter(self.config["ais"]))
                else:
                    self.config["default_ai"] = None
                    
            self.save_config()
            
    def set_default_ai(self, ai_id):
        """设置默认AI"""
        if "ais" in self.config and ai_id in self.config["ais"]:
            self.config["default_ai"] = ai_id
            self.save_config()
            
    def get_default_ai(self):
        """获取默认AI配置"""
        default_ai_id = self.config.get("default_ai")
        if default_ai_id and "ais" in self.config and default_ai_id in self.config["ais"]:
            return default_ai_id, self.config["ais"][default_ai_id]
        elif "ais" in self.config and self.config["ais"]:
            # 如果没有默认AI但有AI配置，返回第一个
            first_ai_id = next(iter(self.config["ais"]))
            return first_ai_id, self.config["ais"][first_ai_id]
        else:
            return None, None
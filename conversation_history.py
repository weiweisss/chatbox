import json
import os
from datetime import datetime
from typing import List, Dict

class ConversationHistory:
    def __init__(self, history_dir="data/history"):
        self.history_dir = history_dir
        self.current_session_id = None
        self.ensure_history_dir()
        
    def ensure_history_dir(self):
        """确保历史记录目录存在"""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
            
    def create_new_session(self):
        """创建新的对话会话"""
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.current_session_id
        
    def get_current_history(self) -> List[Dict[str, str]]:
        """获取当前会话的历史记录"""
        if not self.current_session_id:
            self.create_new_session()
            
        history_file = os.path.join(self.history_dir, f"{self.current_session_id}.json")
        
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("messages", [])
        else:
            return []
            
    def save_current_history(self, messages: List[Dict[str, str]]):
        """保存当前会话的历史记录"""
        if not self.current_session_id:
            self.create_new_session()
            
        history_file = os.path.join(self.history_dir, f"{self.current_session_id}.json")
        
        # 创建会话数据
        session_data = {
            "session_id": self.current_session_id,
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }
        
        # 保存到文件
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
            
    def get_all_sessions(self) -> List[Dict[str, str]]:
        """获取所有会话列表"""
        sessions = []
        
        for filename in os.listdir(self.history_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.history_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 获取第一条消息作为会话标题
                    first_message = ""
                    if data.get("messages"):
                        first_message = data["messages"][0].get("content", "")[:30] + "..."
                    
                    sessions.append({
                        "session_id": data.get("session_id"),
                        "title": first_message,
                        "timestamp": data.get("timestamp")
                    })
                    
        # 按时间倒序排列
        sessions.sort(key=lambda x: x["timestamp"], reverse=True)
        return sessions
        
    def load_session(self, session_id: str) -> List[Dict[str, str]]:
        """加载指定会话的历史记录"""
        history_file = os.path.join(self.history_dir, f"{session_id}.json")
        
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("messages", [])
        else:
            return []
            
    def delete_session(self, session_id: str):
        """删除指定会话"""
        history_file = os.path.join(self.history_dir, f"{session_id}.json")
        
        if os.path.exists(history_file):
            os.remove(history_file)
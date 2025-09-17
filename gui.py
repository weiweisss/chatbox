import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
from datetime import datetime
import threading
from api_manager import APIManager
from conversation_history import ConversationHistory
from config import ConfigManager
from autostart import AutoStartManager

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI助手")
        self.root.geometry("400x500")
        self.root.attributes('-topmost', True)  # 窗口置顶
        self.root.overrideredirect(True)  # 无边框窗口
        
        # 初始化组件
        self.config_manager = ConfigManager()
        self.api_manager = APIManager(self.config_manager)
        self.history_manager = ConversationHistory()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化拖动功能
        self.drag_data = {"x": 0, "y": 0}
        self.setup_drag_binding()
        
    def create_widgets(self):
        # 标题栏（用于拖动）
        self.title_bar = tk.Frame(self.root, bg="#2c3e50", height=30)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)
        
        # 标题文本
        title_label = tk.Label(self.title_bar, text="AI助手", bg="#2c3e50", fg="white", font=("Arial", 10))
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 关闭按钮
        close_btn = tk.Button(self.title_bar, text="×", bg="#e74c3c", fg="white", 
                             font=("Arial", 12), bd=0, padx=10, command=self.root.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 最小化按钮
        minimize_btn = tk.Button(self.title_bar, text="−", bg="#3498db", fg="white", 
                                font=("Arial", 12), bd=0, padx=10, 
                                command=self.root.iconify)
        minimize_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 设置按钮
        settings_btn = tk.Button(self.title_bar, text="⚙", bg="#95a5a6", fg="white", 
                                font=("Arial", 12), bd=0, padx=10, 
                                command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 对话显示区域
        self.chat_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state=tk.DISABLED,
                                                     bg="#ecf0f1", font=("Arial", 10))
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 输入区域
        input_frame = tk.Frame(self.root, bg="#ffffff")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 输入框
        self.user_input = tk.Text(input_frame, height=3, font=("Arial", 10))
        self.user_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 发送按钮
        send_btn = tk.Button(input_frame, text="发送", bg="#2ecc71", fg="white",
                            font=("Arial", 10), command=self.send_message)
        send_btn.pack(side=tk.RIGHT, padx=(5, 0), ipadx=10, ipady=5)
        
        # 绑定回车键发送消息
        self.user_input.bind("<Return>", self.send_message_enter)
        self.user_input.bind("<Shift-Return>", self.new_line)
        
    def setup_drag_binding(self):
        """设置窗口拖动功能"""
        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.on_drag)
        
    def start_drag(self, event):
        """开始拖动窗口"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        
    def on_drag(self, event):
        """拖动窗口"""
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        
    def send_message_enter(self, event):
        """回车键发送消息"""
        self.send_message()
        return "break"  # 阻止默认行为
        
    def new_line(self, event):
        """Shift+回车换行"""
        self.user_input.insert(tk.INSERT, "\n")
        return "break"
        
    def send_message(self):
        """发送用户消息"""
        message = self.user_input.get("1.0", tk.END).strip()
        if not message:
            return
            
        # 显示用户消息
        self.display_message("你", message)
        
        # 清空输入框
        self.user_input.delete("1.0", tk.END)
        
        # 在新线程中获取AI响应
        threading.Thread(target=self.get_ai_response, args=(message,), daemon=True).start()
        
    def get_ai_response(self, user_message):
        """获取AI响应"""
        # 显示正在思考的提示
        self.root.after(0, self.display_message, "AI", "正在思考...")
        
        try:
            # 获取对话历史
            history = self.history_manager.get_current_history()
            
            # 添加用户消息到历史
            history.append({"role": "user", "content": user_message})
            
            # 调用API获取响应
            response = self.api_manager.get_response(history)
            
            # 更新显示（移除"正在思考..."并显示真实响应）
            self.root.after(0, self.update_last_message, "AI", response)
            
            # 添加AI响应到历史
            history.append({"role": "assistant", "content": response})
            self.history_manager.save_current_history(history)
            
        except Exception as e:
            error_msg = f"错误: {str(e)}"
            self.root.after(0, self.update_last_message, "AI", error_msg)
            
    def display_message(self, sender, message):
        """显示消息"""
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
    def update_last_message(self, sender, message):
        """更新最后一条消息"""
        self.chat_display.config(state=tk.NORMAL)
        # 删除最后两行（消息和空行）
        self.chat_display.delete("end-2l", "end-1l")
        # 插入新消息
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
    def open_settings(self):
        """打开设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # API密钥设置
        tk.Label(settings_window, text="API密钥:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        api_key_var = tk.StringVar(value=self.config_manager.get("api_key", ""))
        api_key_entry = tk.Entry(settings_window, textvariable=api_key_var, width=50, show="*")
        api_key_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # API基础URL设置
        tk.Label(settings_window, text="API基础URL:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        base_url_var = tk.StringVar(value=self.config_manager.get("base_url", "https://api.openai.com/v1"))
        base_url_entry = tk.Entry(settings_window, textvariable=base_url_var, width=50)
        base_url_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # 模型选择
        tk.Label(settings_window, text="模型:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        model_var = tk.StringVar(value=self.config_manager.get("model", "gpt-3.5-turbo"))
        model_entry = tk.Entry(settings_window, textvariable=model_var, width=50)
        model_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # 开机自启动设置
        autostart_var = tk.BooleanVar(value=self.config_manager.get("autostart", False))
        autostart_check = tk.Checkbutton(settings_window, text="开机自启动", variable=autostart_var)
        autostart_check.pack(anchor=tk.W, padx=10, pady=5)
        
        # 保存按钮
        def save_settings():
            self.config_manager.set("api_key", api_key_var.get())
            self.config_manager.set("base_url", base_url_var.get())
            self.config_manager.set("model", model_var.get())
            self.config_manager.set("autostart", autostart_var.get())
            
            # 更新API管理器配置
            self.api_manager.update_config(self.config_manager)
            
            # 更新开机自启动设置
            autostart_manager = AutoStartManager()
            if autostart_var.get():
                autostart_manager.enable_autostart()
            else:
                autostart_manager.disable_autostart()
                
            settings_window.destroy()
            
        save_btn = tk.Button(settings_window, text="保存", command=save_settings)
        save_btn.pack(pady=20)

def main():
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
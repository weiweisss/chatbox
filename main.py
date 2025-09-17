import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
from datetime import datetime
import threading
import sys
import os

# 尝试导入图标处理相关模块
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_manager import APIManager
from conversation_history import ConversationHistory
from config import ConfigManager
from autostart import AutoStartManager

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry("400x500")
        self.root.overrideredirect(True)  # 无边框窗口
        self.root.attributes('-topmost', True)  # 窗口置顶
        
        # 绑定主窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_main_window_close)
        
        # 设置应用程序图标
        self.set_application_icon()
        
        # 初始化组件
        self.config_manager = ConfigManager()
        self.api_manager = APIManager(self.config_manager)
        self.history_manager = ConversationHistory()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化拖动功能
        self.drag_data = {"x": 0, "y": 0}
        self.setup_drag_binding()
        
        # 创建新会话
        self.history_manager.create_new_session()
        
        # 更新标题显示当前AI
        self.update_title()
        
    def set_application_icon(self):
        """设置应用程序图标"""
        try:
            # 定义图标文件路径（支持多种格式）
            icon_paths = [
                "icons/ai_icon.png",    # PNG格式图标（优先使用PNG）
                "icons/ai_icon.ico",    # ICO图标
                "data/ai_icon.png",     # 备选PNG图标
                "data/ai_icon.ico",     # 备选ICO图标
                "ai_icon.png",          # 根目录PNG图标
                "ai_icon.ico"           # 根目录ICO图标
            ]
            
            # 尝试加载自定义图标
            icon_set = False
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    try:
                        # 优先使用PNG图标，因为它在任务栏中显示效果更好
                        if icon_path.endswith('.png'):
                            # 使用iconphoto设置PNG图标
                            self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
                        else:
                            # 处理ICO图标
                            self.root.iconbitmap(icon_path)
                        icon_set = True
                        break
                    except Exception as e:
                        print(f"无法加载图标 {icon_path}: {e}")
                        continue
            
            # 如果没有找到自定义图标，使用默认图标
            if not icon_set:
                # 设置默认的Tk图标（这会使用系统的默认图标）
                try:
                    self.root.iconbitmap(default=True)
                except:
                    pass
            
            # 在Windows上设置任务栏图标
            try:
                import ctypes
                # 获取图标文件路径
                icon_path = None
                for path in icon_paths:
                    if os.path.exists(path) and path.endswith('.png'):
                        icon_path = path
                        break
                
                if icon_path:
                    # 设置任务栏图标
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AI助手")
            except:
                pass
                
        except Exception as e:
            print(f"设置图标时出错: {e}")
            # 出错时使用默认行为
            try:
                self.root.iconbitmap(default=True)
            except:
                pass
                
    def set_png_icon(self, window, png_path):
        """设置PNG格式的图标"""
        try:
            if PIL_AVAILABLE:
                # 使用PIL加载PNG图片并设置为图标
                image = Image.open(png_path)
                # 转换为PhotoImage
                photo = ImageTk.PhotoImage(image)
                window.iconphoto(True, photo)
            else:
                # 如果没有PIL，尝试直接使用iconphoto
                window.iconphoto(True, tk.PhotoImage(file=png_path))
        except Exception as e:
            print(f"设置PNG图标时出错: {e}")
            # 回退到默认图标
            window.iconbitmap(default=True)
        
    def create_widgets(self):
        # 标题栏（用于拖动）
        self.title_bar = tk.Frame(self.root, bg="#2c3e50", height=30)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)
        
        # 标题文本
        self.title_label = tk.Label(self.title_bar, text="AI助手", bg="#2c3e50", fg="white", font=("Arial", 10))
        self.title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 关闭按钮
        close_btn = tk.Button(self.title_bar, text="×", bg="#e74c3c", fg="white", 
                             font=("Arial", 12), bd=0, padx=10, command=self.root.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 最小化按钮
        minimize_btn = tk.Button(self.title_bar, text="−", bg="#3498db", fg="white", 
                                font=("Arial", 12), bd=0, padx=10, 
                                command=self.minimize_window)
        minimize_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # AI选择按钮
        self.ai_select_btn = tk.Button(self.title_bar, text="🤖", bg="#f39c12", fg="white", 
                                      font=("Arial", 12), bd=0, padx=10, 
                                      command=self.open_ai_selector)
        self.ai_select_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 设置按钮
        settings_btn = tk.Button(self.title_bar, text="⚙", bg="#95a5a6", fg="white", 
                                font=("Arial", 12), bd=0, padx=10, 
                                command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 新建聊天按钮
        new_chat_btn = tk.Button(self.title_bar, text="+", bg="#9b59b6", fg="white", 
                                font=("Arial", 12), bd=0, padx=10, 
                                command=self.new_chat)
        new_chat_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 历史记录按钮
        history_btn = tk.Button(self.title_bar, text="H", bg="#9b59b6", fg="white", 
                               font=("Arial", 12), bd=0, padx=10, 
                               command=self.open_history)
        history_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
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
        
    def update_title(self):
        """更新标题显示当前AI"""
        current_ai_name = self.api_manager.get_current_ai_name()
        self.root.title(current_ai_name)
        self.title_label.config(text=current_ai_name)
        
    def minimize_window(self):
        """最小化窗口"""
        # 保存当前聊天记录
        try:
            # 在最小化前保存当前会话的所有消息
            self.save_current_session_history()
        except Exception as e:
            print(f"保存聊天记录时出错: {e}")
        
        # 对于无边框窗口，我们隐藏窗口并在任务栏显示通知
        self.root.withdraw()
        
        # 显示提示信息
        self.show_minimize_notification()
        
    def save_current_session_history(self):
        """保存当前会话历史"""
        # 只有当有内容时才保存
        history = self.history_manager.get_current_history()
        if history:  # 只有当有历史记录时才保存
            # 确保会话已创建
            if not self.history_manager.current_session_id:
                self.history_manager.create_new_session()
            # 保存当前历史记录
            self.history_manager.save_current_history(history)
        # 注意：如果没有历史记录，我们不创建空会话
        
    def show_minimize_notification(self):
        """显示最小化通知"""
        try:
            # 创建一个临时的顶层窗口作为任务栏提醒（搜索栏样式）
            self.notification_window = tk.Toplevel()
            # 使用当前AI名称作为窗口标题
            current_ai_name = self.api_manager.get_current_ai_name()
            self.notification_window.title(current_ai_name)
            self.notification_window.geometry("400x100")  # 横向长条形窗口
            self.notification_window.resizable(False, False)
            
            # 设置窗口图标
            self.set_window_icon(self.notification_window)
            
            # 确保窗口在任务栏中显示
            self.notification_window.wm_attributes("-toolwindow", False)
            
            # 设置窗口属性
            self.notification_window.attributes('-topmost', True)
            
            # 绑定窗口关闭事件
            self.notification_window.protocol("WM_DELETE_WINDOW", self.on_notification_window_close)
            
            # 创建主框架
            main_frame = tk.Frame(self.notification_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 添加标签
            tk.Label(main_frame, text=current_ai_name, font=("Arial", 10)).pack(anchor=tk.W)
            
            # 创建输入框架
            input_frame = tk.Frame(main_frame)
            input_frame.pack(fill=tk.X, pady=5)
            
            # 创建输入框
            self.quick_input = tk.Entry(input_frame, font=("Arial", 11))
            self.quick_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 创建发送按钮
            send_btn = tk.Button(input_frame, text="发送", command=self.quick_send_message, 
                                width=8, font=("Arial", 10))
            send_btn.pack(side=tk.RIGHT, padx=(5, 0))
            
            # 绑定回车键发送消息
            self.quick_input.bind("<Return>", lambda event: self.quick_send_message())
            
            # 设置焦点到输入框
            self.quick_input.focus_set()
            
        except Exception as e:
            # 如果创建通知窗口失败，直接恢复主窗口
            self.root.deiconify()
            
    def set_window_icon(self, window):
        """为窗口设置图标"""
        try:
            # 定义图标文件路径（支持多种格式）
            icon_paths = [
                "icons/ai_icon.png",    # PNG格式图标（优先使用PNG）
                "icons/ai_icon.ico",    # ICO图标
                "data/ai_icon.png",     # 备选PNG图标
                "data/ai_icon.ico",     # 备选ICO图标
                "ai_icon.png",          # 根目录PNG图标
                "ai_icon.ico"           # 根目录ICO图标
            ]
            
            # 尝试加载自定义图标
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    try:
                        # 优先使用PNG图标，因为它在任务栏中显示效果更好
                        if icon_path.endswith('.png'):
                            # 使用iconphoto设置PNG图标
                            window.iconphoto(True, tk.PhotoImage(file=icon_path))
                        else:
                            # 处理ICO图标
                            window.iconbitmap(icon_path)
                        return
                    except Exception as e:
                        print(f"无法加载图标 {icon_path}: {e}")
                        continue
                        
            # 如果没有找到自定义图标，尝试使用主窗口的图标
            try:
                window.iconbitmap(default=True)
            except:
                pass
            
        except Exception as e:
            print(f"设置窗口图标时出错: {e}")
            
    def quick_send_message(self):
        """快速发送消息"""
        message = self.quick_input.get().strip()
        if not message:
            # 如果没有消息，恢复主窗口
            self.root.deiconify()
            self.root.lift()
            try:
                self.notification_window.destroy()
            except:
                pass
            return
            
        try:
            # 获取当前AI配置
            ai_config = self.api_manager.get_current_ai_config()
            if not ai_config:
                messagebox.showerror("错误", "未配置AI")
                # 出错后恢复主窗口
                self.root.deiconify()
                self.root.lift()
                try:
                    self.notification_window.destroy()
                except:
                    pass
                return
                
            # 显示处理中提示
            self.quick_input.delete(0, tk.END)
            self.quick_input.insert(0, "正在处理...")
            self.quick_input.config(state=tk.DISABLED)
            
            # 在新线程中处理AI响应
            threading.Thread(target=self.process_quick_message, args=(message,), daemon=True).start()
            
        except Exception as e:
            self.quick_input.config(state=tk.NORMAL)
            self.quick_input.delete(0, tk.END)
            messagebox.showerror("错误", f"发送失败: {str(e)}")
            # 出错后恢复主窗口
            self.root.deiconify()
            self.root.lift()
            try:
                self.notification_window.destroy()
            except:
                pass
            
    def process_quick_message(self, user_message):
        """处理快速消息"""
        try:
            # 创建简单的对话历史（只包含当前消息）
            history = [{"role": "user", "content": user_message}]
            
            # 调用API获取响应
            response = self.api_manager.get_response(history)
            
            # 不再在这里保存对话历史，而是在show_quick_response中保存
            # history.append({"role": "assistant", "content": response})
            # self.history_manager.save_current_history(history)
            
            # 恢复主窗口并显示结果
            self.root.after(0, self.show_quick_response, user_message, response)
            
        except Exception as e:
            self.root.after(0, self.show_quick_error, str(e))
            
    def show_quick_response(self, user_message, ai_response):
        """显示快速响应结果"""
        try:
            self.notification_window.destroy()
        except:
            pass
            
        # 恢复主窗口
        self.root.deiconify()
        self.root.lift()
        
        # 创建新会话（清空当前显示）
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # 创建新的聊天会话
        self.history_manager.create_new_session()
        
        # 显示对话
        self.display_message("你", user_message)
        self.display_message("AI", ai_response)
        
        # 保存新会话的历史记录
        try:
            history = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ]
            self.history_manager.save_current_history(history)
        except Exception as e:
            print(f"保存快速聊天记录时出错: {e}")
        
    def show_quick_error(self, error_message):
        """显示快速响应错误"""
        try:
            self.notification_window.destroy()
        except:
            pass
            
        # 恢复主窗口
        self.root.deiconify()
        self.root.lift()
        
        # 显示错误
        self.display_message("系统", f"错误: {error_message}")
            
    def restore_from_notification(self):
        """从通知恢复窗口"""
        try:
            self.notification_window.destroy()
        except:
            pass
        # 恢复主窗口
        self.root.deiconify()
        self.root.lift()
        
    def on_notification_window_close(self):
        """处理通知窗口关闭事件"""
        # 销毁通知窗口
        try:
            self.notification_window.destroy()
        except:
            pass
        # 恢复主窗口
        self.root.deiconify()
        self.root.lift()
        
    def on_main_window_close(self):
        """处理主窗口关闭事件"""
        # 销毁可能存在的通知窗口
        try:
            self.notification_window.destroy()
        except:
            pass
        # 退出程序
        self.root.destroy()
        
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
            
        # 确保会话已创建
        if not self.history_manager.current_session_id:
            self.history_manager.create_new_session()
            
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
        
    def open_ai_selector(self):
        """打开AI选择窗口"""
        ai_selector_window = tk.Toplevel(self.root)
        ai_selector_window.title("选择AI")
        ai_selector_window.geometry("400x300")
        ai_selector_window.transient(self.root)
        ai_selector_window.grab_set()
        
        # 设置窗口图标
        self.set_window_icon(ai_selector_window)
        
        # 获取所有AI配置
        ais = self.config_manager.get_ais()
        
        # 创建列表框显示AI
        ai_listbox = tk.Listbox(ai_selector_window, font=("Arial", 10))
        ai_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加AI到列表框
        ai_ids = []
        for ai_id, ai_config in ais.items():
            ai_ids.append(ai_id)
            display_text = f"{ai_config['name']} ({ai_config['model']})"
            ai_listbox.insert(tk.END, display_text)
            
            # 标记当前选中的AI
            if ai_id == self.api_manager.current_ai_id:
                ai_listbox.selection_set(tk.END)
                
        # 双击选择AI
        def select_ai(event):
            selection = ai_listbox.curselection()
            if selection:
                index = selection[0]
                selected_ai_id = ai_ids[index]
                
                # 切换AI
                if self.api_manager.switch_ai(selected_ai_id):
                    self.update_title()
                    ai_selector_window.destroy()
                else:
                    messagebox.showerror("错误", "切换AI失败")
                    
        ai_listbox.bind("<Double-Button-1>", select_ai)
        
        # 选择按钮
        def confirm_select():
            selection = ai_listbox.curselection()
            if selection:
                index = selection[0]
                selected_ai_id = ai_ids[index]
                
                # 切换AI
                if self.api_manager.switch_ai(selected_ai_id):
                    self.update_title()
                    ai_selector_window.destroy()
                else:
                    messagebox.showerror("错误", "切换AI失败")
            else:
                messagebox.showwarning("警告", "请先选择一个AI")
                
        select_btn = tk.Button(ai_selector_window, text="选择", command=confirm_select)
        select_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 管理按钮
        manage_btn = tk.Button(ai_selector_window, text="管理AI", command=self.open_ai_manager)
        manage_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 关闭按钮
        close_btn = tk.Button(ai_selector_window, text="关闭", command=ai_selector_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
    def open_ai_manager(self):
        """打开AI管理窗口"""
        ai_manager_window = tk.Toplevel(self.root)
        ai_manager_window.title("管理AI")
        ai_manager_window.geometry("500x400")
        ai_manager_window.transient(self.root)
        ai_manager_window.grab_set()
        
        # 设置窗口图标
        self.set_window_icon(ai_manager_window)
        
        # 创建notebook用于分页
        notebook = ttk.Notebook(ai_manager_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # AI列表页面
        ai_list_frame = ttk.Frame(notebook)
        notebook.add(ai_list_frame, text="AI列表")
        
        # 创建列表框显示AI
        ai_listbox = tk.Listbox(ai_list_frame, font=("Arial", 10))
        ai_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 获取所有AI配置
        ais = self.config_manager.get_ais()
        ai_ids = []
        
        # 添加AI到列表框
        for ai_id, ai_config in ais.items():
            ai_ids.append(ai_id)
            display_text = f"{ai_config['name']} ({ai_config['model']})"
            ai_listbox.insert(tk.END, display_text)
            
        # 添加AI按钮
        def add_ai():
            self.open_ai_editor(ai_manager_window)
            
        add_btn = tk.Button(ai_list_frame, text="添加AI", command=add_ai)
        add_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 编辑AI按钮
        def edit_ai():
            selection = ai_listbox.curselection()
            if selection:
                index = selection[0]
                ai_id = ai_ids[index]
                self.open_ai_editor(ai_manager_window, ai_id)
            else:
                messagebox.showwarning("警告", "请先选择一个AI")
                
        edit_btn = tk.Button(ai_list_frame, text="编辑", command=edit_ai)
        edit_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 删除AI按钮
        def delete_ai():
            selection = ai_listbox.curselection()
            if selection:
                index = selection[0]
                ai_id = ai_ids[index]
                
                # 确认删除
                if messagebox.askyesno("确认删除", "确定要删除这个AI配置吗？"):
                    self.config_manager.delete_ai(ai_id)
                    # 如果删除后没有AI了，添加一个默认AI
                    if len(self.config_manager.get_ais()) == 0:
                        self.config_manager.add_ai("默认AI", "", "https://api.openai.com/v1", "gpt-3.5-turbo")
                    
                    # 刷新列表
                    ai_listbox.delete(0, tk.END)
                    ais = self.config_manager.get_ais()
                    ai_ids.clear()
                    for ai_id, ai_config in ais.items():
                        ai_ids.append(ai_id)
                        display_text = f"{ai_config['name']} ({ai_config['model']})"
                        ai_listbox.insert(tk.END, display_text)
                    
                    # 更新API管理器和标题
                    self.api_manager.update_config(self.config_manager)
                    self.update_title()
            else:
                messagebox.showwarning("警告", "请先选择一个AI")
                
        delete_btn = tk.Button(ai_list_frame, text="删除", command=delete_ai)
        delete_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 设为默认按钮
        def set_default():
            selection = ai_listbox.curselection()
            if selection:
                index = selection[0]
                ai_id = ai_ids[index]
                self.config_manager.set_default_ai(ai_id)
                messagebox.showinfo("成功", "已设为默认AI")
            else:
                messagebox.showwarning("警告", "请先选择一个AI")
                
        default_btn = tk.Button(ai_list_frame, text="设为默认", command=set_default)
        default_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 关闭按钮
        close_btn = tk.Button(ai_list_frame, text="关闭", command=ai_manager_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
    def open_ai_editor(self, parent_window, ai_id=None):
        """打开AI编辑器"""
        editor_window = tk.Toplevel(parent_window)
        editor_window.title("编辑AI" if ai_id else "添加AI")
        editor_window.geometry("400x300")
        editor_window.transient(parent_window)
        editor_window.grab_set()
        
        # 设置窗口图标
        self.set_window_icon(editor_window)
        
        # 获取AI配置（如果是编辑模式）
        ai_config = {}
        if ai_id:
            ai_config = self.config_manager.get_ai(ai_id) or {}
            
        # 名称设置
        tk.Label(editor_window, text="名称:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        name_var = tk.StringVar(value=ai_config.get("name", ""))
        name_entry = tk.Entry(editor_window, textvariable=name_var, width=50)
        name_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # API密钥设置
        tk.Label(editor_window, text="API密钥:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        api_key_var = tk.StringVar(value=ai_config.get("api_key", ""))
        api_key_entry = tk.Entry(editor_window, textvariable=api_key_var, width=50, show="*")
        api_key_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # API基础URL设置
        tk.Label(editor_window, text="API基础URL:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        base_url_var = tk.StringVar(value=ai_config.get("base_url", "https://api.openai.com/v1"))
        base_url_entry = tk.Entry(editor_window, textvariable=base_url_var, width=50)
        base_url_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # 模型选择
        tk.Label(editor_window, text="模型:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        model_var = tk.StringVar(value=ai_config.get("model", "gpt-3.5-turbo"))
        model_entry = tk.Entry(editor_window, textvariable=model_var, width=50)
        model_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # 保存按钮
        def save_ai():
            name = name_var.get().strip()
            api_key = api_key_var.get().strip()
            base_url = base_url_var.get().strip()
            model = model_var.get().strip()
            
            if not name:
                messagebox.showerror("错误", "请输入AI名称")
                return
                
            if not api_key:
                messagebox.showerror("错误", "请输入API密钥")
                return
                
            if not base_url:
                messagebox.showerror("错误", "请输入API基础URL")
                return
                
            if not model:
                messagebox.showerror("错误", "请输入模型名称")
                return
                
            try:
                if ai_id:
                    # 更新现有AI
                    self.config_manager.update_ai(ai_id, name, api_key, base_url, model)
                else:
                    # 添加新AI
                    self.config_manager.add_ai(name, api_key, base_url, model)
                    
                # 更新API管理器
                self.api_manager.update_config(self.config_manager)
                self.update_title()
                editor_window.destroy()
                messagebox.showinfo("成功", "AI配置已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
                
        save_btn = tk.Button(editor_window, text="保存", command=save_ai)
        save_btn.pack(pady=20)
        
    def open_settings(self):
        """打开设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x350")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置窗口图标
        self.set_window_icon(settings_window)
        
        # 开机自启动设置
        autostart_var = tk.BooleanVar(value=self.config_manager.get("autostart", False))
        autostart_check = tk.Checkbutton(settings_window, text="开机自启动", variable=autostart_var)
        autostart_check.pack(anchor=tk.W, padx=10, pady=10)
        
        # 保存按钮
        def save_settings():
            self.config_manager.set("autostart", autostart_var.get())
            
            # 更新开机自启动设置
            autostart_manager = AutoStartManager()
            if autostart_var.get():
                autostart_manager.enable_autostart()
            else:
                autostart_manager.disable_autostart()
                
            settings_window.destroy()
            
        save_btn = tk.Button(settings_window, text="保存", command=save_settings)
        save_btn.pack(pady=20)
        
    def new_chat(self):
        """新建聊天会话"""
        # 清空当前显示
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # 只有在需要时才创建新会话（当用户发送第一条消息时）
        # 这里不立即创建新会话，避免创建空记录
        self.history_manager.current_session_id = None
        
    def open_history(self):
        """打开历史记录窗口"""
        history_window = tk.Toplevel(self.root)
        history_window.title("历史记录")
        history_window.geometry("500x400")
        history_window.transient(self.root)
        history_window.grab_set()
        
        # 设置窗口图标
        self.set_window_icon(history_window)
        
        # 创建列表框显示历史会话
        history_listbox = tk.Listbox(history_window, font=("Arial", 10))
        history_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 获取所有会话
        sessions = self.history_manager.get_all_sessions()
        
        # 添加会话到列表框
        for session in sessions:
            display_text = f"{session['timestamp'][:19]} - {session['title']}"
            history_listbox.insert(tk.END, display_text)
            
        # 双击加载会话
        def load_session(event):
            selection = history_listbox.curselection()
            if selection:
                index = selection[0]
                session_id = sessions[index]["session_id"]
                
                # 加载会话历史
                messages = self.history_manager.load_session(session_id)
                
                # 清空当前显示
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete(1.0, tk.END)
                self.chat_display.config(state=tk.DISABLED)
                
                # 显示历史消息
                for message in messages:
                    sender = "你" if message["role"] == "user" else "AI"
                    self.display_message(sender, message["content"])
                    
                # 设置当前会话ID
                self.history_manager.current_session_id = session_id
                
                history_window.destroy()
                
        history_listbox.bind("<Double-Button-1>", load_session)
        
        # 删除按钮
        def delete_session():
            selection = history_listbox.curselection()
            if selection:
                index = selection[0]
                session_id = sessions[index]["session_id"]
                
                # 确认删除
                if messagebox.askyesno("确认删除", "确定要删除这个会话吗？"):
                    self.history_manager.delete_session(session_id)
                    history_listbox.delete(index)
                    sessions.pop(index)
                    
        delete_btn = tk.Button(history_window, text="删除", command=delete_session)
        delete_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 清除所有历史记录按钮
        def clear_all_history():
            # 确认删除
            if messagebox.askyesno("确认清除", "确定要删除所有历史记录吗？此操作不可恢复。"):
                self.history_manager.clear_all_history()
                history_listbox.delete(0, tk.END)
                sessions.clear()
                messagebox.showinfo("完成", "所有历史记录已清除")
                    
        clear_all_btn = tk.Button(history_window, text="清除所有历史记录", command=clear_all_history)
        clear_all_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 关闭按钮
        close_btn = tk.Button(history_window, text="关闭", command=history_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=10, pady=10)

def main():
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
import winreg
import sys
import os

class AutoStartManager:
    def __init__(self, app_name="AI助手"):
        self.app_name = app_name
        self.key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
    def get_executable_path(self):
        """获取当前程序的路径"""
        return sys.executable
        
    def enable_autostart(self):
        """启用开机自启动"""
        try:
            # 打开注册表项
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_SET_VALUE)
            
            # 获取程序路径
            exe_path = self.get_executable_path()
            
            # 设置开机启动项
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            
            return True
        except Exception as e:
            print(f"设置开机自启动失败: {e}")
            return False
            
    def disable_autostart(self):
        """禁用开机自启动"""
        try:
            # 打开注册表项
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_SET_VALUE)
            
            # 删除启动项
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
            
            return True
        except FileNotFoundError:
            # 如果键不存在，说明已经禁用了开机启动
            return True
        except Exception as e:
            print(f"禁用开机自启动失败: {e}")
            return False
            
    def is_autostart_enabled(self):
        """检查是否已启用开机自启动"""
        try:
            # 打开注册表项
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_READ)
            
            # 尝试读取值
            value, _ = winreg.QueryValueEx(key, self.app_name)
            winreg.CloseKey(key)
            
            # 检查路径是否匹配
            exe_path = self.get_executable_path()
            return value == exe_path
        except FileNotFoundError:
            # 键不存在
            return False
        except Exception as e:
            print(f"检查开机自启动状态失败: {e}")
            return False
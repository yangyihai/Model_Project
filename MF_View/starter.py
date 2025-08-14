"""
魔方复原助手 - 启动器

直接运行此脚本可立即启动魔方复原GUI程序，无需选择。
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import importlib.util

def add_path_to_sys_path(path):
    """将路径添加到系统路径中，便于模块导入"""
    if path not in sys.path:
        sys.path.insert(0, path)

def start_magic_cube_gui():
    """直接启动魔方复原GUI程序"""
    try:
        # 确保当前目录在Python路径中
        current_dir = os.path.dirname(os.path.abspath(__file__))
        add_path_to_sys_path(current_dir)
        
        # 确保src目录也在Python路径中
        src_dir = os.path.join(current_dir, 'src')
        add_path_to_sys_path(src_dir)
        
        # 导入MF_GUI模块
        module_path = os.path.join(current_dir, 'MF_GUI.py')
        spec = importlib.util.spec_from_file_location("MF_GUI", module_path)
        mf_gui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mf_gui)
        
        # 创建主窗口并启动程序
        root = tk.Tk()
        app = mf_gui.MagicCubeGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        
        # 设置窗口图标
        try:
            root.iconphoto(True, tk.PhotoImage(file=os.path.join(current_dir, "index.png")))
        except Exception:
            pass
        
        # 开始主循环
        root.mainloop()
        
    except ImportError as e:
        messagebox.showerror("错误", f"未能找到或加载MF_GUI.py模块: {e}\n请确保该文件位于当前目录中。")
    except Exception as e:
        messagebox.showerror("错误", f"启动魔方复原助手失败: {e}")

if __name__ == "__main__":
    start_magic_cube_gui()

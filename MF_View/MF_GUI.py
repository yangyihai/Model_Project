"""
魔方复原助手 - 基于QBR的视觉识别

此程序作为QBR魔方还原大模型的界面，提供以下功能：
1. 使用摄像头实时识别魔方状态
2. 提供魔方各面的颜色识别
3. 生成详细的魔方复原步骤
4. 提供图形界面指导用户完成魔方复原
"""

import os
import sys
import time
import threading
import numpy as np
import cv2
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from datetime import datetime

# 确保src目录在导入路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 导入qbr模块
try:
    from src.qbr import Qbr
    from src.video import Webcam
    from src import colordetection
    from src import config
    from src import constants
    import kociemba
    import i18n
    QBR_AVAILABLE = True
except ImportError as e:
    QBR_AVAILABLE = False
    print(f"警告: 无法导入QBR模块 - {e}")

class MagicCubeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("魔方复原助手")
        self.root.geometry("1200x800")
        
        # 初始化QBR相关资源
        if QBR_AVAILABLE:
            # 设置QBR的i18n
            locale = config.config.get_setting('locale')
            if not locale:
                config.config.set_setting('locale', 'zh')
                locale = config.config.get_setting('locale')
            
            i18n.load_path.append(os.path.join(src_dir, 'translations'))
            i18n.set('filename_format', '{locale}.{format}')
            i18n.set('file_format', 'json')
            i18n.set('locale', locale)
            i18n.set('fallback', 'en')
        
        # 创建基本界面
        self.create_widgets()
        
        # 标记程序状态
        self.is_running = False
        
        # 魔方状态
        self.cube_state = None
        self.solution = None
        self.solution_steps = []
        
        # 视频相关
        self.video_source = 0  # 默认为第一个摄像头
        self.video_capture = None
        self.webcam = None
        
        # 显示欢迎信息
        self.log_status("欢迎使用魔方复原助手")
        self.log_status("请选择要使用的解算器")
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧视频区域
        self.video_frame = ttk.LabelFrame(main_frame, text="摄像头视图")
        self.video_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        
        # 视频显示标签
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 右侧控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # 控制按钮
        if QBR_AVAILABLE:
            btn_qbr = ttk.Button(control_frame, text="使用QBR解魔方", 
                               command=self.launch_qbr_solver)
            btn_qbr.pack(fill=tk.X, pady=5)
            
            btn_qbr_embed = ttk.Button(control_frame, text="内嵌使用QBR解魔方", 
                                    command=self.launch_qbr_embedded)
            btn_qbr_embed.pack(fill=tk.X, pady=5)
            
            # 添加分割线
            separator = ttk.Separator(control_frame, orient="horizontal")
            separator.pack(fill=tk.X, pady=10)
        else:
            self.log_status("警告：QBR模块不可用，某些功能将受限")
        
        btn_exit = ttk.Button(control_frame, text="退出", command=self.on_close)
        btn_exit.pack(fill=tk.X, pady=5)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(main_frame, text="状态")
        status_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        # 状态文本显示
        self.status_text = tk.Text(status_frame, wrap=tk.WORD, height=20, width=40)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加状态文本的滚动条
        status_scroll = ttk.Scrollbar(self.status_text)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=status_scroll.set)
        status_scroll.config(command=self.status_text.yview)
        
        # 设置列权重，让视频区域占更多空间
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # 底部进度条
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, 
                                      length=100, variable=self.progress_var, 
                                      mode="determinate")
        self.progress.pack(fill=tk.X)
    
    def launch_qbr_solver(self):
        """启动QBR高级魔方解算器（独立窗口）"""
        if not QBR_AVAILABLE:
            self.log_status("QBR模块不可用，请确保安装了所有依赖")
            return
        
        self.log_status("正在启动QBR高级魔方解算器...")
        
        try:
            # 创建并运行QBR
            qbr = Qbr(normalize=True)
            
            # 提示用户
            self.log_status("QBR解算器已启动，请在新窗口中操作")
            self.log_status("提示：按'c'进入颜色校准模式")
            self.log_status("在校准模式中，依次展示每个面的中心块，按空格键校准")
            self.log_status("完成校准后，按'c'退出校准模式")
            self.log_status("然后依次拍摄魔方六个面，按空格键确认")
            
            # 启动QBR（这会阻塞直到QBR窗口关闭）
            cube_state = qbr.run()
            
            # QBR完成后处理结果
            if isinstance(cube_state, str) and len(cube_state) == 54:
                self.log_status("魔方状态已识别：" + cube_state)
                
                # 显示解法
                try:
                    solution = kociemba.solve(cube_state)
                    self.log_status("解法已生成：" + solution)
                    self.explain_solution(solution)
                except Exception as e:
                    self.log_status(f"生成解法时出错: {e}")
            elif isinstance(cube_state, int) and cube_state > 0:
                if cube_state == constants.E_INCORRECTLY_SCANNED:
                    self.log_status("错误：魔方未正确扫描")
                elif cube_state == constants.E_ALREADY_SOLVED:
                    self.log_status("提示：魔方已经是复原状态")
                else:
                    self.log_status(f"QBR返回未知状态码: {cube_state}")
            
        except Exception as e:
            self.log_status(f"启动QBR解算器失败: {e}")
    
    def launch_qbr_embedded(self):
        """在当前界面中嵌入QBR功能"""
        if not QBR_AVAILABLE:
            self.log_status("QBR模块不可用，请确保安装了所有依赖")
            return
        
        self.log_status("正在初始化内嵌QBR功能...")
        
        # 清理之前的视频对象（如果有的话）
        if self.is_running and self.video_capture:
            self.is_running = False
            time.sleep(0.5)  # 给线程一些时间停止
            if hasattr(self.video_capture, 'release'):
                self.video_capture.release()
        
        try:
            # 创建QBR的Webcam对象
            self.webcam = Webcam()
            
            # 获取其摄像头
            self.video_capture = self.webcam.cam
            
            if not self.video_capture.isOpened():
                raise ValueError("无法打开摄像头")
            
            # 设置标志
            self.is_running = True
            
            # 创建视频线程
            video_thread = threading.Thread(target=self.update_qbr_frame)
            video_thread.daemon = True
            video_thread.start()
            
            # 为用户提供使用说明
            self.log_status("QBR功能已启动")
            self.log_status("按'c'键进入颜色校准模式")
            self.log_status("在校准模式中，依次展示每个面的中心块，按空格键校准")
            self.log_status("完成校准后，按'c'键退出校准模式")
            self.log_status("然后进行魔方面的录入:")
            self.log_status("1. 按对应的按键(U/R/F/D/L/B)选择要录入的面")
            self.log_status("2. 按空格键拍摄并记录当前选择的面")
            self.log_status("3. 重复以上步骤直到录入所有六个面")
            self.log_status("")
            self.log_status("面的标准定义（仅供参考，您可以根据自己的习惯选择）:")
            self.log_status("U (Up/上面) - 通常为白色")
            self.log_status("R (Right/右面) - 通常为红色")
            self.log_status("F (Front/前面) - 通常为绿色")
            self.log_status("D (Down/下面) - 通常为黄色")
            self.log_status("L (Left/左面) - 通常为橙色")
            self.log_status("B (Back/后面) - 通常为蓝色")
            self.log_status("")
            self.log_status("完成所有面的拍摄后，程序会自动生成解法")
            
        except Exception as e:
            self.log_status(f"初始化QBR功能失败: {e}")
    
    def update_qbr_frame(self):
        """更新QBR视频帧"""
        try:
            while self.is_running:
                ret, frame = self.video_capture.read()
                if not ret:
                    continue
                
                # 使用QBR的视频处理功能处理帧
                grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurredFrame = cv2.blur(grayFrame, (3, 3))
                cannyFrame = cv2.Canny(blurredFrame, 30, 60, 3)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
                dilatedFrame = cv2.dilate(cannyFrame, kernel)
                
                # 寻找魔方轮廓
                contours = self.webcam.find_contours(dilatedFrame)
                if len(contours) == 9:
                    self.webcam.draw_contours(contours)
                    self.webcam.update_preview_state(contours)
                
                # 将原始功能的一部分绘制到帧上
                self.webcam.frame = frame  # 设置当前帧
                if hasattr(self.webcam, 'calibrate_mode') and self.webcam.calibrate_mode:
                    self.webcam.draw_current_color_to_calibrate()
                    self.webcam.draw_calibrated_colors()
                else:
                    self.webcam.draw_current_language()
                    self.webcam.draw_preview_stickers()
                    self.webcam.draw_snapshot_stickers()
                    self.webcam.draw_scanned_sides()
                    self.webcam.draw_2d_cube_state()
                
                # 检查按键
                key = cv2.waitKey(10) & 0xff
                if key == 27:  # ESC键
                    self.is_running = False
                    break
                
                if key == ord('c'):  # 切换校准模式
                    if hasattr(self.webcam, 'calibrate_mode'):
                        if self.webcam.calibrate_mode:
                            self.webcam.reset_calibrate_mode()
                        self.webcam.calibrate_mode = not self.webcam.calibrate_mode
                
                # 处理面选择按键
                if key == ord('U') or key == ord('u'):
                    self.webcam.current_selected_face = 'U'
                    self.log_status(f"已选择 U (Up/上面)")
                elif key == ord('R') or key == ord('r'):
                    self.webcam.current_selected_face = 'R'
                    self.log_status(f"已选择 R (Right/右面)")
                elif key == ord('F') or key == ord('f'):
                    self.webcam.current_selected_face = 'F'
                    self.log_status(f"已选择 F (Front/前面)")
                elif key == ord('D') or key == ord('d'):
                    self.webcam.current_selected_face = 'D'
                    self.log_status(f"已选择 D (Down/下面)")
                elif key == ord('L') or key == ord('l'):
                    self.webcam.current_selected_face = 'L'
                    self.log_status(f"已选择 L (Left/左面)")
                elif key == ord('B') or key == ord('b'):
                    self.webcam.current_selected_face = 'B'
                    self.log_status(f"已选择 B (Back/后面)")
                
                if key == 32:  # 空格键
                    if hasattr(self.webcam, 'calibrate_mode') and self.webcam.calibrate_mode:
                        # 处理校准逻辑
                        if not self.webcam.done_calibrating:
                            current_color = self.webcam.colors_to_calibrate[self.webcam.current_color_to_calibrate_index]
                            contours = self.webcam.find_contours(dilatedFrame)
                            if len(contours) == 9:
                                (x, y, w, h) = contours[4]
                                roi = frame[y+7:y+h-7, x+14:x+w-14]
                                avg_bgr = colordetection.get_dominant_color(roi)
                                self.webcam.calibrated_colors[current_color] = avg_bgr
                                self.webcam.current_color_to_calibrate_index += 1
                                self.webcam.done_calibrating = self.webcam.current_color_to_calibrate_index == len(self.webcam.colors_to_calibrate)
                                if self.webcam.done_calibrating:
                                    colordetection.set_cube_color_pallete(self.webcam.calibrated_colors)
                                    config.config.set_setting('cube_palette', colordetection.cube_color_palette)
                                    
                                # 更新UI
                                self.log_status(f"已校准颜色: {current_color}")
                    else:
                        # 正常模式下拍摄
                        if hasattr(self.webcam, 'current_selected_face') and self.webcam.current_selected_face:
                            # 用户已经选择了面
                            face = self.webcam.current_selected_face
                            self.webcam.update_snapshot_state(face)
                            self.log_status(f"已拍摄面: {face}")
                        else:
                            # 没有选择面，提示用户
                            self.log_status("请先按 U, R, F, D, L, B 键选择要录入的面")
                        
                        # 检查是否完成了所有6个面
                        if len(self.webcam.result_state.keys()) == 6:
                            # 检查是否已经解决
                            if self.webcam.state_already_solved():
                                self.log_status("魔方已经是复原状态！")
                            else:
                                # 获取魔方状态
                                cube_state = self.webcam.get_result_notation()
                                self.cube_state = cube_state
                                
                                # 尝试求解
                                try:
                                    solution = kociemba.solve(cube_state)
                                    self.solution = solution
                                    self.solution_steps = solution.split()
                                    
                                    self.log_status(f"魔方状态: {cube_state}")
                                    self.log_status(f"解法已生成: {solution}")
                                    
                                    # 显示解法解释
                                    self.explain_solution(solution)
                                except Exception as e:
                                    self.log_status(f"生成解法失败: {e}")
                
                # 将OpenCV图像转换为PIL格式并在Tkinter上显示
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                
                # 调整图像大小以适应界面
                pil_img = pil_img.resize((640, 480), Image.LANCZOS)
                
                img_tk = ImageTk.PhotoImage(image=pil_img)
                
                # 更新GUI（必须在主线程中进行）
                self.root.after(0, lambda: self.update_video_label(img_tk))
                
                time.sleep(0.03)  # 控制刷新率
                
        except Exception as e:
            self.log_status(f"视频处理出错: {e}")
            self.is_running = False
    
    def update_video_label(self, img_tk):
        """更新视频标签（在主线程中调用）"""
        self.video_label.configure(image=img_tk)
        self.video_label.image = img_tk  # 保持引用，防止被垃圾回收
    
    def explain_solution(self, solution):
        """解释魔方解法步骤"""
        steps = solution.split()
        self.solution_steps = steps
        
        self.log_status(f"总步骤数: {len(steps)}")
        self.log_status("步骤解释:")
        
        for i, step in enumerate(steps):
            explanation = self.get_step_explanation(step)
            self.log_status(f"{i+1}. {step} - {explanation}")
    
    def get_step_explanation(self, step):
        """获取步骤的中文解释"""
        step_explanations = {
            "R": "右面顺时针90度",
            "R'": "右面逆时针90度",
            "R2": "右面180度",
            "L": "左面顺时针90度",
            "L'": "左面逆时针90度",
            "L2": "左面180度",
            "F": "前面顺时针90度",
            "F'": "前面逆时针90度",
            "F2": "前面180度",
            "B": "后面顺时针90度",
            "B'": "后面逆时针90度",
            "B2": "后面180度",
            "U": "上面顺时针90度",
            "U'": "上面逆时针90度",
            "U2": "上面180度",
            "D": "下面顺时针90度",
            "D'": "下面逆时针90度",
            "D2": "下面180度"
        }
        
        return step_explanations.get(step, f"未知步骤: {step}")
    
    def log_status(self, message):
        """向状态文本框添加消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.root.after(0, lambda: self._log_status_main_thread(f"[{timestamp}] {message}"))
    
    def _log_status_main_thread(self, message):
        """在主线程中更新状态文本框（避免线程冲突）"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
    
    def on_close(self):
        """窗口关闭时的清理工作"""
        self.is_running = False
        
        # 释放视频资源
        if hasattr(self, 'video_capture') and self.video_capture is not None:
            self.video_capture.release()
        
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MagicCubeGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
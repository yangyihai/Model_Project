"""
魔方复原助手项目说明

此项目是一个基于OpenCV的魔方复原助手，能够通过摄像头识别魔方各面颜色，并提供详细的复原步骤指导。
"""

# 项目需要的依赖包
requirements = [
    'numpy==1.22.4', # 使用兼容版本，避免与scipy的版本冲突
    'opencv-python>=4.5.1',
    'scipy>=1.6.0',
    'Pillow>=8.1.0',
    'kociemba>=1.2'
]

# 打印依赖列表
print("魔方复原助手依赖列表:")
for req in requirements:
    print(f"- {req}")

print("\n使用方法:")
print("1. 安装依赖: pip install -r requirements.txt")
print("2. 运行程序: python starter.py")
print("3. 按照界面提示依次展示魔方的六个面")
print("4. 获取并按照步骤指引完成魔方复原")

# 将依赖写入文件
with open('requirements.txt', 'w') as f:
    for req in requirements:
        f.write(f"{req}\n")
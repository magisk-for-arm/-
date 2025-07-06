#!/usr/bin/env python3
import sys
import os
import shutil
import chardet
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget, QProgressBar, QFileDialog,
                             QMessageBox, QAction, QMenuBar, QStatusBar, QCheckBox, QComboBox,
                             QGroupBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QPalette, QColor, QDragEnterEvent, QDropEvent

class EncodingConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("高级编码转换工具")
        self.setGeometry(300, 300, 800, 600)
        
        # 深色模式标志
        self.dark_mode = False
        
        # 输出目录设置
        self.output_dir = ""
        self.use_custom_output = False
        
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        open_action = QAction("添加文件(&A)...", self)
        open_action.triggered.connect(self.add_files)
        file_menu.addAction(open_action)
        
        folder_action = QAction("添加文件夹(&D)...", self)
        folder_action.triggered.connect(self.add_folder)
        file_menu.addAction(folder_action)
        
        file_menu.addSeparator()
        
        output_action = QAction("设置输出目录(&O)...", self)
        output_action.triggered.connect(self.set_output_dir)
        file_menu.addAction(output_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 主题菜单
        theme_menu = menubar.addMenu("主题(&T)")
        light_action = QAction("浅色模式", self)
        light_action.triggered.connect(lambda: self.set_theme(False))
        theme_menu.addAction(light_action)
        
        dark_action = QAction("深色模式", self)
        dark_action.triggered.connect(lambda: self.set_theme(True))
        theme_menu.addAction(dark_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 创建主界面
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 文件列表
        file_group = QGroupBox("文件列表 (拖放文件或文件夹到此处)")
        file_group_layout = QVBoxLayout(file_group)
        self.file_list = QListWidget()
        self.file_list.setAcceptDrops(False)  # 列表本身不接受拖放，由窗口处理
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        file_group_layout.addWidget(self.file_list)
        layout.addWidget(file_group)
        
        # 设置拖放支持
        self.setAcceptDrops(True)
        
        # 转换选项区域
        options_group = QGroupBox("转换选项")
        options_layout = QVBoxLayout(options_group)
        
        # 转换方向选择
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("转换方向:"))
        
        self.conversion_direction = QButtonGroup(self)
        self.to_utf16_radio = QRadioButton("UTF-8 → UTF-16LE")
        self.to_utf16_radio.setChecked(True)
        self.conversion_direction.addButton(self.to_utf16_radio)
        direction_layout.addWidget(self.to_utf16_radio)
        
        self.to_utf8_radio = QRadioButton("UTF-16LE → UTF-8")
        self.conversion_direction.addButton(self.to_utf8_radio)
        direction_layout.addWidget(self.to_utf8_radio)
        
        options_layout.addLayout(direction_layout)
        
        # BOM选项
        self.bom_check = QCheckBox("添加字节顺序标记 (BOM)")
        self.bom_check.setChecked(True)
        options_layout.addWidget(self.bom_check)
        
        # 自动检测选项
        self.auto_detect_check = QCheckBox("自动检测源文件编码")
        self.auto_detect_check.setChecked(True)
        self.auto_detect_check.stateChanged.connect(self.toggle_auto_detect)
        options_layout.addWidget(self.auto_detect_check)
        
        # 手动选择源编码
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("源文件编码:"))
        
        self.source_encoding_combo = QComboBox()
        self.source_encoding_combo.addItems(["UTF-8", "UTF-16LE", "UTF-16BE", "ISO-8859-1", "GBK", "BIG5"])
        self.source_encoding_combo.setEnabled(False)
        source_layout.addWidget(self.source_encoding_combo)
        
        options_layout.addLayout(source_layout)
        
        # 输出选项
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出设置:"))
        
        self.overwrite_check = QCheckBox("覆盖原始文件")
        self.overwrite_check.setChecked(True)
        self.overwrite_check.stateChanged.connect(self.toggle_overwrite)
        output_layout.addWidget(self.overwrite_check)
        
        self.custom_output_check = QCheckBox("使用自定义输出目录")
        self.custom_output_check.stateChanged.connect(self.toggle_output_option)
        output_layout.addWidget(self.custom_output_check)
        
        options_layout.addLayout(output_layout)
        
        # 输出目录显示
        self.output_label = QLabel("输出目录: 未设置")
        options_layout.addWidget(self.output_label)
        
        # 备份选项
        self.backup_check = QCheckBox("创建备份文件 (.bak)")
        options_layout.addWidget(self.backup_check)
        
        layout.addWidget(options_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加文件")
        self.add_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(self.add_btn)
        
        self.add_folder_btn = QPushButton("添加文件夹")
        self.add_folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.add_folder_btn)
        
        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.clear_btn)
        
        self.remove_btn = QPushButton("移除选中")
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(self.remove_btn)
        
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.clicked.connect(self.start_conversion)
        btn_layout.addWidget(self.convert_btn)
        layout.addLayout(btn_layout)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 初始应用浅色主题
        self.set_theme(False)
    
    def toggle_auto_detect(self, state):
        auto_detect = (state == Qt.Checked)
        self.source_encoding_combo.setEnabled(not auto_detect)
    
    def toggle_overwrite(self, state):
        overwrite = (state == Qt.Checked)
        self.custom_output_check.setEnabled(not overwrite)
        if overwrite:
            self.custom_output_check.setChecked(False)
            self.use_custom_output = False
    
    def toggle_output_option(self, state):
        self.use_custom_output = (state == Qt.Checked)
        if self.use_custom_output and not self.output_dir:
            self.set_output_dir()
    
    def set_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir = dir_path
            self.output_label.setText(f"输出目录: {dir_path}")
            self.custom_output_check.setChecked(True)
            self.use_custom_output = True
    
    def set_theme(self, dark):
        self.dark_mode = dark
        
        if dark:
            # 深色模式样式
            self.setStyleSheet("""
                QMainWindow, QWidget, QGroupBox {
                    background-color: #2D2D2D;
                    color: #F0F0F0;
                    font-family: "Noto Sans", sans-serif;
                }
                QGroupBox {
                    border: 1px solid #444;
                    border-radius: 5px;
                    margin-top: 1ex;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 5px;
                }
                QPushButton {
                    background-color: #3a3a3a;
                    color: #F0F0F0;
                    border: 1px solid #5a5a5a;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QPushButton:pressed {
                    background-color: #2a2a2a;
                }
                QListWidget {
                    background-color: #252525;
                    color: #F0F0F0;
                    border: 1px solid #444;
                }
                QProgressBar {
                    border: 1px solid #444;
                    border-radius: 4px;
                    text-align: center;
                    color: #000;
                }
                QProgressBar::chunk {
                    background-color: #3daee9;
                    width: 10px;
                }
                QLabel, QRadioButton, QCheckBox {
                    color: #F0F0F0;
                }
                QComboBox {
                    background-color: #252525;
                    color: #F0F0F0;
                    border: 1px solid #444;
                }
                QMenuBar {
                    background-color: #2D2D2D;
                    color: #F0F0F0;
                }
                QMenuBar::item:selected {
                    background-color: #3a3a3a;
                }
                QMenu {
                    background-color: #3a3a3a;
                    color: #F0F0F0;
                    border: 1px solid #555;
                }
                QMenu::item:selected {
                    background-color: #4a4a4a;
                }
            """)
        else:
            # 浅色模式样式
            self.setStyleSheet("""
                QMainWindow, QWidget, QGroupBox {
                    background-color: #f0f0f0;
                    color: #000000;
                    font-family: "Noto Sans", sans-serif;
                }
                QGroupBox {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    margin-top: 1ex;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 5px;
                }
                QPushButton {
                    background-color: #3daee9;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1d99e3;
                }
                QPushButton:pressed {
                    background-color: #0c7ec7;
                }
                QListWidget {
                    background-color: white;
                    color: #000000;
                    border: 1px solid #ccc;
                }
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #3daee9;
                    width: 10px;
                }
                QLabel, QRadioButton, QCheckBox {
                    color: #000000;
                }
                QComboBox {
                    background-color: white;
                    color: #000000;
                    border: 1px solid #ccc;
                }
                QMenuBar {
                    background-color: #f0f0f0;
                }
            """)
    
    # 拖放支持方法
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_count = 0
        
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                self.file_list.addItem(path)
                file_count += 1
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        self.file_list.addItem(os.path.join(root, file))
                        file_count += 1
        
        if file_count > 0:
            self.status_bar.showMessage(f"添加了 {file_count} 个文件", 3000)
        event.acceptProposedAction()
    
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", "所有文件 (*);;文本文件 (*.txt *.csv *.json *.xml)")
        if files:
            self.file_list.addItems(files)
            self.status_bar.showMessage(f"添加了 {len(files)} 个文件", 3000)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            file_count = 0
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.file_list.addItem(file_path)
                    file_count += 1
            self.status_bar.showMessage(f"添加了 {file_count} 个文件", 3000)

    def clear_list(self):
        self.file_list.clear()
        self.status_bar.showMessage("文件列表已清空", 3000)
    
    def remove_selected(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            self.file_list.takeItem(self.file_list.row(item))
        
        self.status_bar.showMessage(f"移除了 {len(selected_items)} 个文件", 3000)

    def start_conversion(self):
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加要转换的文件")
            return

        # 检查输出目录
        if self.use_custom_output and not self.output_dir:
            QMessageBox.warning(self, "警告", "请先设置自定义输出目录")
            return

        # 如果使用自定义目录但目录不存在，则创建
        if self.use_custom_output and not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建输出目录: {str(e)}")
                return

        self.progress.setVisible(True)
        self.progress.setRange(0, self.file_list.count())
        self.progress.setValue(0)

        success_count = 0
        error_count = 0
        error_files = []

        # 获取转换方向
        to_utf16 = self.to_utf16_radio.isChecked()

        for i in range(self.file_list.count()):
            input_path = self.file_list.item(i).text()
            filename = os.path.basename(input_path)
            self.status_bar.showMessage(f"正在转换: {filename}")
            QApplication.processEvents()  # 更新UI

            try:
                # 确定输出路径，避免自定义目录下同名文件被覆盖
                if self.use_custom_output:
                    output_path = os.path.join(self.output_dir, filename)
                    base, ext = os.path.splitext(output_path)
                    count = 1
                    while os.path.exists(output_path) and os.path.abspath(output_path) != os.path.abspath(input_path):
                        output_path = f"{base}_{count}{ext}"
                        count += 1
                else:
                    output_path = input_path

                # 只在覆盖原始文件且未用自定义目录时备份，且不覆盖已有.bak
                if self.backup_check.isChecked() and not self.use_custom_output and self.overwrite_check.isChecked():
                    backup_path = input_path + ".bak"
                    if not os.path.exists(backup_path):
                        shutil.copy2(input_path, backup_path)

                # 自动检测编码
                if self.auto_detect_check.isChecked():
                    with open(input_path, 'rb') as f:
                        raw_data = f.read()
                        result = chardet.detect(raw_data)
                        source_encoding = result['encoding'] or 'utf-8'
                else:
                    # 手动选择编码
                    enc_map = {
                        "UTF-8": "utf-8",
                        "UTF-16LE": "utf-16-le",
                        "UTF-16BE": "utf-16-be",
                        "ISO-8859-1": "iso-8859-1",
                        "GBK": "gbk",
                        "BIG5": "big5"
                    }
                    source_encoding = enc_map.get(self.source_encoding_combo.currentText(), "utf-8")

                # 处理UTF-16的特殊情况
                if source_encoding.lower() in ('utf-16le', 'utf-16be'):
                    source_encoding = source_encoding.lower()

                # 根据转换方向执行转换
                if to_utf16:  # 任意 → UTF-16LE
                    with open(input_path, 'r', encoding=source_encoding, errors='replace') as f:
                        content = f.read()
                    with open(output_path, 'w', encoding='utf-16-le') as f:
                        if self.bom_check.isChecked():
                            f.write('\ufeff')
                        f.write(content)
                else:  # 任意 → UTF-8
                    with open(input_path, 'r', encoding=source_encoding, errors='replace') as f:
                        content = f.read()
                    if self.bom_check.isChecked():
                        with open(output_path, 'wb') as f:
                            f.write(b'\xef\xbb\xbf')
                            f.write(content.encode('utf-8', errors='replace'))
                    else:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(content)

                # 如果另存为新文件，保留原始文件修改时间
                if self.use_custom_output:
                    shutil.copystat(input_path, output_path)

                success_count += 1
            except Exception as e:
                error_count += 1
                error_files.append(f"{filename}: {str(e)}")
                self.status_bar.showMessage(f"错误: {filename} - {str(e)}", 5000)
            finally:
                self.progress.setValue(i + 1)

        # 显示结果
        direction = "UTF-8 → UTF-16LE" if to_utf16 else "UTF-16LE → UTF-8"
        result_msg = f"转换完成! ({direction})\n成功: {success_count}, 失败: {error_count}"

        if error_count > 0:
            result_msg += "\n\n失败文件:\n" + "\n".join(error_files[:5])
            if error_count > 5:
                result_msg += f"\n...以及其他 {error_count-5} 个文件"

        self.status_bar.showMessage(result_msg.split('\n')[0], 10000)
        QMessageBox.information(self, "转换完成", result_msg, QMessageBox.Ok)
        self.progress.setVisible(False)
    
    def show_about(self):
        about_text = """
        <b>高级编码转换工具</b><br><br>
        版本: 2.0<br>
        作者: DeepSeek and arm<br><br>
        功能:<br>
        - 双向编码转换：UTF-8 ↔ UTF-16LE<br>
        - 支持文件/文件夹拖放导入<br>
        - 自动检测源文件编码<br>
        - 可选择添加BOM(字节顺序标记)<br>
        - 支持覆盖原始文件或另存为新文件<br>
        - 深色/浅色主题切换<br><br>
        <i>注意: 此工具主要适用于文本文件</i>
        """
        QMessageBox.about(self, "关于", about_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置应用样式为Fusion以匹配KDE风格
    app.setStyle("Fusion")
    converter = EncodingConverter()
    converter.show()
    sys.exit(app.exec_())
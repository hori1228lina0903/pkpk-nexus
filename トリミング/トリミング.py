import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import glob

class ImageCropper:
    def __init__(self, root):
        self.root = root
        self.root.title("画像トリミングツール - 一括処理対応")
        self.root.geometry("1100x700")
        
        # 変数の初期化
        self.image_path = None
        self.original_image = None
        self.display_image = None
        self.tk_image = None
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.crop_box = None
        self.cropped_image = None
        self.scale_ratio = 1.0
        
        # 一括処理用の変数
        self.batch_crop_box = None
        
        # UIの構築
        self.setup_ui()
    
    def setup_ui(self):
        main_panel = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ===== 左側：コントロールパネル =====
        control_frame = ttk.Frame(main_panel, width=300)
        main_panel.add(control_frame, weight=0)
        
        # ノートブック（タブ）
        notebook = ttk.Notebook(control_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # タブ1: 単一画像処理
        single_tab = ttk.Frame(notebook)
        notebook.add(single_tab, text="単一画像")
        self.setup_single_tab(single_tab)
        
        # タブ2: 一括処理
        batch_tab = ttk.Frame(notebook)
        notebook.add(batch_tab, text="一括処理")
        self.setup_batch_tab(batch_tab)
        
        # ===== 右側：画像表示エリア =====
        image_frame = ttk.LabelFrame(main_panel, text="画像表示")
        main_panel.add(image_frame, weight=1)
        
        # キャンバス
        canvas_container = ttk.Frame(image_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_container, bg='lightgray', highlightthickness=0)
        
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # マウスイベント
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # ステータスバー
        self.status_bar = ttk.Label(self.root, text="準備完了", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 数値入力の検証
        self.setup_validation()
    
    def setup_single_tab(self, parent):
        """単一画像処理タブ"""
        # ファイル操作
        file_frame = ttk.LabelFrame(parent, text="ファイル操作", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(file_frame, text="画像を開く", command=self.select_image).pack(fill=tk.X, pady=2)
        
        # 画像情報
        info_frame = ttk.LabelFrame(parent, text="画像情報", padding=5)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.info_text = tk.StringVar(value="画像が選択されていません")
        ttk.Label(info_frame, textvariable=self.info_text, wraplength=250).pack()
        
        # 追加：画像表示用ラベル
        self.preview_label = ttk.Label(info_frame)
        self.preview_label.pack(pady=5)
        
        # 座標入力
        coord_frame = ttk.LabelFrame(parent, text="座標・サイズ指定", padding=10)
        coord_frame.pack(fill=tk.X, padx=5, pady=5)
        
        inner_frame = ttk.Frame(coord_frame)
        inner_frame.pack(fill=tk.X)
        
        ttk.Label(inner_frame, text="開始 X:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.x_entry = ttk.Entry(inner_frame, width=15)
        self.x_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.x_entry.insert(0, "0")
        
        ttk.Label(inner_frame, text="開始 Y:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.y_entry = ttk.Entry(inner_frame, width=15)
        self.y_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.y_entry.insert(0, "0")
        
        ttk.Label(inner_frame, text="幅:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.width_entry = ttk.Entry(inner_frame, width=15)
        self.width_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.width_entry.insert(0, "100")
        
        ttk.Label(inner_frame, text="高さ:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.height_entry = ttk.Entry(inner_frame, width=15)
        self.height_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        self.height_entry.insert(0, "100")
        
        # プリセットボタン
        preset_frame = ttk.Frame(inner_frame)
        preset_frame.grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(preset_frame, text="45,332,990x315", command=self.apply_preset).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="20,140,1040x600", command=self.apply_preset2).pack(side=tk.LEFT, padx=2)
        
        # ボタンフレーム
        button_frame = ttk.Frame(inner_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="適用", command=self.apply_coordinates).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="クリア", command=self.clear_coordinates).pack(side=tk.LEFT, padx=5)
        
        # 選択情報
        selection_frame = ttk.LabelFrame(parent, text="選択情報", padding=5)
        selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.selection_text = tk.StringVar(value="選択範囲: なし")
        ttk.Label(selection_frame, textvariable=self.selection_text, wraplength=250).pack()
        
        # アクションボタン
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.btn_crop = ttk.Button(action_frame, text="トリミング実行", command=self.crop_image, state='disabled')
        self.btn_crop.pack(fill=tk.X, pady=2)
        
        self.btn_save = ttk.Button(action_frame, text="保存", command=self.save_image, state='disabled')
        self.btn_save.pack(fill=tk.X, pady=2)
        
        self.btn_reset = ttk.Button(action_frame, text="選択リセット", command=self.reset_selection, state='disabled')
        self.btn_reset.pack(fill=tk.X, pady=2)
    
    def setup_batch_tab(self, parent):
        """一括処理タブ"""
        desc_frame = ttk.Frame(parent)
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(desc_frame, text="複数の画像を同じ座標で一括トリミングします", wraplength=250).pack()
        
        input_frame = ttk.LabelFrame(parent, text="入力フォルダ", padding=5)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.input_path_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_path_var).pack(fill=tk.X, pady=2)
        ttk.Button(input_frame, text="参照...", command=self.select_input_folder).pack(pady=2)
        
        output_frame = ttk.LabelFrame(parent, text="出力フォルダ", padding=5)
        output_frame.pack(fill=tk.X, padx=5, pady=5)
        self.output_path_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_path_var).pack(fill=tk.X, pady=2)
        ttk.Button(output_frame, text="参照...", command=self.select_output_folder).pack(pady=2)
        
        coord_frame = ttk.LabelFrame(parent, text="トリミング座標", padding=10)
        coord_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # プリセットボタン
        preset_batch_frame = ttk.Frame(coord_frame)
        preset_batch_frame.pack(fill=tk.X, pady=5)
        ttk.Button(preset_batch_frame, text="プリセット1 (45,332,990x315)", 
                   command=self.apply_batch_preset).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(preset_batch_frame, text="プリセット2 (20,140,1040x600)", 
                   command=self.apply_batch_preset2).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Separator(coord_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        inner_frame = ttk.Frame(coord_frame)
        inner_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(inner_frame, text="X:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.batch_x_entry = ttk.Entry(inner_frame, width=15)
        self.batch_x_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.batch_x_entry.insert(0, "0")
        
        ttk.Label(inner_frame, text="Y:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.batch_y_entry = ttk.Entry(inner_frame, width=15)
        self.batch_y_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.batch_y_entry.insert(0, "0")
        
        ttk.Label(inner_frame, text="幅:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.batch_width_entry = ttk.Entry(inner_frame, width=15)
        self.batch_width_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.batch_width_entry.insert(0, "100")
        
        ttk.Label(inner_frame, text="高さ:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.batch_height_entry = ttk.Entry(inner_frame, width=15)
        self.batch_height_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        self.batch_height_entry.insert(0, "100")
        
        option_frame = ttk.LabelFrame(parent, text="オプション", padding=5)
        option_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.keep_original_name = tk.BooleanVar(value=True)
        ttk.Checkbutton(option_frame, text="元のファイル名を保持", variable=self.keep_original_name).pack(anchor=tk.W)
        
        self.create_subfolder = tk.BooleanVar(value=True)
        ttk.Checkbutton(option_frame, text="出力フォルダにサブフォルダを作成", variable=self.create_subfolder).pack(anchor=tk.W)
        
        format_frame = ttk.Frame(option_frame)
        format_frame.pack(fill=tk.X, pady=5)
        ttk.Label(format_frame, text="出力形式:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="JPEG")
        ttk.Combobox(format_frame, textvariable=self.format_var, values=["JPEG", "PNG", "BMP"], width=10).pack(side=tk.LEFT, padx=5)
        
        progress_frame = ttk.LabelFrame(parent, text="進捗", padding=5)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100).pack(fill=tk.X, pady=5)
        self.progress_label = ttk.Label(progress_frame, text="待機中")
        self.progress_label.pack()
        
        self.btn_batch = ttk.Button(parent, text="一括トリミング実行", command=self.batch_crop)
        self.btn_batch.pack(fill=tk.X, padx=20, pady=10)
    
    def apply_batch_preset(self):
        """一括処理タブにプリセット値を入力"""
        self.batch_x_entry.delete(0, tk.END)
        self.batch_x_entry.insert(0, "45")
        self.batch_y_entry.delete(0, tk.END)
        self.batch_y_entry.insert(0, "332")
        self.batch_width_entry.delete(0, tk.END)
        self.batch_width_entry.insert(0, "990")
        self.batch_height_entry.delete(0, tk.END)
        self.batch_height_entry.insert(0, "315")
        self.status_bar.config(text="一括処理用プリセット適用: X=45, Y=332, 990x315")
    
    def apply_batch_preset2(self):
        """一括処理タブにプリセット2の値を入力"""
        self.batch_x_entry.delete(0, tk.END)
        self.batch_x_entry.insert(0, "20")
        self.batch_y_entry.delete(0, tk.END)
        self.batch_y_entry.insert(0, "140")
        self.batch_width_entry.delete(0, tk.END)
        self.batch_width_entry.insert(0, "1040")
        self.batch_height_entry.delete(0, tk.END)
        self.batch_height_entry.insert(0, "600")
        self.status_bar.config(text="一括処理用プリセット2適用: X=20, Y=140, 1040x600")
    
    def setup_validation(self):
        def validate_number(value):
            if value == "":
                return True
            try:
                int(value)
                return True
            except ValueError:
                return False
        
        vcmd = (self.root.register(validate_number), '%P')
        for entry in [self.x_entry, self.y_entry, self.width_entry, self.height_entry,
                      self.batch_x_entry, self.batch_y_entry, 
                      self.batch_width_entry, self.batch_height_entry]:
            entry.configure(validate='key', validatecommand=vcmd)
    
    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="画像を選択",
            filetypes=[("画像ファイル", "*.jpg *.jpeg *.png *.bmp *.gif"), ("すべてのファイル", "*.*")]
        )
        if file_path:
            self.image_path = file_path
            self.load_image()
    
    def select_input_folder(self):
        folder = filedialog.askdirectory(title="入力フォルダを選択")
        if folder:
            self.input_path_var.set(folder)
    
    def select_output_folder(self):
        folder = filedialog.askdirectory(title="出力フォルダを選択")
        if folder:
            self.output_path_var.set(folder)
    
    def apply_preset(self):
        """プリセット値を入力"""
        if not self.original_image:
            messagebox.showwarning("警告", "先に画像を開いてください")
            return
        
        preset_x, preset_y, preset_w, preset_h = 45, 332, 990, 315
        
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, str(preset_x))
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, str(preset_y))
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(preset_w))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(preset_h))
        
        if self.scale_ratio:
            disp_x = int(preset_x / self.scale_ratio)
            disp_y = int(preset_y / self.scale_ratio)
            disp_w = int(preset_w / self.scale_ratio)
            disp_h = int(preset_h / self.scale_ratio)
            
            if self.rect:
                self.canvas.delete(self.rect)
            
            self.rect = self.canvas.create_rectangle(
                disp_x, disp_y, disp_x + disp_w, disp_y + disp_h,
                outline='red', width=2
            )
            self.crop_box = (disp_x, disp_y, disp_x + disp_w, disp_y + disp_h)
            self.selection_text.set(f"選択範囲: X={preset_x}, Y={preset_y}\nサイズ: {preset_w} x {preset_h}")
            self.status_bar.config(text=f"プリセット適用: ({preset_x}, {preset_y}) - {preset_w}x{preset_h}")
    
    def apply_preset2(self):
        """プリセット2の値を入力（20,140,1040x600）"""
        if not self.original_image:
            messagebox.showwarning("警告", "先に画像を開いてください")
            return
        
        preset_x, preset_y, preset_w, preset_h = 20, 140, 1040, 600
        
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, str(preset_x))
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, str(preset_y))
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(preset_w))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(preset_h))
        
        if self.scale_ratio:
            disp_x = int(preset_x / self.scale_ratio)
            disp_y = int(preset_y / self.scale_ratio)
            disp_w = int(preset_w / self.scale_ratio)
            disp_h = int(preset_h / self.scale_ratio)
            
            if self.rect:
                self.canvas.delete(self.rect)
            
            self.rect = self.canvas.create_rectangle(
                disp_x, disp_y, disp_x + disp_w, disp_y + disp_h,
                outline='red', width=2
            )
            self.crop_box = (disp_x, disp_y, disp_x + disp_w, disp_y + disp_h)
            self.selection_text.set(f"選択範囲: X={preset_x}, Y={preset_y}\nサイズ: {preset_w} x {preset_h}")
            self.status_bar.config(text=f"プリセット2適用: ({preset_x}, {preset_y}) - {preset_w}x{preset_h}")
    
    def load_image(self):
        try:
            self.original_image = Image.open(self.image_path)
            self.display_image = self.original_image.copy()
            self.display_image.thumbnail((800, 600), Image.Resampling.LANCZOS)
            self.scale_ratio = self.original_image.width / self.display_image.width
            self.tk_image = ImageTk.PhotoImage(self.display_image)
            
            self.canvas.config(scrollregion=(0, 0, self.display_image.width, self.display_image.height))
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor='nw', image=self.tk_image)
            
            self.btn_crop.config(state='normal')
            self.btn_reset.config(state='normal')
            
            file_name = os.path.basename(self.image_path)
            
            self.info_text.set(f"{file_name} ({self.original_image.width}x{self.original_image.height})")
            
            default_w = min(300, self.original_image.width)
            default_h = min(200, self.original_image.height)
            default_x = (self.original_image.width - default_w) // 2
            default_y = (self.original_image.height - default_h) // 2
            
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(default_x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(default_y))
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(default_w))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(default_h))
            
            self.status_bar.config(text=f"画像を読み込みました: {file_name}")
        except Exception as e:
            messagebox.showerror("エラー", f"画像の読み込みに失敗しました: {e}")
    
    def on_mouse_down(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
    
    def on_mouse_move(self, event):
        if self.rect:
            current_x = self.canvas.canvasx(event.x)
            current_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect, self.start_x, self.start_y, current_x, current_y)
    
    def on_mouse_up(self, event):
        if self.start_x and self.start_y:
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            left, upper = min(self.start_x, end_x), min(self.start_y, end_y)
            right, lower = max(self.start_x, end_x), max(self.start_y, end_y)
            
            if right - left < 5 or lower - upper < 5:
                self.canvas.delete(self.rect)
                self.rect = None
                return
            
            self.crop_box = (int(left), int(upper), int(right), int(lower))
            x = int(left * self.scale_ratio)
            y = int(upper * self.scale_ratio)
            w = int((right - left) * self.scale_ratio)
            h = int((lower - upper) * self.scale_ratio)
            
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(y))
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(w))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(h))
            self.selection_text.set(f"選択範囲: X={x}, Y={y}\nサイズ: {w} x {h}")
    
    def apply_coordinates(self):
        if not self.original_image:
            messagebox.showwarning("警告", "先に画像を開いてください")
            return
        try:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            w = int(self.width_entry.get())
            h = int(self.height_entry.get())
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                messagebox.showwarning("警告", "正の値を入力してください")
                return
            if x + w > self.original_image.width:
                messagebox.showwarning("警告", f"X座標+幅が画像サイズ({self.original_image.width})を超えています")
                return
            if y + h > self.original_image.height:
                messagebox.showwarning("警告", f"Y座標+高さが画像サイズ({self.original_image.height})を超えています")
                return
            
            dx, dy = int(x / self.scale_ratio), int(y / self.scale_ratio)
            dw, dh = int(w / self.scale_ratio), int(h / self.scale_ratio)
            
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(dx, dy, dx + dw, dy + dh, outline='red', width=2)
            self.crop_box = (dx, dy, dx + dw, dy + dh)
            self.selection_text.set(f"選択範囲: X={x}, Y={y}\nサイズ: {w} x {h}")
        except ValueError:
            messagebox.showwarning("警告", "全ての項目に数値を入力してください")
    
    def clear_coordinates(self):
        if self.original_image:
            default_w = min(300, self.original_image.width)
            default_h = min(200, self.original_image.height)
            default_x = (self.original_image.width - default_w) // 2
            default_y = (self.original_image.height - default_h) // 2
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(default_x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(default_y))
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(default_w))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(default_h))
        self.reset_selection()
    
    def reset_selection(self):
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None
            self.crop_box = None
            self.selection_text.set("選択範囲: なし")
    
    def crop_image(self):
        if not self.crop_box and self.original_image:
            try:
                x = int(self.x_entry.get())
                y = int(self.y_entry.get())
                w = int(self.width_entry.get())
                h = int(self.height_entry.get())
                self.cropped_image = self.original_image.crop((x, y, x + w, y + h))
                self.btn_save.config(state='normal')
                self.status_bar.config(text=f"トリミング完了: {w} x {h}")
                self.show_cropped_preview()
                return
            except:
                messagebox.showwarning("警告", "トリミングする領域を選択してください")
                return
        elif not self.crop_box:
            messagebox.showwarning("警告", "トリミングする領域を選択してください")
            return
        try:
            l = int(self.crop_box[0] * self.scale_ratio)
            u = int(self.crop_box[1] * self.scale_ratio)
            r = int(self.crop_box[2] * self.scale_ratio)
            d = int(self.crop_box[3] * self.scale_ratio)
            self.cropped_image = self.original_image.crop((l, u, r, d))
            self.btn_save.config(state='normal')
            self.status_bar.config(text=f"トリミング完了: {self.cropped_image.width} x {self.cropped_image.height}")
            self.show_cropped_preview()
        except Exception as e:
            messagebox.showerror("エラー", f"トリミングに失敗しました: {e}")
    
    def show_cropped_preview(self):
        if self.cropped_image:
            preview = tk.Toplevel(self.root)
            preview.title("プレビュー")
            preview_img = self.cropped_image.copy()
            preview_img.thumbnail((100, 70))
            preview_tk = ImageTk.PhotoImage(preview_img)
            label = ttk.Label(preview, image=preview_tk)
            label.image = preview_tk
            label.pack(padx=10, pady=10)
            ttk.Label(preview, text=f"サイズ: {self.cropped_image.width} x {self.cropped_image.height}").pack()
            ttk.Button(preview, text="閉じる", command=preview.destroy).pack(pady=10)
    
    def save_image(self):
        if not self.cropped_image:
            return
        save_path = filedialog.asksaveasfilename(
            title="保存先を選択",
            defaultextension=".jpg",
            filetypes=[("JPEG画像", "*.jpg"), ("PNG画像", "*.png"), ("BMP画像", "*.bmp")]
        )
        if save_path:
            try:
                self.cropped_image.save(save_path)
                messagebox.showinfo("完了", "画像を保存しました")
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました: {e}")
    
    def batch_crop(self):
        input_folder = self.input_path_var.get()
        output_folder = self.output_path_var.get()
        if not input_folder or not os.path.exists(input_folder):
            messagebox.showerror("エラー", "有効な入力フォルダを指定してください")
            return
        if not output_folder:
            messagebox.showerror("エラー", "出力フォルダを指定してください")
            return
        try:
            x = int(self.batch_x_entry.get())
            y = int(self.batch_y_entry.get())
            w = int(self.batch_width_entry.get())
            h = int(self.batch_height_entry.get())
            if w <= 0 or h <= 0:
                messagebox.showerror("エラー", "幅と高さは正の値を指定してください")
                return
        except ValueError:
            messagebox.showerror("エラー", "座標に有効な数値を入力してください")
            return
        
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']:
            image_files.extend(glob.glob(os.path.join(input_folder, ext)))
            image_files.extend(glob.glob(os.path.join(input_folder, ext.upper())))
        
        if not image_files:
            messagebox.showwarning("警告", "画像ファイルが見つかりません")
            return
        
        if self.create_subfolder.get():
            output_folder = os.path.join(output_folder, f"cropped_{x}_{y}_{w}x{h}")
        os.makedirs(output_folder, exist_ok=True)
        
        self.progress_var.set(0)
        self.progress_label.config(text="処理中...")
        self.btn_batch.config(state='disabled')
        self.root.update()
        
        success = 0
        error = 0
        for i, path in enumerate(image_files, 1):
            try:
                img = Image.open(path)
                if x + w > img.width or y + h > img.height:
                    error += 1
                    continue
                cropped = img.crop((x, y, x + w, y + h))
                name, ext = os.path.splitext(os.path.basename(path))
                out_name = f"{name}_cropped{ext}" if self.keep_original_name.get() else f"cropped_{i:04d}{ext}"
                out_path = os.path.join(output_folder, out_name)
                cropped.save(out_path)
                success += 1
            except:
                error += 1
            self.progress_var.set((i / len(image_files)) * 100)
            self.progress_label.config(text=f"処理中... {i}/{len(image_files)}")
            self.root.update()
        
        self.progress_label.config(text=f"完了！ 成功: {success}, 失敗: {error}")
        self.btn_batch.config(state='normal')
        messagebox.showinfo("完了", f"成功: {success}枚\n失敗: {error}枚")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCropper(root)
    root.mainloop()
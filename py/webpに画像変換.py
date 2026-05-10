import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

def select_files_or_folder():
    """ファイルまたはフォルダを選択する"""
    # サイズ指定の取得
    try:
        target_w = int(entry_width.get())
        target_h = int(entry_height.get())
        if target_w <= 0 or target_h <= 0:
            raise ValueError
        use_resize = True
    except ValueError:
        # サイズが未入力または不正な場合はリサイズなし
        use_resize = False
        if entry_width.get() or entry_height.get():
            # 入力があるのに不正な値の場合のみ警告
            if not messagebox.askyesno("サイズ確認", "サイズの値が不正です。リサイズせずに変換しますか？"):
                return
        target_w = target_h = None
    
    # 選択ダイアログ（ファイル or フォルダ）
    choice = messagebox.askyesno("選択", "フォルダを選択しますか？\n「はい」=フォルダ選択\n「いいえ」=ファイル選択")
    
    if choice:  # フォルダ選択
        folder_path = filedialog.askdirectory(title="画像が入っているフォルダを選択")
        if folder_path:
            convert_folder(folder_path, target_w, target_h, use_resize)
    else:  # ファイル選択
        file_path = filedialog.askopenfilename(
            title="変換する画像を選択",
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.tiff"), ("All files", "*.*")]
        )
        if file_path:
            convert_single_file(file_path, target_w, target_h, use_resize)

def convert_single_file(input_path, target_w=None, target_h=None, use_resize=False):
    """単一ファイルを変換"""
    try:
        # 保存先を選択
        output_dir = filedialog.askdirectory(title="保存先フォルダを選択")
        if not output_dir:
            return
        
        # ファイル名を取得（拡張子なし）
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.webp")
        
        # 画像変換
        convert_to_webp(input_path, output_path, target_w, target_h, use_resize)
        messagebox.showinfo("完了", f"変換が完了しました:\n{output_path}")
        
    except Exception as e:
        messagebox.showerror("エラー", f"変換に失敗しました:\n{str(e)}")

def convert_folder(folder_path, target_w=None, target_h=None, use_resize=False):
    """フォルダ内の画像を一括変換"""
    try:
        # 保存先フォルダを選択
        output_dir = filedialog.askdirectory(title="保存先フォルダを選択")
        if not output_dir:
            return
        
        # 対応する画像拡張子
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
        
        # フォルダ内の画像ファイルを取得
        image_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith(image_extensions):
                image_files.append(file)
        
        if not image_files:
            messagebox.showwarning("警告", "画像ファイルが見つかりませんでした。")
            return
        
        # 変換処理
        converted_count = 0
        failed_files = []
        
        # サイズ指定がある場合の確認
        if use_resize:
            size_info = f" {target_w}×{target_h}px"
            if not messagebox.askyesno("サイズ確認", f"すべての画像を{size_info}にリサイズして変換します。よろしいですか？"):
                return
        else:
            size_info = " 元サイズ"
        
        for filename in image_files:
            try:
                input_path = os.path.join(folder_path, filename)
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(output_dir, f"{base_name}.webp")
                
                convert_to_webp(input_path, output_path, target_w, target_h, use_resize)
                converted_count += 1
                
            except Exception as e:
                failed_files.append(f"{filename}: {str(e)}")
        
        # 結果表示
        result_message = f"変換完了: {converted_count}ファイル (サイズ:{size_info})\n"
        if failed_files:
            result_message += f"\n失敗: {len(failed_files)}ファイル\n"
            for failed in failed_files[:5]:  # 最初の5件だけ表示
                result_message += f"・{failed}\n"
            if len(failed_files) > 5:
                result_message += f"…他{len(failed_files)-5}件\n"
        
        messagebox.showinfo("変換結果", result_message)
        
    except Exception as e:
        messagebox.showerror("エラー", f"変換に失敗しました:\n{str(e)}")

def convert_to_webp(input_path, output_path, target_w=None, target_h=None, use_resize=False, quality=90):
    """画像をWebPに変換（サイズ指定対応）"""
    # 画像を開く
    img = Image.open(input_path)
    
    # RGBAに変換（透過対応）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # サイズ指定がある場合のみリサイズ
    if use_resize and target_w and target_h:
        # アスペクト比を維持せずに指定サイズにリサイズ
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # WebPで保存
    img.save(output_path, "WEBP", quality=quality)

def convert_and_show_image():
    """画像を選択して変換（元の機能を維持）"""
    global tk_img, current_img
    
    input_path = filedialog.askopenfilename(
        title="変換する画像を選択",
        filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp"), ("All files", "*.*")]
    )
    if not input_path:
        return
    
    current_img = Image.open(input_path).convert("RGBA")
    
    # 元のサイズを入力欄に反映
    width, height = current_img.size
    entry_width.delete(0, tk.END)
    entry_width.insert(0, str(width))
    entry_height.delete(0, tk.END)
    entry_height.insert(0, str(height))
    
    # プレビュー表示
    preview_img = current_img.copy()
    preview_img.thumbnail((300, 300))
    tk_img = ImageTk.PhotoImage(preview_img)
    image_label.config(image=tk_img)
    
    messagebox.showinfo("確認", "画像が読み込まれました。サイズを確認して保存してください。")

def save_image():
    """サイズ指定して保存（元の機能を維持）"""
    global current_img
    if 'current_img' not in globals():
        messagebox.showwarning("警告", "先に画像を選択してください。")
        return
    
    try:
        target_w = int(entry_width.get())
        target_h = int(entry_height.get())
    except ValueError:
        messagebox.showerror("エラー", "サイズには数値を入力してください。")
        return
    
    # 左端の色を透過にする処理
    img = current_img.copy()
    left_color = img.getpixel((0, 0))
    new_data = []
    for item in img.getdata():
        if item[:3] == left_color[:3]:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    
    # 指定サイズにリサイズ
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # WebPで保存
    output_path = filedialog.asksaveasfilename(
        title="保存先を選択",
        defaultextension=".webp",
        filetypes=[("WebP Images", "*.webp")]
    )
    
    if output_path:
        img.save(output_path, "WEBP")
        messagebox.showinfo("完了", f"保存が完了しました:\n{output_path}")

# --- GUI作成 ---
root = tk.Tk()
root.title("WebP一括変換ツール（サイズ指定対応）")
root.geometry("420x680")

# サイズ指定の説明
size_frame = tk.Frame(root, bg="#f0f0f0", relief=tk.RIDGE, bd=2)
size_frame.pack(pady=10, padx=10, fill=tk.X)

tk.Label(size_frame, text="【変換サイズ設定】", bg="#f0f0f0", font=("", 10, "bold")).pack(pady=2)
tk.Label(size_frame, text="※未入力の場合は元サイズで変換", bg="#f0f0f0", fg="gray").pack()

# サイズ入力エリア（一元化）
frame_size = tk.Frame(root)
frame_size.pack(pady=5)

tk.Label(frame_size, text="幅:", font=("", 11)).grid(row=0, column=0)
entry_width = tk.Entry(frame_size, width=10, font=("", 11), justify="center")
entry_width.grid(row=0, column=1, padx=5)

tk.Label(frame_size, text="×", font=("", 14, "bold")).grid(row=0, column=2, padx=5)

tk.Label(frame_size, text="高さ:", font=("", 11)).grid(row=0, column=3)
entry_height = tk.Entry(frame_size, width=10, font=("", 11), justify="center")
entry_height.grid(row=0, column=4, padx=5)

tk.Label(frame_size, text="px", font=("", 11)).grid(row=0, column=5)

# 一括変換ボタン
btn_batch = tk.Button(root, text="📁 一括変換（フォルダ/ファイル）", 
                     command=select_files_or_folder, height=2, width=25, 
                     bg="#d1e7dd", font=("", 10, "bold"))
btn_batch.pack(pady=15)

# 区切り線
tk.Frame(root, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=5, pady=10)

# 従来の機能（単一ファイル・透過処理）
tk.Label(root, text="【従来モード（透過処理あり）】", font=("", 9, "bold")).pack()

btn_select = tk.Button(root, text="① 画像を選択", command=convert_and_show_image, height=1, width=15)
btn_select.pack(pady=2)

btn_save = tk.Button(root, text="② 透過処理して保存", command=save_image, height=1, width=15, bg="#e1e1e1")
btn_save.pack(pady=2)

# プレビューラベル
image_label = tk.Label(root, text="画像がここに表示されます", bg="#f5f5f5", width=40, height=8)
image_label.pack(pady=10)

# 使い方説明
help_text = """
【使い方】
1. 上部で変換サイズを指定（未入力=元サイズ）
2. 「一括変換」ボタンでファイル/フォルダを選択
   → 指定サイズでWebPに変換（元のファイル名保持）

【従来モード】
・左端の色を透過処理して保存（サイズ指定可）
"""
tk.Label(root, text=help_text, justify=tk.LEFT, fg="gray", bg="#fafafa").pack(pady=5, fill=tk.X, padx=10)

root.mainloop()
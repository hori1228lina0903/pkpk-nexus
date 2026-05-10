import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import tkinter.ttk as ttk
from bs4 import BeautifulSoup
import re
import requests

class DeckScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Limitless Decklist Generator")
        self.root.geometry("950x750")

        # ノートブック（タブ）を作成
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # タブ1: URLから取得（元の機能）
        self.url_frame = tk.Frame(self.notebook)
        self.notebook.add(self.url_frame, text="URLから取得")
        self.setup_url_tab()

        # タブ2: HTMLファイルから抽出（新機能）
        self.file_frame = tk.Frame(self.notebook)
        self.notebook.add(self.file_frame, text="HTMLファイルから抽出")
        self.setup_file_tab()

        self.current_output = ""

    def setup_url_tab(self):
        """URLから取得するタブ"""
        main_frame = tk.Frame(self.url_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(main_frame, text="Limitless Decklist URL:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.url_entry = tk.Entry(main_frame, width=100)
        self.url_entry.pack(fill=tk.X, pady=5)
        self.url_entry.insert(0, "https://play.limitlesstcg.com/tournament/69bc5b69d478313a15a2f015/player/warpis/decklist")

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn = tk.Button(btn_frame, text="HTML生成実行", command=self.fetch_and_convert,
                            bg="#2196F3", fg="white", font=("Arial", 10, "bold"), padx=20)
        self.btn.pack(side=tk.LEFT, padx=5)

        self.copy_btn = tk.Button(btn_frame, text="コピー", command=self.copy_to_clipboard,
                                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=20, state=tk.DISABLED)
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(btn_frame, text="", font=("Arial", 9))
        self.status_label.pack(side=tk.LEFT, padx=10)

        tk.Label(main_frame, text="出力結果:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10,5))
        self.result_area = scrolledtext.ScrolledText(main_frame, width=100, height=30, font=("Courier", 10))
        self.result_area.pack(fill=tk.BOTH, expand=True, pady=5)

        clear_btn = tk.Button(main_frame, text="クリア", command=self.clear_result, bg="#FF9800", fg="white")
        clear_btn.pack(pady=5)

    def setup_file_tab(self):
        """HTMLファイルから抽出するタブ（ファイル選択のみ）"""
        main_frame = tk.Frame(self.file_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ファイル選択エリア
        tk.Label(main_frame, text="HTMLファイルを選択:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # 選択されたファイル名を表示するラベル
        self.file_label = tk.Label(main_frame, text="ファイルが選択されていません", fg="gray", bg="white", 
                                    anchor=tk.W, relief=tk.SUNKEN, padx=5, pady=5)
        self.file_label.pack(fill=tk.X, pady=5)
        
        # 参照ボタンのみ
        self.browse_btn = tk.Button(main_frame, text="ファイルを参照", command=self.browse_file, 
                                     bg="#607D8B", fg="white", font=("Arial", 10), padx=10, pady=5)
        self.browse_btn.pack(pady=5)

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.file_btn = tk.Button(btn_frame, text="HTML生成実行", command=self.convert_from_file,
                            bg="#2196F3", fg="white", font=("Arial", 10, "bold"), padx=20, state=tk.DISABLED)
        self.file_btn.pack(side=tk.LEFT, padx=5)

        self.file_copy_btn = tk.Button(btn_frame, text="コピー", command=self.copy_file_result,
                                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=20, state=tk.DISABLED)
        self.file_copy_btn.pack(side=tk.LEFT, padx=5)

        self.file_status_label = tk.Label(btn_frame, text="", font=("Arial", 9))
        self.file_status_label.pack(side=tk.LEFT, padx=10)

        tk.Label(main_frame, text="出力結果:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10,5))
        self.file_result_area = scrolledtext.ScrolledText(main_frame, width=100, height=30, font=("Courier", 10))
        self.file_result_area.pack(fill=tk.BOTH, expand=True, pady=5)

        file_clear_btn = tk.Button(main_frame, text="クリア", command=self.clear_file_result, bg="#FF9800", fg="white")
        file_clear_btn.pack(pady=5)

        self.file_current_output = ""
        self.selected_file_path = ""

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="HTMLファイルを選択",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        if filename:
            self.selected_file_path = filename
            # ファイル名だけを表示
            self.file_label.config(text=os.path.basename(filename), fg="green")
            self.file_btn.config(state=tk.NORMAL)
            self.update_file_status(f"選択: {os.path.basename(filename)}")

    def clear_result(self):
        self.result_area.delete(1.0, tk.END)
        self.current_output = ""
        self.copy_btn.config(state=tk.DISABLED)

    def clear_file_result(self):
        self.file_result_area.delete(1.0, tk.END)
        self.file_current_output = ""
        self.file_copy_btn.config(state=tk.DISABLED)

    def copy_to_clipboard(self):
        if self.current_output:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_output)
            self.update_status("コピーしました！")
            messagebox.showinfo("コピー完了", "テキストをクリップボードにコピーしました")

    def copy_file_result(self):
        if self.file_current_output:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.file_current_output)
            self.update_file_status("コピーしました！")
            messagebox.showinfo("コピー完了", "テキストをクリップボードにコピーしました")

    def update_status(self, message, is_error=False):
        self.status_label.config(text=message, fg="red" if is_error else "green")
        self.root.update()

    def update_file_status(self, message, is_error=False):
        self.file_status_label.config(text=message, fg="red" if is_error else "green")
        self.root.update()

    def convert_set_code(self, set_code):
        """セットコードを小文字に変換し、P-A → promo-a なども処理"""
        code_lower = set_code.lower()
        if code_lower == "p-a":
            return "promo-a"
        elif code_lower == "p-b":
            return "promo-b"
        return code_lower

    def fetch_and_convert(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "URLを入力してください")
            return

        self.btn.config(state=tk.DISABLED)
        self.copy_btn.config(state=tk.DISABLED)
        self.update_status("ページを取得中...")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            output_html = self.extract_decklist(soup)

            self.result_area.delete(1.0, tk.END)
            if output_html:
                self.result_area.insert(tk.END, output_html)
                self.current_output = output_html
                self.copy_btn.config(state=tk.NORMAL)
                card_count = output_html.count('deck-card')
                self.update_status(f"完了: {card_count}枚のカードを抽出しました")
                messagebox.showinfo("成功", f"{card_count}枚のカードを抽出しました")
            else:
                self.result_area.insert(tk.END, "❌ カードデータが見つかりませんでした")
                self.current_output = ""
                self.update_status("カードが見つかりません", True)

        except Exception as e:
            self.update_status(f"エラー: {str(e)[:50]}", True)
            messagebox.showerror("Error", f"エラーが発生しました:\n{str(e)}")
        finally:
            self.btn.config(state=tk.NORMAL)

    def convert_from_file(self):
        if not self.selected_file_path:
            messagebox.showerror("Error", "HTMLファイルを選択してください")
            return

        self.file_btn.config(state=tk.DISABLED)
        self.file_copy_btn.config(state=tk.DISABLED)
        self.update_file_status("ファイルを読み込み中...")

        try:
            with open(self.selected_file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            output_html = self.extract_decklist(soup)

            self.file_result_area.delete(1.0, tk.END)
            if output_html:
                self.file_result_area.insert(tk.END, output_html)
                self.file_current_output = output_html
                self.file_copy_btn.config(state=tk.NORMAL)
                card_count = output_html.count('deck-card')
                self.update_file_status(f"完了: {card_count}枚のカードを抽出しました")
                messagebox.showinfo("成功", f"{card_count}枚のカードを抽出しました")
            else:
                self.file_result_area.insert(tk.END, "❌ カードデータが見つかりませんでした\n\n")
                self.file_result_area.insert(tk.END, "確認事項:\n")
                self.file_result_area.insert(tk.END, "1. decklistクラスのdivが存在しますか？\n")
                self.file_result_area.insert(tk.END, "2. 正しいHTMLファイルを選択していますか？\n")
                self.file_current_output = ""
                self.update_file_status("カードが見つかりません", True)

        except FileNotFoundError:
            self.update_file_status("ファイルが見つかりません", True)
            messagebox.showerror("Error", f"ファイルが見つかりません: {self.selected_file_path}")
        except Exception as e:
            self.update_file_status(f"エラー: {str(e)[:50]}", True)
            messagebox.showerror("Error", f"エラーが発生しました:\n{str(e)}")
        finally:
            self.file_btn.config(state=tk.NORMAL)

    def extract_decklist(self, soup):
        """デッキリストを抽出（絶対URLからセット番号とカード番号を抽出）"""
        output = ""
        
        decklist_div = soup.find('div', class_='decklist')
        if not decklist_div:
            return ""
        
        # 全てのcolumnを処理
        columns = decklist_div.find_all('div', class_='column')
        
        for column in columns:
            # カード行を取得 (pタグ)
            card_ps = column.find_all('p')
            
            for p in card_ps:
                link = p.find('a', href=re.compile(r'pocket.limitlesstcg.com/cards/|/cards/'))
                if not link:
                    continue
                
                # URLを取得
                absolute_url = link.get('href', '')
                
                # URLからセットコードとカード番号を抽出
                url_match = re.search(r'/cards/([^/]+)/(\d+)', absolute_url)
                if not url_match:
                    continue
                
                set_code_raw = url_match.group(1)
                card_number = url_match.group(2)
                
                # テキストから枚数を取得
                text = p.get_text(strip=True)
                match = re.match(r'(\d+)', text)
                count = match.group(1) if match else "1"
                
                # カード名をテキストから取得（カッコを除去）
                card_name_raw = re.sub(r'\s*\([^)]+\)\s*$', '', text)
                card_name_raw = re.sub(r'^\d+\s+', '', card_name_raw)
                
                # セットコードを変換
                set_code = self.convert_set_code(set_code_raw)
                
                # カード名をURL用にフォーマット
                card_name_formatted = card_name_raw.replace(' ', '_').replace("'", "")
                card_name_formatted = re.sub(r'[éèê]', 'e', card_name_formatted)
                card_name_formatted = re.sub(r'[^a-zA-Z0-9_]', '', card_name_formatted)
                
                # カード名表示用
                card_name_display = card_name_raw.replace('-', ' ').title()
                
                # リンクパスと画像パス
                link_path = f"/cards/{set_code}/{card_number}/{card_name_formatted}.html"
                image_path = f"/images/cards/{set_code}/{card_number}.webp"
                
                output += f'''          <div class="deck-card">
            <a href="{link_path}" class="card-link">
              <img src="{image_path}" alt="{card_name_display}">
              <span class="card-count">×{count}</span>
            </a>
          </div>
'''
        
        return output

if __name__ == "__main__":
    import os
    root = tk.Tk()
    app = DeckScraperGUI(root)
    root.mainloop()
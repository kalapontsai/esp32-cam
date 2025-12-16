import subprocess
import datetime
import os
import glob

# --- 設定 ---
IMAGE_DIR = "images"
OUTPUT_DIR = "output"

# 確保輸出目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_timelapse_video():
    """將前一個小時的圖片組合成 MP4 影片。"""
    
    # 獲取「前一個」小時的時間戳記，因為要處理剛結束的那個小時的圖片
    one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
    
    # 產生匹配前一個小時圖片的檔案名稱樣式 (YYYYMMDD_HH*)
    # 例如：如果是 18:00 執行，就會處理 17:00-17:55 的圖片
    time_prefix = one_hour_ago.strftime("%Y%m%d_%H")
    input_pattern = os.path.join(IMAGE_DIR, f"{time_prefix}*.jpg")
    output_filename = os.path.join(OUTPUT_DIR, f"{time_prefix}_timelapse.mp4")
    
    # 輸出影片檔名
    output_filename = os.path.join(OUTPUT_DIR, f"{time_prefix}_timelapse.mp4")

    # 檢查是否有符合條件的圖片
    image_files = sorted(glob.glob(input_pattern))
    if not image_files:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 警告: 找不到符合 {time_prefix}* 樣式的圖片，跳過。")
        return

    list_file_path = os.path.join(os.getcwd(), "list.txt") # 放在腳本執行目錄下
    
    # 這是確保每張圖片顯示 3 秒的關鍵邏輯
    print(f"正在生成圖片列表檔案: {list_file_path}")
    with open(list_file_path, "w") as f:
        for file_path in image_files:
            relative_path = file_path.replace("\\", "/") 
            f.write(f"file '{relative_path}'\n")
            f.write(f"duration 3\n") # ⬅️ 確保這行存在！這會讓圖片在輸出影片中持續 3.0 秒
        
        # 最後一張圖片需要重複 file 行，以確保它在影片結尾被完整納入
        # 這裡使用最後一個相對路徑
        f.write(f"file '{relative_path}'\n")

    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 正在組合 {len(image_files)} 張圖片為影片...")
    
    # FFmpeg 指令：使用 pattern_type glob 讀取圖片序列
    command = [
    "ffmpeg",
    # 讀取列表檔案
    "-f", "concat",
    "-safe", "0",
    "-i", list_file_path,  # 這裡的 list_file_path 指向 list.txt
    
    # 輸出設定
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    "-y",
    output_filename
    ]
    
    try:
        # 執行 FFmpeg 指令 (這次暫時保留錯誤輸出以確保成功)
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 成功創建影片: {output_filename}")
        
        # 4. 檔案清理
        os.remove(list_file_path)
        # ... (刪除圖片的邏輯不變)
        
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] FFmpeg 影片製作失敗，退出碼: {e.returncode}")
        print("--- FFmpeg 錯誤輸出 (stderr) ---")
        print(e.stderr) # 打印 FFmpeg 報告的實際錯誤
        print("---------------------------------")
        # 這是您當前看到的錯誤
        # print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] FFmpeg 影片製作失敗: {e}")
    except FileNotFoundError:
        print("錯誤: 找不到 FFmpeg。請確認它已安裝並設定到系統路徑中。")

if __name__ == "__main__":
    create_timelapse_video()
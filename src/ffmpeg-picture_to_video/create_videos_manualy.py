import subprocess
import datetime
import os
import glob
import time

# --- 設定 ---
IMAGE_DIR = "images"
OUTPUT_DIR = "output"
LIST_FILE_NAME = "manual_list.txt"
IMAGE_DURATION_SECONDS = 0.1  # 每張圖片在影片中顯示的秒數

# 確保目錄存在
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_timelapse_video_manual():
    """
    手動執行縮時攝影影片製作。
    找出 images 目錄中所有圖片，生成 list.txt，並調用 FFmpeg 合成影片。
    """
    print("--- 縮時攝影影片製作啟動 ---")
    
    # 1. 找出所有圖片檔案
    # 使用 *.* 匹配所有檔案，並按名稱排序 (確保時間順序正確)
    input_pattern = os.path.join(IMAGE_DIR, "*.*")
    image_files = sorted(glob.glob(input_pattern))
    
    if not image_files:
        print("警告: 在 images 目錄中找不到任何圖片檔案，請確認圖片已擷取。")
        return

    # 2. 創建列表檔案 (list.txt)
    list_file_path = os.path.join(os.getcwd(), LIST_FILE_NAME) 
    
    print(f"正在生成圖片列表檔案: {list_file_path}，共找到 {len(image_files)} 張圖片。")
    
    try:
        with open(list_file_path, "w") as f:
            
            # 遍歷所有圖片，寫入 file 和 duration (3 秒)
            for file_path in image_files:
                # 確保路徑使用 FFmpeg 慣用的正斜線
                relative_path = file_path.replace("\\", "/") 
                f.write(f"file '{relative_path}'\n")
                f.write(f"duration {IMAGE_DURATION_SECONDS}\n") 
            
            # 寫入最後一行：重複最後一張圖片的路徑，確保它被包含
            final_file_path = image_files[-1].replace("\\", "/") 
            f.write(f"file '{final_file_path}'\n") 
            
    except Exception as e:
        print(f"錯誤: 生成列表檔案失敗: {e}")
        return

    # 3. 創建輸出檔名（使用當前日期時間戳記）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(OUTPUT_DIR, f"manual_timelapse_{timestamp}.mp4")

    print(f"正在組合影片，每張圖片顯示 {IMAGE_DURATION_SECONDS} 秒...")

    # 4. FFmpeg 命令：使用 concat demuxer 讀取列表檔案
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file_path,  # 讀取生成的列表檔案
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",          # 輸出影片播放幀率 30 fps
        "-y",
        output_filename
    ]
    
    try:
        # 執行 FFmpeg 指令，並捕捉輸出以診斷潛在錯誤
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ 成功創建影片: {output_filename}")
        
        # 5. 檔案清理
        print(f"正在清理生成的列表檔案: {LIST_FILE_NAME}...")
        os.remove(list_file_path)
        print("--- 影片製作完成 ---")

    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ FFmpeg 影片製作失敗，退出碼: {e.returncode}")
        print("--- FFmpeg 錯誤輸出 (stderr) ---")
        print(e.stderr) 
        print("---------------------------------")
    except FileNotFoundError:
        print("❌ 錯誤: 找不到 FFmpeg。請確認它已安裝並設定到系統路徑中。")

if __name__ == "__main__":
    create_timelapse_video_manual()
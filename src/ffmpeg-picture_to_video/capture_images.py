import subprocess
import time
import datetime
import os
import ctypes  # 防止 Windows 休眠 & 關閉 QuickEdit
from PIL import Image, ImageDraw, ImageFont # 導入 Pillow 函式庫

# --- 設定 ---
STREAM_URL = "http://10.35.31.13:81/stream"  # 替換為你的串流 URL
CAPTURE_INTERVAL_SECONDS = 300  
IMAGE_DIR = "images"

# --- 網路連線設定 ---
FFMPEG_TIMEOUT_SECONDS = 30  # FFmpeg 執行超時時間（秒）
MAX_RETRY_ATTEMPTS = 3  # 最大重試次數
RETRY_DELAY_SECONDS = 5  # 重試間隔（秒）

# --- 等待顯示設定 ---
WAIT_STATUS_INTERVAL = 60  # 等待期間每 N 秒顯示一次剩餘時間

# --- Pillow 浮水印設定 ---
FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf"  # 確保這是您系統中存在的字型路徑
FONT_SIZE = 20
TEXT_COLOR = (255, 255, 255) # 白色 (R, G, B)
BOX_COLOR = (0, 0, 0, 128)   # 黑色半透明 (R, G, B, Alpha)
PADDING = 10

# 確保圖片目錄存在
os.makedirs(IMAGE_DIR, exist_ok=True)

def apply_watermark(image_path):
    """使用 Pillow 繪製日期時間浮水印在圖片左下角。"""
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img, 'RGBA') # 使用 RGBA 模式支援半透明

        # 獲取時間戳記
        current_time_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        # 嘗試載入字型
        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except IOError:
            # 如果找不到指定字型，使用預設字型
            font = ImageFont.load_default() 
            print("警告: 找不到 Arial 字型，使用預設字型。")

        # 測量文字大小
        bbox = draw.textbbox((0, 0), current_time_str, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 計算位置 (左下角)
        x = PADDING
        y = img.height - text_height - PADDING
        
        # 繪製半透明背景框 (與 FFmpeg 的 box=1 類似)
        box_x1 = x - PADDING // 2
        box_y1 = y - PADDING // 2
        box_x2 = x + text_width + PADDING
        box_y2 = y + text_height + PADDING // 2
        
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=BOX_COLOR)

        # 繪製文字
        draw.text((x, y), current_time_str, font=font, fill=TEXT_COLOR)
        
        # 覆蓋原檔案儲存
        img.save(image_path)
        
    except Exception as e:
        print(f"Pillow 繪製浮水印失敗: {e}")


def capture_frame(stream_url, image_dir, retry_count=0):
    """FFmpeg 擷取圖片，然後使用 Pillow 繪製浮水印。
    
    Args:
        stream_url: 串流 URL
        image_dir: 圖片儲存目錄
        retry_count: 當前重試次數（內部使用）
    """
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(image_dir, f"{timestamp}.jpg")
    
    # FFmpeg 命令，加入網路超時和重連參數
    command = [
        "ffmpeg",
        "-timeout", str(FFMPEG_TIMEOUT_SECONDS * 1000000),  # 超時時間（微秒）
        "-reconnect", "1",  # 啟用自動重連
        "-reconnect_at_eof", "1",  # 在 EOF 時重連
        "-reconnect_streamed", "1",  # 流式重連
        "-reconnect_delay_max", "5",  # 最大重連延遲（秒）
        "-i", stream_url,
        "-ss", "00:00:01",
        "-vframes", "1",
        "-q:v", "2",
        "-y",
        "-loglevel", "error",  # 只顯示錯誤訊息
        output_filename
    ]
    
    try:
        # 1. 執行 FFmpeg 擷取圖片（帶超時）
        if retry_count > 0:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 重試擷取 (第 {retry_count} 次)...")
        
        result = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=FFMPEG_TIMEOUT_SECONDS + 5  # 額外5秒緩衝
        )
        
        # 檢查檔案是否成功建立
        if not os.path.exists(output_filename) or os.path.getsize(output_filename) == 0:
            raise subprocess.CalledProcessError(1, command, "檔案未成功建立或檔案大小為0")
        
        # 2. 使用 Pillow 對剛儲存的圖片進行浮水印處理
        apply_watermark(output_filename)
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 成功擷取並添加浮水印: {output_filename}")
        return True
        
    except subprocess.TimeoutExpired:
        error_msg = f"FFmpeg 執行超時（超過 {FFMPEG_TIMEOUT_SECONDS} 秒）"
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {error_msg}")
        
        # 清理可能產生的不完整檔案
        if os.path.exists(output_filename):
            try:
                os.remove(output_filename)
            except:
                pass
        
        # 重試機制
        if retry_count < MAX_RETRY_ATTEMPTS:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {RETRY_DELAY_SECONDS} 秒後重試...")
            time.sleep(RETRY_DELAY_SECONDS)
            return capture_frame(stream_url, image_dir, retry_count + 1)
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 已達最大重試次數，跳過此次擷取")
            return False
            
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg 執行失敗"
        if e.stderr:
            # 解碼錯誤訊息（可能包含中文）
            try:
                stderr_msg = e.stderr.decode('utf-8', errors='ignore').strip()
                if stderr_msg:
                    error_msg += f": {stderr_msg[:200]}"  # 限制長度
            except:
                pass
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {error_msg}")
        
        # 清理可能產生的不完整檔案
        if os.path.exists(output_filename):
            try:
                os.remove(output_filename)
            except:
                pass
        
        # 重試機制（僅針對網路相關錯誤）
        if retry_count < MAX_RETRY_ATTEMPTS:
            # 檢查是否為網路相關錯誤
            stderr_lower = ""
            if e.stderr:
                try:
                    stderr_lower = e.stderr.decode('utf-8', errors='ignore').lower()
                except:
                    pass
            
            network_errors = ['timeout', 'connection', 'network', 'unreachable', 'refused', 'reset']
            if any(err in stderr_lower for err in network_errors):
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 偵測到網路問題，{RETRY_DELAY_SECONDS} 秒後重試...")
                time.sleep(RETRY_DELAY_SECONDS)
                return capture_frame(stream_url, image_dir, retry_count + 1)
        
        if retry_count >= MAX_RETRY_ATTEMPTS:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 已達最大重試次數，跳過此次擷取")
        
        return False
        
    except FileNotFoundError:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 錯誤: 找不到 FFmpeg。請確認它已安裝並設定到系統路徑中。")
        return False
        
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 未預期的錯誤: {e}")
        return False

def wait_with_countdown(seconds):
    """顯示倒計時等待，定期顯示剩餘時間"""
    # 使用 monotonic 避免系統時間調整或休眠後造成倒計時跳動
    start_monotonic = time.monotonic()
    next_status_monotonic = start_monotonic + WAIT_STATUS_INTERVAL
    end_monotonic = start_monotonic + seconds
    last_tick_monotonic = start_monotonic

    # 修正點 1: 啟動等待時強制刷新
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 等待 {seconds} 秒，下次擷取時間: {(datetime.datetime.now() + datetime.timedelta(seconds=seconds)).strftime('%H:%M:%S')}", flush=True)
    
    while True:
        now_monotonic = time.monotonic()
        # 偵測是否經歷長時間停滯（可能是系統休眠或主機喚醒）
        tick_gap = now_monotonic - last_tick_monotonic
        if tick_gap > WAIT_STATUS_INTERVAL * 3:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 偵測到程式被暫停約 {int(tick_gap)} 秒，可能是系統休眠，已繼續倒計時。", flush=True)
        last_tick_monotonic = now_monotonic
        remaining = end_monotonic - now_monotonic

        if remaining <= 0:
            break

        # 可能因系統休眠/切出導致延遲，補齊應該顯示的狀態
        while now_monotonic >= next_status_monotonic and remaining > 0:
            remaining_minutes = max(0, int(remaining // 60))
            remaining_seconds = max(0, int(remaining % 60))
            next_capture_time = datetime.datetime.now() + datetime.timedelta(seconds=max(0, remaining))
            # 修正點 2: 定期狀態更新時強制刷新
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 剩餘時間: {remaining_minutes} 分 {remaining_seconds} 秒，下次擷取: {next_capture_time.strftime('%H:%M:%S')}", flush=True)
            next_status_monotonic += WAIT_STATUS_INTERVAL

        # 只睡到下一個狀態輸出點，避免長時間睡眠在休眠後累積誤差
        sleep_time = min(1.0, remaining, max(0, next_status_monotonic - now_monotonic))
        if sleep_time > 0:
            time.sleep(sleep_time)

    # 修正點 3: 結束等待時強制刷新
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 等待結束，開始下一次擷取...", flush=True)

def prevent_sleep():
    """在 Windows 上防止系統進入睡眠。"""
    try:
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    except Exception:
        # 非 Windows 或呼叫失敗時略過
        pass

def disable_console_quick_edit():
    """關閉 Windows Console 的 QuickEdit，避免選取文字時整個程式被暫停。"""
    try:
        # 取得標準輸入的 handle
        STD_INPUT_HANDLE = -10
        ENABLE_QUICK_EDIT_MODE = 0x0040
        h_in = ctypes.windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)
        if h_in == 0 or h_in == -1:
            return
        mode = ctypes.c_ulong()
        if ctypes.windll.kernel32.GetConsoleMode(h_in, ctypes.byref(mode)) == 0:
            return
        new_mode = mode.value & ~ENABLE_QUICK_EDIT_MODE
        ctypes.windll.kernel32.SetConsoleMode(h_in, new_mode)
    except Exception:
        # 非 Windows 或無法修改時略過
        pass

def main():
    print(f"啟動串流擷取，間隔為 {CAPTURE_INTERVAL_SECONDS} 秒...")
    print(f"網路設定: 超時 {FFMPEG_TIMEOUT_SECONDS} 秒，最大重試 {MAX_RETRY_ATTEMPTS} 次")
    print(f"串流 URL: {STREAM_URL}")
    print(f"圖片儲存目錄: {os.path.abspath(IMAGE_DIR)}")
    print("-" * 60)
    
    consecutive_failures = 0
    max_consecutive_failures = 5  # 連續失敗次數上限

    # 防止系統睡眠
    prevent_sleep()
    # 關閉 QuickEdit 避免選取文字時程式被暫停
    disable_console_quick_edit()
    
    while True:
        success = capture_frame(STREAM_URL, IMAGE_DIR)
        
        if success:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 警告: 連續 {max_consecutive_failures} 次擷取失敗，請檢查網路連線")
                consecutive_failures = 0  # 重置計數器，繼續嘗試
        
        # 顯示倒計時等待
        wait_with_countdown(CAPTURE_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
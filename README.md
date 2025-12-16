## CameraWebServer.ino
. add ssid list to connect in case we use it in many places.
. add  reconnect function

## capture_images.py
. use ffmpeg command to capture camera stream 

## create_videos
. because i can't use 'glob' parameter to collect all the pictures in 'images' folder. so it will create a list.txt and read it one by one to process the timelapse animation video.

## connect link 
. esp32-cam的串流影像 : http://<ESP32-CAM_IP>:81/stream

. camera config : http://<ESP32-CAM_IP>.

## ESP32-CAM 影像參數說明
1. AWB（Auto White Balance，自動白平衡）

功能：自動調整影像的色溫，使畫面中的白色看起來真正是白色。

關閉時，畫面可能會偏黃、偏藍。

建議：一般保持 開啟。

2. AWB Gain（白平衡增益）

功能：調整紅、綠、藍三色的補償程度。

前提：通常 AWB 要關閉才有效。

用途：手動微調色偏，例如室內黃光補藍、自然光補紅等。

建議：若不做色彩校正，可保持預設。

3. WB Mode（白平衡模式）

功能：指定環境光源類型，以改善顏色準確度。

常見模式：

Auto：自動

Sunny：晴天

Cloudy：陰天

Office：螢光燈

Home：鎢絲燈

建議：若 AWB 開啟 → 通常讓系統自動即可。

4. AEC SENSOR（使用感光元件自動曝光）

功能：曝光（亮度）由感光元件自動控制。

開啟：亮度會自動調整。

關閉：可搭配 AEC DSP、AE Level 手動控制曝光。

建議：一般使用保持 開啟。

5. AEC DSP（使用 DSP 進行曝光控制）

功能：讓 DSP 接管曝光的部分演算法。

作用範圍：關閉時會變成更「純粹」的感光控制。

用途：需要特殊亮度反應時，才會關閉。

建議：保持 開啟，除非做影像分析或特殊曝光需求。

6. AE Level（自動曝光補償）

功能：微調整體亮度（曝光補償 EV）。

常用值範圍：-2 ~ +2 或 -5 ~ +5（視版本）

效果：

數值變大 → 更亮

數值變小 → 更暗

使用情境：逆光、陰暗或高亮場景修正。

7. AGC（Auto Gain Control，自動增益控制）

功能：自動提高感光度，使畫面在低光下仍維持亮度。

缺點：增益越高，畫面越容易出現噪點（雪花）。

建議：一般保持 開啟，若有足夠照明可關閉減少噪點。

8. Gain Ceiling（增益上限）

功能：當 AGC 開啟時，限制增益的最大值。

數值越高：亮度提高能力越強，但噪點越多。

建議：

若環境亮 → 設低值（減少噪點）

若環境暗 → 設高值（確保畫面亮度）

9. BPC（Black Pixel Correction，黑點修正）

功能：修正常見的「黑色壞點」。

開啟可改善壞點帶來的小黑點雜訊。

建議：保持 開啟。

10. WPC（White Pixel Correction，白點修正）

功能：修正「白色壞點」。

效果：在低光環境特別有用，可減少熱噪點造成的亮白點。

建議：保持 開啟。

11. Raw GMA（Gamma 校正）

功能：控制影像 Gamma 曲線，使亮部不過亮、暗部不全黑。

開啟：畫面更自然、細節更均衡。

關閉：畫面對比更硬、暗部細節較差。

建議：一般保持 開啟。

12. Lens Correction（鏡頭畸變校正）

功能：修正廣角鏡頭造成的變形（魚眼效果）。

開啟：邊緣拉伸、線條較直。

缺點：需計算，影像 FPS 變低。

建議：

若需要畫面自然、線條筆直 → 開啟

若追求高 FPS 或不介意變形 → 關閉

Sensor Resolution
UXGA (1600x1200)
Offset
X:400
Y:300
Window Size
X:800
Y:600
Output Size
X:320
Y:240

改成
Sensor Resolution

UXGA (1600x1200)
Offset
X:0
Y:150
Window Size
X:800
Y:600
Output Size
X:320
Y:240

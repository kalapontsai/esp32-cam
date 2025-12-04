//2025-12-04 modify wifi STA / AP mode server function
//添加了 Preferences 库用于 EEPROM 读写
//添加了 WiFi 配置的 EEPROM 存储功能
//实现了从 EEPROM 读取 WiFi 配置的功能
//修改了 setup() 函数：
//开机时从 EEPROM 读取 SSID 和密码
//尝试连接 WiFi
//连接成功：启动 STA+AP 模式
//连接失败：仅启动 AP 模式
//添加了 manualConnectWiFi() 函数，供网页调用进行手动连接

#include "esp_camera.h"
#include <WiFi.h>
#include <Preferences.h>

// ===========================
// Select camera model in board_config.h
// ===========================
#include "board_config.h"

// ===========================
// WiFi EEPROM Storage
// ===========================
Preferences preferences;
const char* PREF_NAMESPACE = "wifi_config";
const char* PREF_SSID_KEY = "ssid";
const char* PREF_PASS_KEY = "password";

// AP模式配置
const char* AP_SSID = "ESP32-CAM";
const char* AP_PASSWORD = "12345678";

// WiFi状态（全局变量，供app_httpd.cpp使用）
bool wifiConnected = false;
String staIP = "";

void startCameraServer();
void setupLedFlash();
bool loadWiFiFromEEPROM(String &ssid, String &password);
void saveWiFiToEEPROM(const String &ssid, const String &password);
bool connectToWiFi(const String &ssid, const String &password);
void manualConnectWiFi(const String &ssid, const String &password);

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;  // for streaming
  //config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // if PSRAM IC present, init with UXGA resolution and higher JPEG quality
  //                      for larger pre-allocated frame buffer.
  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      // Limit the frame size when PSRAM is not available
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    // Best option for face detection/recognition
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  // initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);        // flip it back
    s->set_brightness(s, 1);   // up the brightness just a bit
    s->set_saturation(s, -2);  // lower the saturation
  }
  // drop down frame size for higher initial frame rate
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

// Setup LED FLash if LED pin is defined in camera_pins.h
#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  // 初始化EEPROM
  preferences.begin(PREF_NAMESPACE, false);
  
  // 从EEPROM读取WiFi配置
  String ssid = "";
  String password = "";
  
  if (loadWiFiFromEEPROM(ssid, password) && ssid.length() > 0) {
    Serial.println("从EEPROM读取WiFi配置:");
    Serial.print("SSID: ");
    Serial.println(ssid);
    
    // 尝试连接WiFi
    Serial.print("正在连接WiFi...");
    if (connectToWiFi(ssid, password)) {
      wifiConnected = true;
      staIP = WiFi.localIP().toString();
      Serial.println("");
      Serial.println("WiFi连接成功!");
      Serial.print("STA IP: ");
      Serial.println(staIP);
      
      // 连接成功后，启动STA+AP模式
      WiFi.mode(WIFI_AP_STA);
      WiFi.softAP(AP_SSID, AP_PASSWORD);
      Serial.print("AP模式已启动: ");
      Serial.print(AP_SSID);
      Serial.print(", AP IP: ");
      Serial.println(WiFi.softAPIP());
    } else {
      Serial.println("");
      Serial.println("WiFi连接失败，仅启动AP模式");
      wifiConnected = false;
      staIP = "";
      // 连接失败，仅启动AP模式
      WiFi.mode(WIFI_AP);
      WiFi.softAP(AP_SSID, AP_PASSWORD);
      Serial.print("AP模式已启动: ");
      Serial.print(AP_SSID);
      Serial.print(", AP IP: ");
      Serial.println(WiFi.softAPIP());
    }
  } else {
    Serial.println("EEPROM中没有WiFi配置，启动AP模式");
    wifiConnected = false;
    staIP = "";
    // 没有配置，仅启动AP模式
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    Serial.print("AP模式已启动: ");
    Serial.print(AP_SSID);
    Serial.print(", AP IP: ");
    Serial.println(WiFi.softAPIP());
  }
  
  WiFi.setSleep(false);

  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  if (wifiConnected) {
    Serial.print(staIP);
    Serial.println("' (STA) or 'http://");
    Serial.print(WiFi.softAPIP());
    Serial.println("' (AP) to connect");
  } else {
    Serial.print(WiFi.softAPIP());
    Serial.println("' (AP) to connect");
  }
}

// 从EEPROM读取WiFi配置
bool loadWiFiFromEEPROM(String &ssid, String &password) {
  ssid = preferences.getString(PREF_SSID_KEY, "");
  password = preferences.getString(PREF_PASS_KEY, "");
  return (ssid.length() > 0);
}

// 保存WiFi配置到EEPROM
void saveWiFiToEEPROM(const String &ssid, const String &password) {
  preferences.putString(PREF_SSID_KEY, ssid);
  preferences.putString(PREF_PASS_KEY, password);
  preferences.end();
  preferences.begin(PREF_NAMESPACE, false);
  Serial.println("WiFi配置已保存到EEPROM");
}

// 连接WiFi
bool connectToWiFi(const String &ssid, const String &password) {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid.c_str(), password.c_str());
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  return (WiFi.status() == WL_CONNECTED);
}

// 手动连接WiFi（从网页调用）
void manualConnectWiFi(const String &ssid, const String &password) {
  Serial.println("手动连接WiFi...");
  Serial.print("SSID: ");
  Serial.println(ssid);
  
  if (connectToWiFi(ssid, password)) {
    wifiConnected = true;
    staIP = WiFi.localIP().toString();
    Serial.println("WiFi连接成功!");
    Serial.print("STA IP: ");
    Serial.println(staIP);
    
    // 保存到EEPROM
    saveWiFiToEEPROM(ssid, password);
    
    // 启动STA+AP模式
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    Serial.print("AP模式已启动: ");
    Serial.print(AP_SSID);
    Serial.print(", AP IP: ");
    Serial.println(WiFi.softAPIP());
  } else {
    Serial.println("WiFi连接失败");
    wifiConnected = false;
    staIP = "";
  }
}

void loop() {
  // Do nothing. Everything is done in another task by the web server
  delay(10000);
}

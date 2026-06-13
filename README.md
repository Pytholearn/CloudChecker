<div align="center">

# ☁️ Cloud Checker

**Cloudflare IP Scanner — tuned for restricted networks**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-blue)]()
[![GitHub](https://img.shields.io/github/stars/Pytholearn/CloudChecker?style=social)](https://github.com/Pytholearn/CloudChecker)

[English](#features) • [فارسی](#-فارسی)

<br>

```
          ☁                                                     ☁
                .~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
          .~~~~'                                               '~~~.
      .~~'                                                         '~~.
    .'                                                                 '.
   /   ██████╗██╗      ██████╗ ██╗   ██╗██████╗                          \
  |   ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗                          |
  |   ██║     ██║     ██║   ██║██║   ██║██║  ██║                          |
  |   ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝                         |
  |        ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗         |
  |       ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝       |
  |       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║       |
   \                      made by hazard                                /
    '.                  github.com/Pytholearn                        .'
      '~~.                                                      .~~'
               '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
```

</div>

---

## Features

- **Phase 1 — Connectivity Scan**: Probes thousands of Cloudflare edge IPs via TLS handshake + HTTP `/cdn-cgi/trace` to find reachable ones
- **Phase 2 — Speed Test**: Downloads 100 KB from `speed.cloudflare.com` on the top 10 candidates to measure real throughput
- **Config Modifier**: Paste a VLESS/Trojan config URL + provide an IP list → generates new configs with each clean IP (like [v2ray-config-modifier](https://seramo.github.io/v2ray-config-modifier/))
- **Custom Range Scan**: Scan any CIDR range or IP list — not limited to official Cloudflare ranges
- **Max Latency Filter**: Skip IPs above a configurable latency threshold (200ms / 500ms / 1000ms / custom)
- **Export**: Save results as CSV, JSON, or plain IP list
- **Clipboard Copy**: Copy the best IP to clipboard with one keypress
- **Auto-Update CF Ranges**: Fetches latest Cloudflare IP ranges from `cloudflare.com/ips-v4/` daily, cached locally
- **Neighbor Scanning**: Automatically probes nearby IPs of the best results
- **Persistent Settings**: All scan settings saved between sessions
- **Live TUI**: Smooth, flicker-free terminal UI powered by [Rich](https://github.com/Textualize/rich)

---

## Installation

### Quick Install (Windows)

```bash
git clone https://github.com/Pytholearn/CloudChecker.git
cd CloudChecker
install.bat
```

### Manual Install (All Platforms)

**Requirements:** Python 3.8+

```bash
git clone https://github.com/Pytholearn/CloudChecker.git
cd CloudChecker
pip install -r requirements.txt
```

### Run

```bash
python CloudChecker.py
```

---

## Usage

### 1. Find Working IPs

1. Launch the tool → select **Find Working IPs**
2. *(Optional)* Paste a VLESS/Trojan config URL for SNI-based probing
3. Configure scan settings with arrow keys:

| Setting | Options | Default |
|---------|---------|---------|
| **Source** | Random / From File / Custom Range | Random |
| **Count** | 1,000 / 5,000 / 20,000 / Custom | 5,000 |
| **Workers** | 50 / 100 / 200 / Custom | 50 |
| **Timeout** | 2s / 3s / 5s / Custom | 5s |
| **Max Latency** | No limit / 200ms / 500ms / 1000ms / Custom | No limit |
| **Ports** | 443, 8443, 2053, 2083, 2087, 2096 | 443 |

4. Press **Enter** to start scanning
5. Watch live results — press **q** to stop early
6. After scan: copy best IP, export CSV/JSON, save to `ips.txt`

### 2. Config Modifier

1. Select **Config Modifier** from main menu
2. Paste your base VLESS/Trojan config URL
3. Provide an IP list file (or press Enter to use last scan results)
4. Browse generated configs → **[s]** save to file, **[c]** copy all

### 3. Custom Range Scan

Select **Custom Range** as source in scan settings, then enter CIDR ranges or IPs:

```
▶ 8.6.112.0/24
▶ 45.85.118.0/24
▶ 188.114.96.0/20
▶                     ← empty line to finish
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate menu / scroll |
| `←` `→` | Change option |
| `Enter` | Select / Confirm |
| `Space` | Toggle port |
| `q` / `ESC` | Back / Stop scan |
| `s` | Save (in config modifier) |
| `c` | Copy (in config modifier) |

---

## Output Files

| File | Content |
|------|---------|
| `CloudChecker-YYYYMMDD-HHMMSS.txt` | All healthy IPs (auto-saved) |
| `ips.txt` | Clean IP list (manual save) |
| `CloudChecker-*.csv` | Full results with latency, loss, colo, speed |
| `CloudChecker-*.json` | JSON format results |
| `configs-*.txt` | Generated V2Ray configs |

---

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│  Generate /  │────▶│  Phase 1:    │────▶│  Neighbor   │────▶│ Phase 2: │
│  Load IPs    │     │  TLS Probe   │     │  Scan ±12   │     │ Speed    │
│              │     │  /cdn-cgi/   │     │  around top │     │ Test     │
│              │     │  trace       │     │  5 IPs      │     │ top 10   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
                          │                                        │
                          ▼                                        ▼
                    Filter by:                              Sort by speed
                    - max latency                           & latency
                    - connectivity
```

---

## Configuration

Settings are saved to:
- **Windows:** `%APPDATA%\cloudchecker\config.json`
- **macOS:** `~/Library/Application Support/cloudchecker/config.json`
- **Linux:** `~/.config/cloudchecker/config.json`

Cloudflare IP ranges are cached in the same directory and refreshed every 24 hours.

---

## Credits

- Built with [Rich](https://github.com/Textualize/rich) for terminal UI
- Auto-update via [autoupgrader](https://pypi.org/project/autoupgrader/)
- Inspired by [SenPaiScanner](https://github.com/MatinSenPai/SenPaiScanner)
- Extended CF ranges from [ircfspace/cf-ip-ranges](https://github.com/ircfspace/cf-ip-ranges)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

---

<div align="center">

**made by hazard**

[GitHub](https://github.com/Pytholearn) • [Report Bug](https://github.com/Pytholearn/CloudChecker/issues)

</div>

---
---

<div dir="rtl" align="right">

# ☁️ فارسی

## کلود چکر — اسکنر آیپی کلادفلر برای شبکه‌های محدود

ابزاری برای پیدا کردن آیپی‌های تمیز کلادفلر که روی شبکه شما کار میکنن، همراه با تست سرعت دانلود.

---

## امکانات

- **فاز ۱ — اسکن اتصال**: هزاران آیپی لبه کلادفلر رو از طریق TLS + HTTP تست میکنه
- **فاز ۲ — تست سرعت**: سرعت دانلود واقعی ۱۰ آیپی برتر رو اندازه میگیره
- **تغییر کانفیگ**: کانفیگ VLESS/Trojan رو با آیپی‌های تمیز ترکیب میکنه (مثل سایت seramo)
- **اسکن رنج دلخواه**: هر CIDR یا آیپی دلخواهی رو میتونی اسکن کنی
- **فیلتر لیتنسی**: آیپی‌های کند رو حذف کن (۲۰۰/۵۰۰/۱۰۰۰ میلی‌ثانیه)
- **خروجی**: ذخیره به CSV، JSON، یا لیست آیپی ساده
- **کپی**: بهترین آیپی رو با یک کلید کپی کن
- **بروزرسانی خودکار رنج‌ها**: رنج‌های CF رو از سایت رسمی هر ۲۴ ساعت آپدیت میکنه
- **اسکن همسایه**: خودکار آیپی‌های نزدیک بهترین نتایج رو تست میکنه
- **ذخیره تنظیمات**: تمام تنظیمات بین جلسات ذخیره میشه
- **رابط کاربری زنده**: انیمیشن روان بدون لرزش با Rich

---

## نصب

### نصب سریع (ویندوز)

```bash
git clone https://github.com/Pytholearn/CloudChecker.git
cd CloudChecker
install.bat
```

### نصب دستی (همه پلتفرم‌ها)

**پیش‌نیاز:** Python 3.8+

```bash
git clone https://github.com/Pytholearn/CloudChecker.git
cd CloudChecker
pip install -r requirements.txt
```

### اجرا

```bash
python CloudChecker.py
```

---

## نحوه استفاده

### ۱. پیدا کردن آیپی سالم

1. ابزار رو اجرا کن → **Find Working IPs** رو انتخاب کن
2. *(اختیاری)* لینک کانفیگ VLESS/Trojan رو پیست کن
3. تنظیمات اسکن رو با کلیدهای جهتی تنظیم کن:

| تنظیم | گزینه‌ها | پیش‌فرض |
|-------|---------|---------|
| **منبع** | رندوم / از فایل / رنج دلخواه | رندوم |
| **تعداد** | ۱٬۰۰۰ / ۵٬۰۰۰ / ۲۰٬۰۰۰ / دلخواه | ۵٬۰۰۰ |
| **ورکر** | ۵۰ / ۱۰۰ / ۲۰۰ / دلخواه | ۵۰ |
| **تایم‌اوت** | ۲ث / ۳ث / ۵ث / دلخواه | ۵ث |
| **حداکثر لیتنسی** | بدون حد / ۲۰۰ms / ۵۰۰ms / ۱۰۰۰ms / دلخواه | بدون حد |
| **پورت‌ها** | 443, 8443, 2053, 2083, 2087, 2096 | 443 |

4. **Enter** بزن تا اسکن شروع بشه
5. نتایج زنده رو ببین — **q** بزن برای توقف
6. بعد از اسکن: کپی بهترین آیپی، خروجی CSV/JSON، ذخیره در `ips.txt`

### ۲. تغییر کانفیگ

1. از منو **Config Modifier** رو انتخاب کن
2. لینک کانفیگ پایه VLESS/Trojan رو پیست کن
3. فایل لیست آیپی رو بده (یا Enter بزن برای استفاده از نتایج آخرین اسکن)
4. کانفیگ‌های ساخته شده رو ببین → **[s]** ذخیره، **[c]** کپی همه

### ۳. اسکن رنج دلخواه

توی تنظیمات اسکن **Custom Range** رو انتخاب کن، بعد رنج‌های CIDR یا آیپی وارد کن:

```
▶ 8.6.112.0/24
▶ 45.85.118.0/24
▶ 188.114.96.0/20
▶                     ← خط خالی = پایان
```

---

## کلیدهای میانبر

| کلید | عملکرد |
|------|--------|
| `↑` `↓` | حرکت بین منو / اسکرول |
| `←` `→` | تغییر گزینه |
| `Enter` | انتخاب / تایید |
| `Space` | تغییر وضعیت پورت |
| `q` / `ESC` | بازگشت / توقف اسکن |
| `s` | ذخیره (در تغییر کانفیگ) |
| `c` | کپی (در تغییر کانفیگ) |

---

## فایل‌های خروجی

| فایل | محتوا |
|------|-------|
| `CloudChecker-YYYYMMDD-HHMMSS.txt` | آیپی‌های سالم (ذخیره خودکار) |
| `ips.txt` | لیست آیپی تمیز (ذخیره دستی) |
| `CloudChecker-*.csv` | نتایج کامل با لیتنسی، لاس، کولو، سرعت |
| `CloudChecker-*.json` | نتایج به فرمت JSON |
| `configs-*.txt` | کانفیگ‌های V2Ray ساخته شده |

---

## نحوه کار

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│ ساخت / لود  │────▶│   فاز ۱:     │────▶│   اسکن      │────▶│  فاز ۲:  │
│   آیپی‌ها    │     │   پروب TLS   │     │   همسایه    │     │   تست    │
│              │     │  /cdn-cgi/   │     │   ±۱۲ آیپی  │     │   سرعت   │
│              │     │   trace      │     │   اطراف ۵   │     │  ۱۰ برتر │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
```

---

**ساخته شده توسط hazard**

[گیت‌هاب](https://github.com/Pytholearn) • [گزارش باگ](https://github.com/Pytholearn/CloudChecker/issues)

</div>

# VU+ Stream EPG Refresh

🌊 **Stream-based EPG refresh for VU+ receivers**

## 🎯 Features

- **🔥 No Live-TV Interruption** - Stream fetching instead of zapping
- **📺 Unlimited Channels** - Processes ALL channels in bouquet  
- **⚡ Configurable Sweet Spot** - Tune duration (0.5s - 30s)
- **🤖 Zero Dependencies** - Pure Python standard library
- **⏰ Automation Ready** - Perfect for cron jobs
- **🎮 VU+ Compatible** - All VU+ models with web interface

## 🚀 Quick Start

```bash
# Standard refresh (4s sweet spot)
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "My Channels"

# Fast refresh (2s sweet spot)
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "Sky" --duration=2.0

# Automated (for cron jobs)
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --duration=4.0 --force
```

## 📋 Requirements

- **Python 3.6+** (no external packages needed!)
- **VU+ Receiver** with web interface enabled
- **Network connection** to VU+ receiver

## 📊 How It Works

1. **Analyzes bouquet** - Finds all TV/Radio services
2. **Checks EPG status** - Identifies services without EPG data  
3. **Fetches streams** - Downloads transport stream for X seconds
4. **Triggers EPG update** - VU+ automatically updates EPG data
5. **Live TV continues** - No interruption to current viewing

## 🎯 Sweet Spot Recommendations

| Duration | Use Case | Reliability | Speed |
|----------|----------|-------------|-------|
| **2.0s** | Quick refresh | ⭐⭐⭐ | 🚀🚀🚀 |
| **4.0s** | **Standard** ✅ | ⭐⭐⭐⭐ | 🚀🚀 |  
| **6.0s** | Conservative | ⭐⭐⭐⭐⭐ | 🚀 |
| **8.0s** | Maximum | ⭐⭐⭐⭐⭐ | 🐌 |

## ⏰ Automation Setup

### Linux/WSL Cron Job
```bash
# Daily at 3:00 AM
0 3 * * * cd /path/to/script && python3 vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --force
```

### Windows Task Scheduler
```batch
python C:\path\to\vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --force
```

## 📈 Sample Output

```
🔍 Suche Services ohne EPG in 'Sky'...
  📺 Bouquet gefunden: Sky Deutschland HD
  📊 Lade alle Services aus Bouquet...
  📺 BOUQUET 'Sky' ENTHÄLT 156 SERVICES TOTAL
  📻 TV/Radio Services: 134
  📂 Andere (Ordner/etc): 22
  ✅ Mit EPG: 89
  🔄 Ohne EPG: 45 ← Stream-Refresh nötig

🌊 STREAM-BASIERTES EPG-REFRESH
Services: 45
Sweet Spot: 4.0s pro Service
✅ Live-TV wird NICHT unterbrochen!

[01/45] Sky Cinema Premiere HD            📡1 📊512KB ✅ 24 events
[02/45] Sky Cinema Action HD              📡1 📊487KB ✅ 18 events
...
📊 ERGEBNIS: 43/45 erfolgreich
🎯 Live-TV blieb ungestört! 127 neue EPG-Events
```

## 🔧 Technical Details

The script uses these VU+ web interface endpoints:
- `/web/getservices` - Get bouquet services
- `/web/ts?sRef=...` - Transport stream (primary)
- `/web/stream.m3u8?ref=...` - HLS stream (fallback)
- `/web/epgservice?sRef=...` - Check EPG data

## 🤝 Contributing

Contributions welcome! This script has been tested with:
- VU+ Duo², Solo², Ultimo, Zero
- OpenATV, OpenPLi, VTi images
- Various satellite/cable/terrestrial setups

## 📜 License

MIT License - Use freely for personal and commercial projects.

## 🙏 Credits

Developed by wakdo - Inspired by the need for non-disruptive EPG updates in headless VU+ setups.

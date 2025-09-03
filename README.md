# VU+ Stream EPG Refresh

🌊 **Stream-based EPG refresh for VU+ receivers**

## 🎯 Features

- **🔥 No Live-TV Interruption** - Stream fetching instead of zapping
- **📺 Unlimited Channels** - Processes ALL channels in bouquet  
- **🚫 Smart Channel Skipping** - Skip unwanted channels via string matching
- **🔐 HTTP Basic Auth** - Optional username/password authentication
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

# Refresh only channels with less than 5 EPG events
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "Sky" --max_events=5

# Skip specific channels (string matching)
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --skip="Sky Sport,Sky Bundesliga"

# With HTTP Basic Authentication
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --username=admin --password=secret

# Automated (for cron jobs)
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --duration=4.0 --force

# Combined: Fast refresh for channels with less than 3 EPG events, skip Sky channels
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --duration=2.0 --max_events=3 --skip="Sky" --force

# Full featured: Auth + Skip + Duration + Force
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --username=admin --password=secret --duration=3.0 --skip="Adult,Test" --force
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

## 🚫 Channel Skipping (--skip)

The `--skip` parameter allows skipping specific channels based on string matching:

**How it works:**
- Comma-separated list of search strings: `--skip="String1,String2,String3"`
- Case-insensitive substring matching in channel names
- Channel is skipped if **any** of the skip strings is contained in the name
- Perfect for excluding problematic or unwanted channels

**Examples:**
```bash
# Skip Sky Sport channels
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --skip="Sky Sport"

# Skip multiple categories
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --skip="Sky Sport,Sky Bundesliga,Adult"

# Exclude test and demo channels
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --skip="Test,Demo,Preview"
```

**String-Matching Examples:**
- `--skip="Sky Sport"` skips: "Sky Sport 1 HD", "Sky Sport 2", "Sky Sport News"
- `--skip="HD"` skips all HD channels
- `--skip="Radio"` skips all radio stations

## 🔐 HTTP Basic Authentication

For VU+/Dreambox devices with enabled web interface password protection:

**Parameters:**
- `--username=USER` - HTTP Basic Auth username
- `--password=PASS` - HTTP Basic Auth password
- Both parameters are optional and only needed when auth is enabled

**Examples:**
```bash
# Standard auth (common combinations)
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --username=admin --password=admin
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --username=root --password=dreambox

# Custom auth with other parameters
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "Sky" --username=myuser --password=mypass --duration=3.0

# Auth + Skip combined
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --username=admin --password=secret --skip="Adult,Test"
```

**Notes:**
- Works with standard HTTP Basic Authentication (RFC 7617)
- Automatic URL encoding: `http://user:pass@host:port`
- Without auth parameters, the script works as usual
- Secure password transmission only with HTTPS (usually not available on VU+)

## 🎢 EPG Filtering (max_events)

The `--max_events` parameter enables intelligent EPG filtering:

**How it works:**
- Default value: `0` = All channels without EPG will be refreshed
- Value > 0: Only channels with fewer than X EPG events will be refreshed
- Prevents unnecessary refreshes on channels with existing EPG data

| max_events | Behavior | Use Case |
|------------|----------|----------|
| **0** | All without EPG ✅ | Standard mode |
| **1-5** | Only with very little EPG | Fine tuning |
| **10-20** | Only with incomplete EPG | Performance optimization |
| **50+** | Almost all channels | Maintenance mode |

**Examples:**
```bash
# Only completely empty channels (default)
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "Sky" --max_events=0

# Refresh channels with fewer than 5 EPG events
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "Sky" --max_events=5

# Performance: Only refresh when fewer than 20 events
python vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --max_events=20 --duration=2.0
```

## ⏰ Automation Setup

### Linux/WSL Cron Job
```bash
# Daily at 3:00 AM
0 3 * * * cd /path/to/script && python3 vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --force

# With HTTP Auth (recommended: credentials in separate config)
0 3 * * * cd /path/to/script && python3 vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --username=admin --password=secret --force
```

### Windows Task Scheduler
```batch
python C:\\path\\to\\vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --force

REM With HTTP Auth
python C:\\path\\to\\vu_stream_epgrefresh.py 192.168.1.100 bouquet "All" --username=admin --password=secret --force
```

## 📈 Sample Output

### Standard Mode (max_events=0)
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

### Skip Mode (--skip="Sky Sport")
```
🚫 Skip Strings: ['Sky Sport']
🔍 Suche Services ohne EPG in 'All'...
  📺 Bouquet gefunden: Alle Kanäle
  📊 Lade alle Services aus Bouquet...
  📺 BOUQUET 'All' ENTHÄLT 200 SERVICES TOTAL
  🚫 Übersprungen: Sky Sport 1 HD (enthält 'Sky Sport')
  🚫 Übersprungen: Sky Sport 2 HD (enthält 'Sky Sport')
  🚫 Übersprungen: Sky Sport News HD (enthält 'Sky Sport')
  🔄 Braucht Refresh: ARD HD ( 0 Events )
  🔄 Braucht Refresh: ZDF HD ( 0 Events )
  ✅ 15 Services mit EPG analysiert...
```

### Filtered Mode (max_events=5)
```
🔍 Suche Services ohne EPG in 'Sky'...
  📺 Bouquet gefunden: Sky Deutschland HD
  📊 Lade alle Services aus Bouquet...
  📺 BOUQUET 'Sky' ENTHÄLT 156 SERVICES TOTAL
  🔄 Braucht Refresh: Sky Cinema Premiere HD ( 2 Events )
  🔄 Braucht Refresh: Sky Cinema Action HD ( 0 Events )
  🔄 Braucht Refresh: Sky Sport News HD ( 4 Events )
  ✅ 20 Services mit EPG analysiert...

📊 BOUQUET-ANALYSE:
  📺 TOTAL Services: 156
  📻 TV/Radio Services: 134
  📂 Andere (Ordner/etc): 22
  ✅ Mit EPG: 119 (> 5 Events)
  🔄 Ohne EPG: 15 (≤ 5 Events) ← Stream-Refresh nötig

🌊 STREAM-BASIERTES EPG-REFRESH
Services: 15
Sweet Spot: 4.0s pro Service
✅ Live-TV wird NICHT unterbrochen!

[01/15] Sky Cinema Premiere HD            📡1 📊512KB ✅ 24 events
[02/15] Sky Cinema Action HD              📡1 📊487KB ✅ 18 events
...
📊 ERGEBNIS: 14/15 erfolgreich
🎯 Live-TV blieb ungestört! 89 neue EPG-Events
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

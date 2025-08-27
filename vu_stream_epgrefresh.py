#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VU+ Stream-basiertes EPG-Refresh - BUGFIX VERSION 2.0
NEUE METHODE: Stream holen statt Zappen → Live-TV ungestört!

🐛 BUGFIXES V2.0:
- ✅ VLC User-Agent für bessere VU+ Kompatibilität
- ✅ Optimierte HTTP-Header gegen Verbindungsprobleme
- ✅ Dynamisches Timeout-Handling (6-20s adaptive)
- ✅ 16KB Chunks für bessere Performance
- ✅ Intelligente Content-Type-Erkennung
- ✅ Adaptive Stream-Limits (5MB Video, 3MB andere)
- ✅ Frühe Erfolgs-Erkennung für stabile Streams
- ✅ Erweiterte Stream-URLs mit mehr Fallbacks
- ✅ Spezifisches Exception-Handling für HTTP-Fehler
- ✅ Verbesserte Stream-Validierung

Usage: python vu_stream_epgrefresh.py <IP> bouquet <name> [--duration=4.0] [--force]
"""

# MINIMAL IMPORTS - nur was wirklich gebraucht wird
import sys
import urllib.request
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote
import threading
import io

class VUStreamEPGRefresher:
    def __init__(self, host, port=80, force_mode=False, debug_mode=False):
        self.host = host
        self.port = port
        self.base_url = f'http://{host}:{port}'  # Web-Interface
        self.stream_base_url = f'http://{host}:8001'  # BUGFIX: Stream-Server auf Port 8001
        self.force_mode = force_mode
        self.debug_mode = debug_mode
        
    def _make_request(self, endpoint, timeout=10):
        """Einfacher HTTP Request"""
        try:
            url = self.base_url + endpoint
            response = urllib.request.urlopen(url, timeout=timeout)
            content = response.read().decode('utf-8', errors='ignore')
            return {'success': True, 'content': content}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def find_services_without_epg(self, bouquet_name, max_events=0):
        """Findet Services ohne EPG-Daten - UNLIMITED"""
        print(f"🔍 Suche Services ohne EPG in '{bouquet_name}'...")
        
        # Bouquet finden
        bouquets_result = self._make_request('/web/getservices')
        if not bouquets_result['success']:
            return []
        
        target_bouquet = None
        try:
            root = ET.fromstring(bouquets_result['content'])
            for service in root.findall('.//e2service'):
                service_ref_elem = service.find('e2servicereference')
                service_name_elem = service.find('e2servicename')
                
                if service_ref_elem is not None and service_name_elem is not None:
                    ref = service_ref_elem.text.strip()
                    name = service_name_elem.text.strip()
                    
                    if ref.startswith('1:7:') and bouquet_name.lower() in name.lower():
                        target_bouquet = ref
                        print(f"  📺 Bouquet gefunden: {name}")
                        break
        except Exception as e:
            print(f"  ❌ Bouquet-Fehler: {e}")
            return []
        
        if not target_bouquet:
            print(f"  ❌ Bouquet '{bouquet_name}' nicht gefunden")
            return []
        
        print(f"  📊 Lade alle Services aus Bouquet...")
        
        # Services ohne EPG finden
        services_result = self._make_request(f'/web/getservices?sRef={quote(target_bouquet, safe="")}')
        if not services_result['success']:
            return []
        
        services_without_epg = []
        services_with_epg = []
        total_services_in_bouquet = 0
        tv_radio_services = 0
        
        try:
            root = ET.fromstring(services_result['content'])
            all_services = root.findall('.//e2service')
            total_services_in_bouquet = len(all_services)
            
            print(f"  📺 BOUQUET '{bouquet_name}' ENTHÄLT {total_services_in_bouquet} SERVICES TOTAL")
            
            for service in all_services:
                service_ref_elem = service.find('e2servicereference')
                service_name_elem = service.find('e2servicename')
                
                if service_ref_elem is not None and service_name_elem is not None:
                    service_ref = service_ref_elem.text.strip()
                    service_name = service_name_elem.text.strip()
                    
                    # Nur echte TV/Radio Services
                    if service_ref.startswith('1:0:') and service_name != "<n/a>":
                        tv_radio_services += 1
                        # EPG prüfen
                        epg_result = self._make_request(f'/web/epgservice?sRef={quote(service_ref, safe="")}')
                        events = 0

                        if epg_result['success']:
                            events = epg_result['content'].count('<e2event>')
                        
                        if events <= max_events:
                            services_without_epg.append({'ref': service_ref, 'name': service_name, 'events': events})
                            print(f"  🔄 Braucht Refresh: {service_name} ( {events} Events )")
                        else:
                            services_with_epg.append({'ref': service_ref, 'name': service_name, 'events': events})
                            if len(services_with_epg) % 20 == 0:  # Status alle 20 Services
                                print(f"  ✅ {len(services_with_epg)} Services mit EPG analysiert...")
                            
        except Exception as e:
            print(f"  ❌ Service-Analyse Fehler: {e}")
        
        other_services = total_services_in_bouquet - tv_radio_services
        print(f"\n📊 BOUQUET-ANALYSE:")
        print(f"  📺 TOTAL Services: {total_services_in_bouquet}")
        print(f"  📻 TV/Radio Services: {tv_radio_services}")
        print(f"  📂 Andere (Ordner/etc): {other_services}")
        print(f"  ✅ Mit EPG: {len(services_with_epg)}")
        print(f"  🔄 Ohne EPG: {len(services_without_epg)} ← Stream-Refresh nötig")
        
        # Für Debug: Nur ersten 2 Services für Test
        if self.debug_mode and len(services_without_epg) > 2:
            print(f"  🐛 DEBUG: Begrenze auf ersten 2 Services für Test")
            return services_without_epg[:2]
        return services_without_epg  # ALLE ohne Limit!
    
    def stream_based_epg_refresh(self, services, duration=5.0):
        """Stream-basiertes EPG-Refresh OHNE Zapping"""
        if not services:
            print("✅ Keine Services brauchen EPG-Refresh!")
            return True, 0
        
        print(f"\n🌊 STREAM-BASIERTES EPG-REFRESH")
        print(f"Services: {len(services)}")
        print(f"Sweet Spot: {duration}s pro Service")
        print(f"✅ Live-TV wird NICHT unterbrochen!")
        print()
        
        successful = 0
        total_new_events = 0
        
        for i, service in enumerate(services):
            print(f"[{i+1:2d}/{len(services)}] {service['name'][:40]:<40}", end=" ")
            
            try:
                encoded_ref = quote(service['ref'], safe='')
                
                # BUGFIX: Korrekte Stream URLs für Port 8001 basierend auf VU+ M3U8 Format
                #stream_urls = [
                #    f'/{service["ref"]}',                       # Direkt Service-Ref (wie in M3U8)
                #    f'/web/ts?sRef={encoded_ref}',              # Web-Interface TS (Port 80)
                #    f'/web/stream.m3u8?ref={encoded_ref}',      # Web-Interface M3U8 (Port 80)
                #    f'/web/stream?ref={encoded_ref}',           # Web-Interface Generic (Port 80)
                #]
                stream_urls = [
                    f'/{service["ref"]}',                       # Direkt Service-Ref (wie in M3U8)
                ]

                stream_success = False
                bytes_received = 0
                
                for j, stream_url in enumerate(stream_urls):
                    try:
                        if self.debug_mode:
                            print(f"\n    🔗 URL {j+1}: {stream_url}")
                        else:
                            print(f"📡{j+1}", end=" ")
                        
                        # BUGFIX: Erste URL über Port 8001 (Stream-Server), andere über Port 80 (Web-Interface)
                        if j == 0:  # Erste URL ist direkter Stream auf Port 8001
                            full_url = self.stream_base_url + stream_url
                            print(f" {full_url} ", end=" ")
                        else:  # Andere URLs über Web-Interface auf Port 80
                            full_url = self.base_url + stream_url
                        
                        req = urllib.request.Request(full_url)
                        # BUGFIX: Verbesserte HTTP-Header für VU+ Kompatibilität
                        req.add_header('User-Agent', 'VLC/3.0.16 LibVLC/3.0.16')  # VLC für beste Kompatibilität
                        req.add_header('Accept', '*/*')
                        req.add_header('Accept-Encoding', 'identity')  # Verhindert Kompression-Probleme
                        req.add_header('Connection', 'close')          # Verhindert Keep-Alive Issues
                        req.add_header('Cache-Control', 'no-cache')   # Verhindert Caching-Probleme
                        
                        start_time = time.time()
                        bytes_received = 0
                        chunks_count = 0
                        
                        # BUGFIX: Dynamisches Timeout (6-20s Range)
                        timeout = min(max(duration + 3, 6), 20)
                        
                        if self.debug_mode:
                            print(f"    ⏱️ Timeout: {timeout}s, Duration: {duration}s")
                        
                        with urllib.request.urlopen(req, timeout=timeout) as response:
                            content_type = response.headers.get('Content-Type', '').lower()
                            content_length = response.headers.get('Content-Length', 'unknown')
                            
                            if self.debug_mode:
                                print(f"    ✅ Connected! Status: {response.status}")
                                print(f"    📋 Content-Type: {content_type}")
                                print(f"    📏 Content-Length: {content_length}")
                                print(f"    🔄 Reading chunks...")
                            
                            while (time.time() - start_time) < duration:
                                try:
                                    # BUGFIX: 16KB Chunks für bessere Performance
                                    chunk = response.read(16384)
                                    if not chunk:
                                        if self.debug_mode:
                                            print(f"    📭 No more data (EOF)")
                                        break
                                    
                                    bytes_received += len(chunk)
                                    chunks_count += 1
                                    
                                    if self.debug_mode and chunks_count <= 3:
                                        print(f"    📦 Chunk {chunks_count}: {len(chunk)} bytes ({bytes_received//1024}KB total)")
                                    
                                    # BUGFIX: Adaptive Limits basierend auf Content-Type
                                    if 'video' in content_type or 'octet-stream' in content_type:
                                        max_bytes = 5*1024*1024  # 5MB für Video-Streams
                                        min_bytes = 16*1024     # 16KB Minimum für Video
                                    else:
                                        max_bytes = 3*1024*1024  # 3MB für andere
                                        min_bytes = 4*1024      # 4KB Minimum für andere
                                    
                                    if bytes_received > max_bytes:
                                        if self.debug_mode:
                                            print(f"    🛑 Max limit reached: {bytes_received//1024}KB")
                                        break
                                    
                                    # BUGFIX: Weniger strenge Erfolgs-Erkennung
                                    #if chunks_count >= 3 and bytes_received >= min_bytes:
                                    #    if self.debug_mode:
                                    #        print(f"    🚀 Early success: {chunks_count} chunks, {bytes_received//1024}KB")
                                    #    #break
                                        
                                except Exception as read_e:
                                    if self.debug_mode:
                                        print(f"    ❌ Read error: {read_e}")
                                    break
                        
                        # BUGFIX: Weniger strenge Stream-Validierung
                        min_threshold = 8*1024 if 'video' in content_type or 'octet-stream' in content_type else 2*1024
                        
                        if self.debug_mode:
                            print(f"    📊 Final: {bytes_received} bytes, {chunks_count} chunks, threshold: {min_threshold}")
                        
                        # Erfolg wenn wir mindestens etwas bekommen haben
                        if bytes_received >= min_threshold and chunks_count >= 1:
                            stream_success = True
                            if self.debug_mode:
                                print(f"    ✅ SUCCESS: {bytes_received//1024}KB received")
                            else:
                                print(f"📊{bytes_received//1024}KB", end=" ")
                            break
                        else:
                            if self.debug_mode:
                                print(f"    ⚠️ Not enough data: {bytes_received} bytes < {min_threshold} or {chunks_count} chunks < 1")
                            
                    # BUGFIX: Spezifisches Exception-Handling mit Debug-Output
                    except urllib.error.HTTPError as e:
                        if self.debug_mode:
                            print(f"    ❌ HTTP Error {e.code}: {e.reason}")
                        if e.code == 404:  # Service nicht verfügbar
                            continue
                        elif e.code == 403:  # Zugriff verweigert
                            continue  
                        elif e.code >= 500:  # Server-Fehler
                            time.sleep(0.1)
                            continue
                        else:
                            continue
                    except urllib.error.URLError as e:
                        if self.debug_mode:
                            print(f"    ❌ URL Error: {e.reason}")
                        continue  # Netzwerk-Probleme
                    except Exception as e:
                        if self.debug_mode:
                            print(f"    ❌ Other Exception: {type(e).__name__}: {e}")
                        continue  # Andere Fehler
                
                if not stream_success:
                    print("❌")
                    continue
                
                # EPG prüfen
                time.sleep(0.5)
                epg_result = self._make_request(f'/web/epgservice?sRef={encoded_ref}', timeout=10)
                
                if epg_result['success']:
                    events = epg_result['content'].count('<e2event>')
                    new_events = events - service['events']
                    total_new_events += max(0, new_events)
                    successful += 1
                    
                    if events > 0:
                        print(f"✅ {events} events")
                    else:
                        print(f"⚠️ 0 events")
                else:
                    print("❌ EPG failed")
                
            except Exception as e:
                print(f"❌ {str(e)[:15]}")
            
            time.sleep(0.2)  # Kurze Pause
        
        print(f"\n📊 ERGEBNIS: {successful}/{len(services)} erfolgreich")
        print(f"🎯 Live-TV blieb ungestört! {total_new_events} neue EPG-Events")
        
        return successful > 0, total_new_events
    
    def run(self, bouquet_name, duration=4.0, max_events=0):
        """Hauptfunktion"""
        print("="*70)
        print(f"VU+ STREAM EPG REFRESH - Sweet Spot: {duration}s")
        print("="*70)
        print("🎯 Stream-Methode: Live-TV ungestört!")
        print(f"📺 Bouquet: {bouquet_name}")
        print()
        
        # Services ohne EPG finden
        services_to_refresh = self.find_services_without_epg(bouquet_name, max_events=max_events)
        
        if not services_to_refresh:
            print("🎉 Alle Services haben bereits EPG-Daten!")
            return True
        
        # Bestätigung (nur wenn nicht --force)
        if not self.force_mode:
            total_time = len(services_to_refresh) * (duration + 0.5)
            print(f"\n💡 INFO:")
            print(f"  • {len(services_to_refresh)} Services brauchen Refresh")
            print(f"  • {duration}s pro Service")  
            print(f"  • ~{total_time:.0f}s Gesamtzeit")
            
            try:
                confirm = input(f"\n🚀 Stream-Refresh starten? (j/N): ").strip().lower()
                if confirm not in ['j', 'ja', 'y', 'yes']:
                    print("❌ Abgebrochen")
                    return False
            except:
                print("❌ Abgebrochen")
                return False
        
        # Stream-Refresh durchführen
        success, new_events = self.stream_based_epg_refresh(services_to_refresh, duration)
        
        if success:
            print(f"\n🎉 Stream-EPG-Refresh erfolgreich!")
            return True
        else:
            print(f"\n💥 Stream-EPG-Refresh fehlgeschlagen")
            return False

def main():
    # Einfache Parameter-Parsing ohne argparse
    if len(sys.argv) < 4:
        print("VU+ Stream EPG Refresher - Minimal Version")
        print("="*50)
        print("🌊 Stream-Methode: Kein Zapping → Live-TV ungestört")
        print()
        print("Usage:")
        print("  python vu_stream_epg.py <IP> bouquet <name> [--duration=X] [--max_events=Y] [--force]")
        print()
        print("Parameter:")
        print("  --duration=X     Stream-Duration in Sekunden (0.5-30.0, Standard: 4.0)")
        print("  --max_events=Y   Min. EPG-Events für Refresh (Standard: 0 = alle ohne EPG)")
        print("  --force          Ohne Bestätigung ausführen")
        print("  --debug          Debug-Ausgabe aktivieren")
        print()
        print("Beispiele:")
        print("  python vu_stream_epg.py 192.168.178.39 bouquet MyTV")
        print("  python vu_stream_epg.py 192.168.178.39 bouquet MyTV --duration=6.0")
        print("  python vu_stream_epg.py 192.168.178.39 bouquet MyTV --max_events=5")
        print("  python vu_stream_epg.py 192.168.178.39 bouquet MyTV --force")
        print("  python vu_stream_epg.py 192.168.178.39 bouquet MyTV --duration=2.0 --max_events=3 --force")
        return
    
    host = sys.argv[1]
    mode = sys.argv[2]  # sollte "bouquet" sein
    name = sys.argv[3]
    
    # Parameter
    force_mode = '--force' in sys.argv
    debug_mode = '--debug' in sys.argv
    duration = 4.0
    max_events = 0

    # Duration aus --duration=X extrahieren
    for arg in sys.argv:
        if arg.startswith('--duration='):
            try:
                duration = float(arg.split('=')[1])
                if duration < 0.5 or duration > 30.0:
                    print(f"❌ Duration {duration}s ungültig (0.5-30.0s)")
                    return
            except:
                print(f"❌ Ungültige Duration: {arg}")
                return
        if arg.startswith('--max_events='):
            try:
                max_events = int(arg.split('=')[1])
            except:
                print(f"❌ Ungültige max_events: {arg}")
    
    print(f"🎯 Sweet Spot: {duration}s")
    print(f"🎯 Max. Events: {max_events}")
    
    refresher = VUStreamEPGRefresher(host, force_mode=force_mode, debug_mode=debug_mode)
    
    try:
        if mode == 'bouquet':
            success = refresher.run(name, duration, max_events=max_events)
        else:
            print(f"❌ Mode '{mode}' nicht unterstützt (nur 'bouquet')")
            success = False
        
        if success:
            print(f"\n🎉 EPG-Refresh erfolgreich!")
        else:
            print(f"\n💥 EPG-Refresh fehlgeschlagen")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Unterbrochen!")
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    main()

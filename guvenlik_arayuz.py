import streamlit as st
import pandas as pd
import time
import random
import math
from datetime import datetime, timedelta

# ==========================================
# 0. SAYFA AYARLARI VE CSS
# ==========================================
st.set_page_config(page_title="BKZS Anti-Spoofing", layout="wide", initial_sidebar_state="expanded")

# Arayüzü güzelleştirmek için özel CSS
st.markdown("""
<style>
    /* Ana sayfa başlık ve düzeni */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    .stAlert {
        border-radius: 10px;
    }
    
    /* Metrik kutularının stilini geliştirme */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: bold;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. HAFIZA (SESSION STATE) BAŞLATMA
# ==========================================
if 'acceleration' not in st.session_state:
    st.session_state.acceleration = 0.0
if 'prev_speed' not in st.session_state:
    st.session_state.prev_speed = 40.0
if 'prev_lat' not in st.session_state:
    st.session_state.prev_lat = 39.92077
if 'prev_lon' not in st.session_state:
    st.session_state.prev_lon = 32.85411
if 'prev_heading' not in st.session_state:
    st.session_state.prev_heading = 0.0
if 'ins_active' not in st.session_state:
    st.session_state.ins_active = False

if 'orbit_lon' not in st.session_state:
    st.session_state.orbit_lon = -180.0

if 'true_lat' not in st.session_state:
    st.session_state.true_lat = 38.6744  
    st.session_state.true_lon = 39.1942
    
    st.session_state.lat = st.session_state.true_lat
    st.session_state.lon = st.session_state.true_lon
    
    st.session_state.last_good_lat = st.session_state.true_lat
    st.session_state.last_good_lon = st.session_state.true_lon
    
    st.session_state.snr_history = [40] * 30
    
    now = datetime.now()
    st.session_state.logs = [
        f"[{now.strftime('%H:%M:%S')}] 🚨 IŞINLANMA SPOOFING TESPİT EDİLDİ (GPS Konum Sıçraması) | Müdahale: Fiziksel veya Aerodinamik imkansızlık yakalandı. GPS engelleniyor!",
        f"[{(now - timedelta(minutes=15, seconds=32)).strftime('%H:%M:%S')}] 🛡️ JAMMING MÜDAHALESİ BAŞARILI (Filtreler Aktif) | Müdahale: Sinyal eşiği aştığında güçlendirme kalkanı ile izole edildi.",
        f"[{(now - timedelta(minutes=42, seconds=15)).strftime('%H:%M:%S')}] ⚠️ Sinyal Zayıflıyor! (%75 Sınırı Aşıldı, Filtreler Devrede) | Müdahale: Sistem Koruma Altında: Sinyal Güçlendirici hazırlanıyor..."
    ]
    
    st.session_state.attack_mode = "normal"
    st.session_state.fw_state = True
    st.session_state.auto_sim_state = False
    st.session_state.spoof_target_lat = 48.8566
    st.session_state.spoof_target_lon = 2.3522
    st.session_state.spoof_time_offset = random.choice([-8, -6, -4, 4, 6, 8])
    st.session_state.prev_attack_mode = "normal"
    st.session_state.jamming_start_time = 0.0
    st.session_state.jamming_baseline = 42.0
    st.session_state.jamming_state = "none"
    st.session_state.spoofing_start_time = 0.0
    st.session_state.spoof_type = "teleport" # varsayılan
    st.session_state.spoof_drag_lat = 0.0
    st.session_state.spoof_drag_lon = 0.0
    st.session_state.spoof_drag_speed = 50.0
    st.session_state.spoof_drag_angle = 0.0
    st.session_state.ins_duration = 0.0
    st.session_state.ins_lat = 0.0
    st.session_state.ins_lon = 0.0
    st.session_state.ins_heading = 0.0
    st.session_state.ins_speed = 0.0
    st.session_state.ins_accel = 0.0

# ==========================================
# 1.5. KONTROL GERİ ÇAĞIRIMLARI (RACE CONDITION FIX)
# ==========================================
def cb_fw():
    st.session_state.fw_state = st.session_state.fw_widget

def cb_sim():
    st.session_state.auto_sim_state = st.session_state.sim_widget

def cb_mode_normal():
    st.session_state.attack_mode = "normal"
    st.session_state.force_reset = True

def cb_mode_jamming():
    st.session_state.attack_mode = "jamming"
    st.session_state.force_reset = True

def cb_mode_spoofing():
    st.session_state.attack_mode = "spoofing"
    st.session_state.spoof_target_lat = random.uniform(20.0, 60.0)
    st.session_state.spoof_target_lon = random.uniform(-20.0, 50.0)
    st.session_state.force_reset = True

# ==========================================
# 2. YAN PANEL (GÜVENLİK DUVARI VE KONTROLLER)
# ==========================================
st.sidebar.title("🎮 Kontrol ve Simülasyon")
st.sidebar.markdown("---")

st.sidebar.subheader("🛡️ Güvenlik Duvarı Sistemi")
st.sidebar.write("Aktif edildiğinde saldırıları tespit eder ve otomatik önlemler alır.")
# Güvenlik Duvarı Aç/Kapa
firewall_active = st.sidebar.toggle("Firewall (Güvenlik Duvarı) Aktif", value=st.session_state.fw_state, key="fw_widget", on_change=cb_fw)

if firewall_active:
    st.sidebar.success("✅ Firewall AÇIK - Sistem Korunuyor")
else:
    st.sidebar.error("🚨 Firewall KAPALI - Sistem Savunmasız!")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Saldırı Simülatörü")

st.sidebar.button("✅ Normal Seyir", use_container_width=True, on_click=cb_mode_normal)
st.sidebar.button("⚡ Jamming Saldırısı", use_container_width=True, on_click=cb_mode_jamming)
st.sidebar.button("🗺️ Spoofing Saldırısı", use_container_width=True, on_click=cb_mode_spoofing)

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Otomatik Simülasyon")
auto_sim = st.sidebar.toggle("Simülasyon Modu (Otomatik Saldırı)", value=st.session_state.auto_sim_state, key="sim_widget", on_change=cb_sim)

orbit_mode = False

if "last_sim_time" not in st.session_state:
    st.session_state.last_sim_time = time.time()

if auto_sim:
    elapsed = time.time() - st.session_state.last_sim_time
    
    # Güvenlik duvarı durumuna göre simülasyon dinamikleri
    if st.session_state.attack_mode != "normal":
        if firewall_active:
            interval = 3  # FW AÇIK: Saldırı püskürtüldüğü için kısa sürer
            weights = [80, 10, 10] # Çabucak normale döner
        else:
            interval = 15 # FW KAPALI: Saldırı müdahale edilemediği için UZUN sürer
            weights = [10, 45, 45] # Saldırıda kalma ihtimali çok yüksektir
    else:
        if firewall_active:
            interval = 8  # FW AÇIK: Sistem korumalı, barış süresi daha uzun
            weights = [70, 15, 15] # Saldırı gelme sıklığı az
        else:
            interval = 5  # FW KAPALI: Sistem savunmasız, çabuk saldırı gelir
            weights = [30, 35, 35]

    if elapsed > interval:
        st.session_state.last_sim_time = time.time()
        new_mode = random.choices(["normal", "jamming", "spoofing"], weights=weights)[0]
        st.session_state.attack_mode = new_mode
        st.session_state.force_reset = True
        if new_mode == "spoofing":
            st.session_state.spoof_target_lat = random.uniform(20.0, 60.0)
            st.session_state.spoof_target_lon = random.uniform(-20.0, 50.0)

st.sidebar.markdown("---")
if st.session_state.attack_mode == "normal":
    st.sidebar.info("Geçerli Durum: **NORMAL (Tehdit Yok)**")
elif st.session_state.attack_mode == "jamming":
    st.sidebar.warning("Geçerli Durum: **JAMMING (Sinyal Boğma)**")
elif st.session_state.attack_mode == "spoofing":
    st.sidebar.error("Geçerli Durum: **SPOOFING (Sahte Konum)**")

# ==========================================
# 3. SENSÖR VERİ SİMÜLASYONU
# ==========================================
# Temel GPS sapmaları (doğal)
noise_lat = random.uniform(-0.0002, 0.0002)
noise_lon = random.uniform(-0.0002, 0.0002)

is_new_attack = (st.session_state.get("prev_attack_mode") != st.session_state.attack_mode) or st.session_state.get("force_reset", False)



if st.session_state.attack_mode == "jamming" and is_new_attack:
    st.session_state.jamming_start_time = time.time()
    st.session_state.jamming_baseline = sum(st.session_state.snr_history[-5:]) / 5.0 if len(st.session_state.snr_history) >= 5 else 42.0
    st.session_state.jamming_state = "dropping"

if st.session_state.attack_mode == "spoofing" and is_new_attack:
    st.session_state.is_teleporting = True
    st.session_state.spoofing_start_time = time.time()
    
    # %50 ihtimalle Işınlanma şoku, %50 ihtimalle İvmeli Sürüklenme saldırısı
    st.session_state.spoof_type = random.choice(["teleport", "drag"])
    
    if st.session_state.spoof_type == "drag":
        # Sürüklenme için başlangıç değerleri: Mevcut konumdan başla
        st.session_state.spoof_drag_lat = st.session_state.true_lat
        st.session_state.spoof_drag_lon = st.session_state.true_lon
        
        # Sürüklenmenin ana gidiş yönünü belirle (tamamen rastgele 360 derece bir radyan açısı başlar)
        st.session_state.spoof_drag_angle = random.uniform(0, 2 * math.pi)
        
        # İlk rastgele hedef (100-125 km / ~0.9 - 1.15 derece mesafede)
        radius_1 = random.uniform(0.9, 1.15)
        st.session_state.spoof_target_lat = st.session_state.true_lat + radius_1 * math.cos(st.session_state.spoof_drag_angle)
        st.session_state.spoof_target_lon = st.session_state.true_lon + radius_1 * math.sin(st.session_state.spoof_drag_angle)
        
        # Artan ivme için başlangıç hızı
        st.session_state.spoof_drag_speed = 1000.0 
else:
    st.session_state.is_teleporting = False

st.session_state.prev_attack_mode = st.session_state.attack_mode
st.session_state.force_reset = False

if st.session_state.attack_mode == "normal":
    raw_snr = random.uniform(38.0, 45.0)
    raw_speed = random.uniform(40.0, 45.0)
    raw_lat = st.session_state.true_lat + noise_lat
    raw_lon = st.session_state.true_lon + noise_lon

elif st.session_state.attack_mode == "jamming":
    elapsed = time.time() - st.session_state.jamming_start_time
    duration = 5.0 # 5 saniyede dibe inecek şekilde yavaş düşüş
    baseline = st.session_state.jamming_baseline
    threshold = baseline * 0.75
    
    if st.session_state.jamming_state == "dropping":
        progress = min(elapsed / duration, 1.0)
        current_snr = baseline - (progress * (baseline - 3.0))
        raw_snr = current_snr + random.uniform(-0.5, 0.5)
        
        if current_snr <= threshold:
            if firewall_active:
                st.session_state.jamming_state = "recovering" # Bir sonraki tick'te kurtaracak
            else:
                if progress >= 1.0:
                    st.session_state.jamming_state = "success"
    elif st.session_state.jamming_state == "recovering":
        st.session_state.jamming_state = "recovered"
        raw_snr = baseline + random.uniform(-1.0, 1.0)
    elif st.session_state.jamming_state == "recovered":
        raw_snr = baseline + random.uniform(-1.0, 1.0)
    elif st.session_state.jamming_state == "success":
        raw_snr = random.uniform(2.0, 6.0)

    raw_speed = random.uniform(40.0, 45.0)
    raw_lat = st.session_state.true_lat + random.uniform(-0.02, 0.02)
    raw_lon = st.session_state.true_lon + random.uniform(-0.02, 0.02)

elif st.session_state.attack_mode == "spoofing":
    raw_snr = random.uniform(52.0, 58.0) # Sahte verici bastırması
    
    if st.session_state.get("spoof_type", "teleport") == "teleport":
        # TÜR 1: Klasik Işınlanma Anı ve Orijinal Şok Hızı
        raw_lat = st.session_state.spoof_target_lat + random.uniform(-0.01, 0.01)
        raw_lon = st.session_state.spoof_target_lon + random.uniform(-0.01, 0.01)

        if st.session_state.get("is_teleporting", False):
            R = 6371.0 # Dünya yarıçapı (km)
            dlat = math.radians(raw_lat - st.session_state.true_lat)
            dlon = math.radians(raw_lon - st.session_state.true_lon)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(st.session_state.true_lat)) * math.cos(math.radians(raw_lat)) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance_km = R * c
            raw_speed = distance_km * 3600.0 # 1 saniyede gidildiği için muazzam çarpım
        else:
            raw_speed = random.uniform(85.0, 120.0)
            
    elif st.session_state.spoof_type == "drag":
        # TÜR 2: Artan İvmeyle Harita Üzerinde Rastgele Kayarak Sürüklenme
        lat_diff = st.session_state.spoof_target_lat - st.session_state.spoof_drag_lat
        lon_diff = st.session_state.spoof_target_lon - st.session_state.spoof_drag_lon
        dist = max((lat_diff**2 + lon_diff**2)**0.5, 0.0001)
        
        # OVERSHOOT (Git-Gel/Titreme) Hata Gidericisi: Adım büyüklüğünü hedefe varmadan ÖNCE hesapla
        step = (st.session_state.spoof_drag_speed / 3600.0) / 111.0 
        
        # Eğer kalan mesafe, o andaki devasa hız adımından kısaysa hedefi atlayıp geri dönmek yerine direkt re-roll yap
        if dist <= step * 1.5 or dist < 0.05: 
            # Git-gel yapmaması (geri dönmemesi) için var olan açıyı maksimum +-60 derece saptırarak İLERİ sürüklenmeye devam ettir
            st.session_state.spoof_drag_angle += random.uniform(-math.pi/3, math.pi/3)
            
            # 2. noktadan itibaren her yeni hedef tamamen 100-125km (0.9 - 1.15 derece) menzilli olacak
            radius_2 = random.uniform(0.9, 1.15)
            
            st.session_state.spoof_target_lat = st.session_state.spoof_drag_lat + radius_2 * math.cos(st.session_state.spoof_drag_angle)
            st.session_state.spoof_target_lon = st.session_state.spoof_drag_lon + radius_2 * math.sin(st.session_state.spoof_drag_angle)
            
            lat_diff = st.session_state.spoof_target_lat - st.session_state.spoof_drag_lat
            lon_diff = st.session_state.spoof_target_lon - st.session_state.spoof_drag_lon
            dist = max((lat_diff**2 + lon_diff**2)**0.5, 0.0001)
            
        # İvme Çarpanı: Orta-Agresif tırmanma
        st.session_state.spoof_drag_speed *= random.uniform(1.20, 1.40)
        if st.session_state.spoof_drag_speed > 50000.0:
            st.session_state.spoof_drag_speed = 50000.0
        
        st.session_state.spoof_drag_lat += (lat_diff / dist) * step
        st.session_state.spoof_drag_lon += (lon_diff / dist) * step
        
        raw_lat = st.session_state.spoof_drag_lat
        raw_lon = st.session_state.spoof_drag_lon
        raw_speed = st.session_state.spoof_drag_speed

# SNR geçmişini tut (Grafik için)
st.session_state.snr_history.append(raw_snr)
if len(st.session_state.snr_history) > 30:
    st.session_state.snr_history.pop(0)

# ==========================================
# 4. TEHDİT ANALİZİ VE GÜVENLİK DUVARI MÜDAHALESİ
# ==========================================
# 4.1 FİZİKSEL VE AERODİNAMİK KONTROLLER (KİNEMATİK ANALİZ)
current_acceleration = raw_speed - st.session_state.prev_speed
st.session_state.prev_speed = raw_speed
st.session_state.acceleration = current_acceleration # Ekranda göstermek için kaydet

# Yön (Heading) hesaplaması: atan2(∆Boylam, ∆Enlem)
lat_diff = raw_lat - st.session_state.prev_lat
lon_diff = raw_lon - st.session_state.prev_lon
current_heading = st.session_state.prev_heading
if abs(lat_diff) > 0.000001 or abs(lon_diff) > 0.000001:
    current_heading = math.degrees(math.atan2(lon_diff, lat_diff))

# İki açısal yön arasındaki gerçek fark (0-180 derece)
heading_diff = abs(current_heading - st.session_state.prev_heading)
if heading_diff > 180.0:
    heading_diff = 360.0 - heading_diff

st.session_state.prev_heading = current_heading
st.session_state.prev_lat = raw_lat
st.session_state.prev_lon = raw_lon

# 4.2 TESPİT MANTIĞI
attack_type = "NORMAL"
detailed_reason = ""

if st.session_state.attack_mode == "jamming":
    baseline = st.session_state.jamming_baseline
    if st.session_state.jamming_state == "recovered":
        attack_type = "JAMMING_RECOVERED"
    elif st.session_state.jamming_state == "success":
        attack_type = "JAMMING"
        detailed_reason = "Sinyal Tamamen Kayboldu"
    elif st.session_state.jamming_state in ["dropping", "recovering"]:
        if raw_snr <= (baseline * 0.75):
            attack_type = "JAMMING_WARNING"
            detailed_reason = "Sinyal Seviyesi Kritik Sınırda (%75)"
        
# A. Konum Şoku (Işınlanma) Tespiti
if abs(raw_lat - st.session_state.last_good_lat) > 0.1:
    attack_type = "SPOOFING"
    detailed_reason = "GPS Konum Sıçraması (Işınlanma)"
# B. Kinematik (G-Force) İmkansızlık Tespiti: > 15 km/sa ani ivme sıçraması
elif abs(current_acceleration) > 15.0:
    attack_type = "SPOOFING"
    detailed_reason = f"Fiziksel İmkansızlık (Ani İvme: {current_acceleration:+.1f} km/s)"
# C. Aerodinamik Tutarsızlık (Keskin Zikzak): > 50km/s hızda tek seferde >45 derece ani sağ/sol manevra
elif heading_diff > 45.0 and raw_speed > 50.0:
    attack_type = "SPOOFING"
    detailed_reason = f"Aerodinamik Tutarsızlık (Keskin Dönüş: {heading_diff:.0f}°)"

msg = "✅ Çevre ve Sinyaller Temiz."
action_taken = "Gerekli Değil."

final_speed = raw_speed
final_snr = raw_snr

# Firewall Karar Mekanizması
if attack_type == "NORMAL":
    final_lat, final_lon = raw_lat, raw_lon
    # Normal durumdayken "Güvenli Son Konum"u güncelle
    st.session_state.last_good_lat = raw_lat
    st.session_state.last_good_lon = raw_lon

elif attack_type == "JAMMING_WARNING":
    if firewall_active:
        msg = "⚠️ Sinyal Zayıflıyor! (%75 Sınırı Aşıldı, Filtreler Devredek)"
        action_taken = "Sistem Koruma Altında: Sinyal Güçlendirici hazırlanıyor..."
    else:
        msg = "⚠️ Sinyal Hızla Düşüyor! Lütfen Güvenlik Duvarını AÇIN!"
        action_taken = "Sistem Savunmasız: Bekleniyor..."
    final_lat, final_lon = raw_lat, raw_lon

elif attack_type == "JAMMING":
    msg = "🚨 JAMMING SALDIRISI GERÇEKLEŞTİ!"
    action_taken = "Firewall KAPALI: Navigasyon bulanıklaşıyor ve koptu."
    final_lat, final_lon = raw_lat, raw_lon

elif attack_type == "JAMMING_RECOVERED":
    msg = "🛡️ JAMMING MÜDAHALESİ BAŞARILI (Filtreler Aktif)"
    action_taken = "Sinyal eşiği aştığında güçlendirme kalkanı ile izole edildi."
    final_lat, final_lon = st.session_state.last_good_lat, st.session_state.last_good_lon

elif attack_type == "SPOOFING":
    if st.session_state.is_teleporting:
        msg = f"🚨 IŞINLANMA SPOOFING TESPİT EDİLDİ ({detailed_reason})"
    else:
        msg = f"🚨 SÜRÜKLENME SPOOFING TESPİT EDİLDİ ({detailed_reason})"
    
    if firewall_active:
        action_taken = "Fiziksel veya Aerodinamik imkansızlık yakalandı. GPS engelleniyor!"
        
        elapsed = time.time() - st.session_state.get("spoofing_start_time", 0.0)
        is_teleport = (st.session_state.get("spoof_type") == "teleport")
        
        if is_teleport:
            # INS Otopilot Devreye Giriyor
            if not st.session_state.ins_active and elapsed < 1.0: # Saldırı yeni başladıysa
                st.session_state.ins_active = True
                st.session_state.ins_duration = random.uniform(3.0, 5.0)
                st.session_state.ins_lat = st.session_state.last_good_lat
                st.session_state.ins_lon = st.session_state.last_good_lon
                st.session_state.ins_speed = st.session_state.prev_speed
                st.session_state.ins_accel = st.session_state.acceleration
                st.session_state.ins_heading = random.uniform(0, 2*math.pi) # Konumu sakladığımız veri olmadığı için rastgele varsayılan yön seçiyoruz
                
            if st.session_state.ins_active and elapsed < st.session_state.ins_duration:
                msg = "🚨 UYDU ÇEVRİMDIŞI! (Işınlanma Şoku Tespit Edildi)"
                action_taken = "INS Otopilot (Kör Uçuş) Aktif: Araç son ivme ve vektörlere göre tahmini rotasında ilerliyor..."
                
                # Fizik motoru: Son ivmeye göre hızı arttır/azalt (ö.r. yavaşlayan araç yavaşlamaya devam eder)
                st.session_state.ins_speed += st.session_state.ins_accel
                st.session_state.ins_speed = max(0.0, min(st.session_state.ins_speed, 120.0)) # Saçmalamaması için fizik limiti
                
                step = (st.session_state.ins_speed / 3600.0) / 111.0
                st.session_state.ins_lat += step * math.cos(st.session_state.ins_heading)
                st.session_state.ins_lon += step * math.sin(st.session_state.ins_heading)
                
                final_lat, final_lon = st.session_state.ins_lat, st.session_state.ins_lon
                final_speed = st.session_state.ins_speed
                final_snr = 0.0 # Uydu bağlantısı yok
            else:
                if st.session_state.ins_active:
                    st.session_state.ins_active = False # Kurtarma tamamlandı, bayrağı indir
                    st.session_state.last_good_lat = st.session_state.ins_lat
                    st.session_state.last_good_lon = st.session_state.ins_lon
                    
                msg = "🟢 UYDU BAĞLANTISI GERİ GELDİ (Otopilottan Çıkıldı)"
                action_taken = "GPS senkronize edildi, kontroller normale döndü, sahte değerler reddedildi."
                final_lat, final_lon = st.session_state.last_good_lat, st.session_state.last_good_lon
                final_speed = random.uniform(40.0, 45.0)
                final_snr = random.uniform(38.0, 45.0)
                    
        else: # Sürüklenme saldırısı gibi kurtarma senaryoları (Sistem kapatılmaz)
            msg = f"🚨 SÜRÜKLENME SPOOFING TESPİT EDİLDİ ({detailed_reason})"
            action_taken = "Sistem Korunuyor: Sahte GPS reddedildi, Filtreler devrede..."
            final_lat, final_lon = st.session_state.last_good_lat, st.session_state.last_good_lon # Konum her zaman güvende sabitlenir
            
            recovery_duration = 3.0 # 3 saniyelik bir filtreleme/sönümleme animasyonu
            
            if elapsed < 0.5:
                # Sürüklenme ivmesinin anlık şoku
                final_speed = raw_speed
                final_snr = raw_snr
            elif elapsed < recovery_duration:
                # Değerlerin yavaşça normale indirilmesi
                progress = (elapsed - 0.5) / (recovery_duration - 0.5)
                final_speed = raw_speed - (raw_speed - 42.0) * progress
                final_snr = raw_snr - (raw_snr - 40.0) * progress
            else:
                final_speed = random.uniform(40.0, 45.0) # Tamamen izole güvenli hız
                final_snr = random.uniform(38.0, 45.0) # Tamamen filtrelenmiş SNR
    else:
        msg = "🚨 SPOOFING SALDIRISI GERÇEKLEŞTİ!"
        action_taken = "Firewall KAPALI: Araç sahte konuma doğru çekiliyor!"
        final_lat, final_lon = raw_lat, raw_lon # Araç kandırıldı

# Logları Listeye Ekleme
if attack_type != "NORMAL":
    is_new = True
    if len(st.session_state.logs) > 0:
        if msg in st.session_state.logs[0] and action_taken in st.session_state.logs[0]:
            is_new = False
            
    if is_new:
        timestamp = time.strftime('%H:%M:%S')
        log_text = f"[{timestamp}] {msg} | Müdahale: {action_taken}"
        st.session_state.logs.insert(0, log_text)
        
        # Olay anında sağ alttan (veya ekrandan) fırlayan siber ihlal uyarısı
        if auto_sim and not firewall_active:
            if attack_type in ["JAMMING", "SPOOFING"]:
                st.toast("🚨 SİBER İHLAL: Sistem Çöktü! Navigasyon Modülü Devredışı!", icon="☠️")

# ==========================================
# 5. DASHBOARD (ANA EKRAN) GÖRÜNÜMÜ
# ==========================================
st.title("🛰️ Siber Güvenlik ve Navigasyon Paneli (SIEM)")

# A. ÜST BİLGİ KARTLARI
col_time, col1, col2, col3 = st.columns(4)
with col_time:
    if st.session_state.get("ins_active", False):
        st.metric(label="🤖 OTOPİLOT DEVREDE (INS)", value="---", delta="GPS BAĞLANTISI KOPTU", delta_color="inverse")
    elif attack_type == "SPOOFING" and not firewall_active:
        # Fiziksel sahte konuma göre anlık saat kayması tahmini (Sürüklenirken kayarak, ışınlanırken aniden değişir)
        dynamic_offset_hours = (raw_lon - st.session_state.true_lon) / 15.0
        fake_time = datetime.now() + timedelta(hours=dynamic_offset_hours)
        # Delta metni sayı ile başlayınca hatasız aşağı/yukarı ok atar.
        st.metric(label="⚠️ Sahte Saat (Spoofed)", value=fake_time.strftime("%H:%M:%S"), delta=f"{dynamic_offset_hours:.1f} Saat", delta_color="inverse")
    else:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.metric(label="🕒 Yerel Saat", value=current_time)
with col1:
    if st.session_state.get("ins_active", False):
        st.metric(label="📡 Anlık Sinyal Gücü (SNR)", value="---", delta="Uydu Sinyali Yok", delta_color="inverse")
    else:
        st.metric(label="📡 Anlık Sinyal Gücü (SNR)", value=f"{final_snr:.1f} dB", delta=f"{final_snr - 40:.1f} dB", delta_color="inverse")
with col2:
    if st.session_state.get("ins_active", False):
        st.metric(label="🏎️ Hesaplanan Hız (Kör Uçuş)", value="---", delta="Hız Sensörü Çevrimdışı", delta_color="inverse")
    else:
        st.metric(label="🏎️ Hesaplanan Hız", value=f"{final_speed:.1f} km/sa")
with col3:
    if firewall_active:
        st.metric(label="🛡️ Güvenlik Duvarı Durumu", value="AÇIK", delta="Koruma Aktif", delta_color="normal")
    else:
        st.metric(label="⚠️ Güvenlik Duvarı Durumu", value="KAPALI!", delta="-Savunmasız", delta_color="normal")

st.markdown("---")

# B. HARİTA VE OLAY DETAYLARI
col_map, col_info = st.columns([2, 1])

with col_map:
    st.subheader("🗺️ Canlı Uydu Takibi")
    
    map_data = []
    
    if orbit_mode:
        # 🛰️ UYDU YÖRÜNGE ŞOVU MODU
        st.session_state.orbit_lon += 5.0 # Çok hızlı boylam değişimi
        if st.session_state.orbit_lon > 180.0:
            st.session_state.orbit_lon = -180.0
            
        # Dünyayı saran dalgalı sinüs yörüngesi
        orbit_lat = 45.0 * math.sin(math.radians(st.session_state.orbit_lon * 3))
        
        # Diğer tüm araçları ezip sadece devasa Uydumuzu global haritada çizdiriyoruz
        map_data.append({"lat": orbit_lat, "lon": st.session_state.orbit_lon, "color": "#00ffff", "size": 4000})
        zoom_level = 1
    else:
        # 🚗 NORMAL ARAÇ / SİBER SALDIRI MODLARI
        if attack_type == "NORMAL":
            map_data.append({"lat": final_lat, "lon": final_lon, "color": "#00ff00", "size": 250})
            zoom_level = 15
            
        elif attack_type == "JAMMING_RECOVERED":
            map_data.append({"lat": final_lat, "lon": final_lon, "color": "#00ff00", "size": 250})
            map_data.append({"lat": raw_lat, "lon": raw_lon, "color": "#ffff0088", "size": 6000}) 
            zoom_level = 12
            
        elif attack_type == "JAMMING_WARNING":
            map_data.append({"lat": final_lat, "lon": final_lon, "color": "#ffaa00", "size": 600}) 
            zoom_level = 12
            
        elif attack_type == "JAMMING":
            map_data.append({"lat": final_lat, "lon": final_lon, "color": "#ff000088", "size": 6000}) 
            zoom_level = 12
            
        elif attack_type == "SPOOFING":
            if firewall_active:
                if st.session_state.get("ins_active", False):
                    map_data.append({"lat": final_lat, "lon": final_lon, "color": "#0088ff", "size": 350})
                else:
                    map_data.append({"lat": final_lat, "lon": final_lon, "color": "#00ff00", "size": 250})
                    
                map_data.append({"lat": raw_lat, "lon": raw_lon, "color": "#ffaa00", "size": 600}) 
                zoom_level = 3 
            else:
                map_data.append({"lat": final_lat, "lon": final_lon, "color": "#ff0000", "size": 400}) 
                zoom_level = 4 

    # Veriyi DataFrame'e ekle ve çizdir
    st.map(pd.DataFrame(map_data), latitude='lat', longitude='lon', color='color', size='size', zoom=zoom_level)

with col_info:
    st.subheader("🤖 Karar ve Tehdit Merkezi")
    
    if attack_type == "NORMAL":
        st.success("Sistem temiz. GPS Sinyalleri stabilize edildi.")
    else:
        if firewall_active:
            st.warning(msg)
            st.info(f"**⚡ Hızlı Karar (Firewall):**\n{action_taken}")
        else:
            st.error(msg)
            st.error(f"**💀 Kritik Etki:**\n{action_taken}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Sinyal (SNR) Grafiği")
    st.line_chart(st.session_state.snr_history, height=180)

# C. LOGLAR
st.markdown("### 📋 Canlı Sistem Logları")

log_box = st.container(height=400)
with log_box:
    if len(st.session_state.logs) == 0:
        st.info("Henüz kaydedilmiş bir siber vaka yok.")
    else:
        for log_item in st.session_state.logs:
            display_str = log_item
            if "| Müdahale:" in display_str:
                msg_part, action_part = display_str.split("| Müdahale:", 1)
                st.markdown(f"<div style='font-size: 1.3rem; font-weight: bold; margin-bottom: 8px;'>🚨 {msg_part.strip()}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 1.15rem; margin-left: 10px; border-left: 4px solid #28a745; padding-left: 12px; color: #dddddd;'><i>Müdahale: {action_part.strip()}</i></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='font-size: 1.3rem; font-weight: bold;'>{display_str}</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 15px 0; border-top: 1px solid #444;'>", unsafe_allow_html=True)
            
# 5. ZAMAN DÖNGÜSÜ (Simülasyon hızı)
time.sleep(1)
st.rerun()

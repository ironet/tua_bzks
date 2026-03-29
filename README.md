# BKZS / GNSS Sinyal Doğrulama ve Anti-Spoofing Arayüzü 🛰️🛡️

Bu proje, **TUA AstroHackathon** kapsamında geliştirilmiş bir GNSS (Küresel Navigasyon Uydu Sistemi) sinyal doğrulama ve siber tehdit anomali tespiti sistemidir.

Tamamen bağımsız bir **SIEM (Güvenlik Bilgi ve Olay Yönetimi)** tarzı web paneline (Dashboard) sahip olan bu uygulama, GPS sinyallerine yapılan Spoofing (Yanıltma) ve Jamming (Karıştırma) saldırılarını tespit edip otomatik olarak önlemler alır (Firewall simülasyonu).

## 🌐 Canlı Demo 

Projeyi bilgisayarınıza kurmadan, doğrudan web tarayıcınız üzerinden test etmek için aşağıdaki bağlantıya tıklayabilirsiniz:

👉 **[Uygulamayı Canlı Olarak Test Etmek İçin Tıklayın](https://tua-test-bzks.streamlit.app/)**

## 🚀 Özellikler

- **Modern Web Arayüzü (Streamlit):** İnteraktif, hareketli ve anlık siber olay güncelleyici kontrol paneli (Dashboard/C2 Center).
- **Anomali ve Saldırı Tespiti:**
  - **Spoofing Tespiti:** Mantıksız konum sıçramaları (Teleport) ve ani hız/ivme değişimlerinin fiziksel ve aerodinamik algılanması.
  - **Jamming Tespiti:** Uydu (SNR) sinyal gücünün aniden düşmesinin algılanması ve Firewall ile filtreleme.
  - **Sürüklenme (Drag) Saldırıları:** Araç hedeflerken veya kayarak sürüklenirken tespit etme.
- **Güvenlik Duvarı (Firewall) ve Otopilot:** Korsan sinyalleri yakaladığında sahte değerleri reddeden INS (Kör Uçuş) Otopilot devresi kurgusu.
- **Otomatik Simülasyon Senaryoları:** Jüri sunumları için tek tuşla rastgele ataklar üreten akıllı "Otomatik Simülasyon"

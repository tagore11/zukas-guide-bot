# KaşAgora Telegram Botu

Kaş rehberi + ZuKaş 2026 FAQ botu.
Hem website widget hem grup içi kullanım için tasarlandı.

---

## KURULUM (5 dakika)

### 1. BotFather'dan token al
```
@BotFather → /newbot
İsim: KaşAgora Bot
Username: kasagorabot (veya boşsa başka bir şey)
→ Token kopyala
```

### 2. .env dosyası oluştur
```bash
cd ~/Desktop/zukas-2026/bot/
cp .env.example .env
# .env dosyasını aç, token'ı yapıştır
```

### 3. Bağımlılıkları yükle
```bash
pip install -r requirements.txt
```

### 4. Çalıştır
```bash
python kas_bot.py
```

---

## GRUBA EKLEME

Botu bir Telegram grubuna admin olarak ekle:
- Grup → ... → Add Member → @kasagorabot
- Ayarlar → Admins → botu admin yap (sadece mesaj gönderme izni yeterli)

Grup içinde kullanım:
- `ulaşım`, `dolmuş`, `minibüs` → Ulaşım bilgisi verir
- `yemek`, `restaurant`, `cafe` → Restoran önerileri
- `zukas`, `etkinlik`, `başvur` → ZuKaş 2026 bilgisi
- `acil`, `112`, `ambulans` → Acil numaralar

---

## WEBSITE ENTEGRASYONU

Lovable'da zukascity.com'a bot linkini eklemek için şu bloğu yerleştir:

```html
<!-- Telegram Bot CTA -->
<a href="https://t.me/kasagorabot" target="_blank"
   style="display:inline-flex;align-items:center;gap:8px;
          background:#0088cc;color:white;padding:12px 24px;
          border-radius:8px;text-decoration:none;font-weight:600;">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.833.941z"/>
  </svg>
  Kaş Rehber Botu
</a>
```

---

## KOMUTLAR

| Komut | Açıklama |
|-------|----------|
| `/start` | Ana menü |
| `/help` | Yardım |
| `/zukas` | ZuKaş 2026 bilgisi |
| `/ulasim` | Ulaşım rehberi |
| `/yemek` | Restoran önerileri |
| `/konaklama` | Konaklama |
| `/tekne` | Tekne turları |
| `/cowork` | Çalışma alanları |
| `/acil` | Acil numaralar |

---

## DEPLOYMENT (Sunucuya taşıma)

Railway.app veya Render.com ile ücretsiz hosting:

**Railway:**
```bash
railway login
railway new
railway up
# Environment variable: BOT_TOKEN=xxx
```

**Manuel (VPS):**
```bash
nohup python kas_bot.py &
# veya systemd service olarak kur
```

---

## GRUPLARA EKLEME SIRASI

1. ZuKaş Residency (2994791786) — Priority 1
2. Web3 META Hub — Priority 2
3. Samir'in Kaş grubu (19.6K) — Samir onaylarsa Priority 3

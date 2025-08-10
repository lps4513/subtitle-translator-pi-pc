````markdown
# Subtitle Translator (PC & Raspberry Pi)

Ez a projekt automatikusan **angol nyelvű filmekhez** készít feliratot (`.srt`), majd **DeepL API** segítségével magyarra fordítja.

Két platformon használható:
- 💻 **Windows PC** – gyorsabb feldolgozás
- 🍓 **Raspberry Pi 4 / 5** – alacsony fogyasztás, lassabb, de hordozható megoldás

---

## 1. Előfeltételek

- **Python 3.11+**
- **ffmpeg** telepítve és elérhető a `PATH`-ban
- **DeepL API kulcs** (Free vagy Pro)
- Internetkapcsolat

---

## 2. Telepítés

### 📌 Windows PC
1. **ffmpeg letöltése és telepítése**
   - Töltsd le innen: https://ffmpeg.org/download.html  
   - Csomagold ki pl. `C:\ffmpeg` mappába.
   - Add hozzá a `PATH` környezeti változóhoz:
     ```
     C:\ffmpeg\bin
     ```
   - Teszteld:
     ```powershell
     ffmpeg -version
     ```

2. **Projekt klónozása**
   ```powershell
   git clone https://github.com/lps5413/subtitle-translator-pi-pc.git
   cd subtitle-translator-pi-pc
````

3. **Virtuális környezet létrehozása**

   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **DeepL API kulcs beállítása**

   * Hozz létre `.env` fájlt:

     ```
     DEEPL_API_KEY=itt_a_sajat_kulcsod
     ```

---

### 📌 Raspberry Pi 4 / 5

1. **ffmpeg telepítése**

   ```bash
   sudo apt update
   sudo apt install ffmpeg python3-venv git -y
   ```

2. **Projekt klónozása**

   ```bash
   git clone https://github.com/lps5413/subtitle-translator-pi-pc.git
   cd subtitle-translator-pi-pc
   ```

3. **Virtuális környezet**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **DeepL API kulcs**

   ```bash
   echo "DEEPL_API_KEY=itt_a_sajat_kulcsod" > .env
   ```

---

## 3. Használat

1. **Film konvertálása és felirat készítése**

   ```bash
   python subtitle_translator.py mymovie.mp4
   ```

   Ez létrehozza:

   * `subtitle_en.srt` → angol felirat
   * `subtitle_hu.srt` → magyar fordítás

2. **Fordítás működése**

   * A DeepL API hívások soronként történnek (limit figyelembe véve)
   * Ha 429-es hiba jön ("Too Many Requests"), a program automatikusan várakozik

---

## 4. Tippek

* **Windows-on** gyorsabb a feldolgozás (PC CPU teljesítménye miatt).
* **Pi-n** kisebb filmekkel érdemes kísérletezni.
* API kulcsot **ne tölts fel GitHubra**! `.env` fájl a `.gitignore`-ban van.

---

## 5. Licenc

MIT

```

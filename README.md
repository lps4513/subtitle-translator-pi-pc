# Subtitle Translator (Pi + PC)

Platformfüggetlen Python eszköz: angol felirat automatikus generálása `faster-whisper`-rel és részleges, batch-elt DeepL fordítás annak érdekében, hogy elkerüljük az API-korlátozásokat. A szkript automatikusan és folyamatosan ír kettős (angol + magyar) `.srt`-t.

## Fő jellemzők

- Ugyanaz a kód fut Raspberry Pi-n és PC-n.
- GPU-detektálás (ha NVIDIA CUDA elérhető, a transzkripció gyorsabban fut).
- Feldolgozás közbeni, részleges DeepL fordítás (batch méret paraméterezhető).
- Parancssori argumentumok: bemenet, modell, batch méret, fordítás be/ki, stb.

## Követelmények

- Python 3.8+
- 64-bit OS Raspberry Pi esetén (Pi4/5)
- DeepL API kulcs (lásd `.env.example`)

Telepítés:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Állítsd be a környezeti változót (másold a `.env.example`-t `.env`-re):

```
DEEPL_API_KEY=your_deepl_auth_key_here
```

## Használat

Alap példa:

```bash
python subtitle_translator.py --input film.mp4
```

Példa paraméterekkel:

```bash
python subtitle_translator.py --input film.mp4 --model base --batch-size 8 --no-translate False --output mymovie
```

A kimenet alapértelmezés szerint: `mymovie_both.srt` (angol sor, alatta magyar sorok). Ha `--no-translate` használod, csak angol `.srt` készül.

## Licenc

MIT
________________________________________
requirements.txt
faster-whisper
srt
requests
python-dotenv
________________________________________
.env.example
# Másold ide a DeepL kulcsodat és ments .env néven
DEEPL_API_KEY=your_deepl_auth_key_here
________________________________________
.gitignore
venv/
__pycache__/
*.pyc
.env
*.wav
*.log
________________________________________

#!/usr/bin/env python3
"""
subtitle_translator.py

Platformfüggetlen szkript Raspberry Pi-n és PC-n: transcribe (faster-whisper)
és közben batch-elt DeepL fordítás, kétnyelvű .srt írás.

Használat: python subtitle_translator.py --input film.mp4
"""

import os
import sys
import argparse
import time
import math
import subprocess
from pathlib import Path
from datetime import timedelta

try:
    from faster_whisper import WhisperModel
except Exception as e:
    print("ERROR: faster_whisper nem található. Telepítsd: pip install faster-whisper")
    raise

import srt
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

# Default settings
DEFAULT_MODEL = "small"
DEFAULT_BATCH_SIZE = 8
DEFAULT_WAIT_ON_429 = 2.0  # másodperc, exponenciális backoff alap

""""
def extract_audio(video_path: Path, audio_path: Path):
    #"Kivonja a hangot ffmpeg-pel (mono, 16kHz)"

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ac", "1", "-ar", "16000", "-vn", str(audio_path)
    ]
    print("🔊 Hang kinyerése... (ffmpeg)")
    # Megmutatjuk az ffmpeg outputot mert hasznos a progresshez
    subprocess.run(cmd, check=True)
"""

def extract_audio(video_file, audio_file="audio.wav"):
    os.system(f"ffmpeg -y -i {video_file} -ac 1 -ar 16000 -vn {audio_file}")



def detect_device():
    """Megpróbáljuk megállapítani, hogy van-e CUDA elérhető (PC-n), vagy CPU-n futunk."""
    device = "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
    except Exception:
        # torch hiánya nem hiba, csak CPU-t választunk
        device = "cpu"
    print(f"🖥️  Eszköz kiválasztva: {device}")
    return device


def translate_texts_deepl(texts, target_lang="HU"):
    """Batch fordítás DeepL API-val. texts: list[str]. Visszatér list[str]."""
    if not DEEPL_API_KEY:
        raise RuntimeError("DEEPL_API_KEY nincs beállítva. Másold .env-ből a kulcsot.")

    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # DeepL fogad listát 'text' kulccsal többször szerepelhet
    data = [ ("auth_key", DEEPL_API_KEY), ("target_lang", target_lang) ]
    for t in texts:
        data.append(("text", t))

    backoff = DEFAULT_WAIT_ON_429
    while True:
        resp = requests.post(url, data=data)
        if resp.status_code == 429:
            print(f"⚠️  DeepL rate limit (429). Várakozás {backoff}s..." )
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue
        resp.raise_for_status()
        j = resp.json()
        # DeepL visszaad egy 'translations' listát, de amikor több text van,
        # az összes fordítás a translations mezőben jelenik meg sorrendben.
        translations = []
        for elem in j.get("translations", []):
            translations.append(elem.get("text", ""))
        return translations


def write_bilingual_srt_segment(f, index, start_s, end_s, en_text, hu_text=None):
    """Kiír egy SRT bejegyzést angol sorral és opcionálisan magyar sorral alatta."""
    start = str(timedelta(seconds=start_s))
    end = str(timedelta(seconds=end_s))
    # srt pontos formátum: HH:MM:SS,mmm -> a timedelta str adja 'H:MM:SS.sssss'
    # egyszerűsítünk: használjuk a srt modul formátumát
    sub = srt.Subtitle(index=index,
                       start=timedelta(seconds=start_s),
                       end=timedelta(seconds=end_s),
                       content=en_text + ("\n" + hu_text if hu_text else ""))
    f.write(srt.compose([sub]))


def transcribe_and_translate(args):
    video = Path(args.input)
    if not video.exists():
        print("Hiba: bemeneti fájl nem található:", video)
        sys.exit(1)

    base_name = args.output if args.output else video.stem
    audio = video.with_suffix('.wav')
    srt_out = Path(f"{base_name}_both.srt") if not args.output else Path(f"{args.output}_both.srt")
    srt_en_only = Path(f"{base_name}_en.srt")

    # 1) hang kinyerése
    extract_audio(video, audio)

    # 2) modell betöltése és eszköz detektálása
    device = detect_device()
    compute_type = "int8" if device == "cpu" else None
    print(f"🔎 Modell: {args.model}, compute_type={compute_type}")
    model = WhisperModel(args.model, device=device, compute_type=compute_type)

    # 3) transcribe -> streaming mód: gyűjtünk batch-eket és fordítunk
    index = 1
    batch = []  # list of (start, end, text)
    batch_size = args.batch_size

    # Nyitjuk a fájlt folyamatos írásra
    with open(srt_out, 'w', encoding='utf-8') as f_out, open(srt_en_only, 'w', encoding='utf-8') as f_en:
        print("🧾 Transzkripció és részleges fordítás..." )
        segments, info = model.transcribe(str(audio))
        for seg_i, segment in enumerate(segments, start=1):
            start_s = segment.start
            end_s = segment.end
            en_text = segment.text.strip()

            # írjuk az angol-only srt-t is
            write_bilingual_srt_segment(f_en, index, start_s, end_s, en_text, None)

            batch.append((index, start_s, end_s, en_text))
            index += 1

            # ha batch tele vagy ha a szegmens hossza nagy (biztonság)
            if len(batch) >= batch_size:
                if not args.no_translate:
                    texts = [b[3] for b in batch]
                    try:
                        translations = translate_texts_deepl(texts, target_lang=args.target_lang)
                    except Exception as e:
                        print("⚠️  Fordítási hiba, kiírom csak az angolt:", e)
                        translations = [None] * len(texts)
                    # írjuk ki a kétnyelvű bejegyzéseket
                    for (idx, sst, est, ent), hu in zip(batch, translations):
                        write_bilingual_srt_segment(f_out, idx, sst, est, ent, hu)
                else:
                    for (idx, sst, est, ent) in batch:
                        write_bilingual_srt_segment(f_out, idx, sst, est, ent, None)
                # ürítjük a batch-et
                batch = []

        # a maradék batch feldolgozása
        if batch:
            if not args.no_translate:
                texts = [b[3] for b in batch]
                try:
                    translations = translate_texts_deepl(texts, target_lang=args.target_lang)
                except Exception as e:
                    print("⚠️  Fordítási hiba a végén, csak angol lesz:", e)
                    translations = [None] * len(texts)
                for (idx, sst, est, ent), hu in zip(batch, translations):
                    write_bilingual_srt_segment(f_out, idx, sst, est, ent, hu)
            else:
                for (idx, sst, est, ent) in batch:
                    write_bilingual_srt_segment(f_out, idx, sst, est, ent, None)

    # 4) Takarítás
    try:
        if args.keep_audio:
            print(f"🔔 Hangfájl megtartva: {audio}")
        else:
            audio.unlink()
    except Exception:
        pass

    print(f"✅ Kész: angol felirat: {srt_en_only}, kétnyelvű: {srt_out}")


def parse_args():
    p = argparse.ArgumentParser(description="Transcribe and translate subtitles (faster-whisper + DeepL)")
    p.add_argument('--input', '-i', required=True, help='Bemeneti videófájl (mp4, mkv, stb.)')
    p.add_argument('--model', default=DEFAULT_MODEL, help='Whisper model (tiny, base, small, medium, ... )')
    p.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Hány szegmens fordítódjon egyszerre')
    p.add_argument('--no-translate', action='store_true', help='Ne fordítsa (csak angol .srt)')
    p.add_argument('--output', '-o', help='Kimeneti alapnév (alap: bemeneti fájlnév)')
    p.add_argument('--keep-audio', action='store_true', help='Ne törölje a kinyert audio fájlt')
    p.add_argument('--target-lang', default='HU', help='Célnyelv a DeepL-hez (pl. HU)')
    return p.parse_args()


def main():
    args = parse_args()
    transcribe_and_translate(args)


if __name__ == '__main__':
    main()

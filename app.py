from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
from gtts import gTTS
import gtts.lang
import os
import re
import winocr

app = Flask(__name__, static_folder='.')
CORS(app)

# Standard Grade 1 and Grade 2 Braille Mappings
BRAILLE_LETTERS = {
    'a': 1, 'b': 3, 'c': 9, 'd': 25, 'e': 17, 'f': 11, 'g': 27, 'h': 19, 'i': 10, 'j': 26,
    'k': 5, 'l': 7, 'm': 13, 'n': 29, 'o': 21, 'p': 15, 'q': 31, 'r': 23, 's': 14, 't': 30,
    'u': 37, 'v': 39, 'w': 58, 'x': 45, 'y': 61, 'z': 53
}
DIGIT_MAP = {
    'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5',
    'f': '6', 'g': '7', 'h': '8', 'i': '9', 'j': '0'
}
REV_DIGIT_MAP = {v: k for k, v in DIGIT_MAP.items()}

# Punctuation to Braille Unicode offsets
PUNCT_MAP = {
    chr(0x2800 + 50): '.',
    chr(0x2800 + 2): ',',
    chr(0x2800 + 6): ';',
    chr(0x2800 + 18): ':',
    chr(0x2800 + 38): '?',
    chr(0x2800 + 22): '!',
    chr(0x2800 + 36): '-',
    chr(0x2800 + 4): "'",
    chr(0x2800 + 54): '"',
    chr(0x2800): ' ',
    ' ': ' '
}
REV_PUNCT_MAP = {
    '.': chr(0x2800 + 50),
    ',': chr(0x2800 + 2),
    ';': chr(0x2800 + 6),
    ':': chr(0x2800 + 18),
    '?': chr(0x2800 + 38),
    '!': chr(0x2800 + 22),
    '-': chr(0x2800 + 36),
    "'": chr(0x2800 + 4),
    '"': chr(0x2800 + 54),
    ' ': '⠀'
}

# Common Grade 2 Braille Contractions (Words & Letter Combos)
CONTRACTIONS = {
    chr(0x2800 + 46): 'the',
    chr(0x2800 + 47): 'and',
    chr(0x2800 + 63): 'for',
    chr(0x2800 + 55): 'of',
    chr(0x2800 + 62): 'with',
    chr(0x2800 + 20): 'in',
    chr(0x2800 + 33): 'ch',
    chr(0x2800 + 41): 'sh',
    chr(0x2800 + 57): 'th',
    chr(0x2800 + 49): 'wh',
    chr(0x2800 + 43): 'ed',
    chr(0x2800 + 59): 'er',
    chr(0x2800 + 51): 'ou',
    chr(0x2800 + 42): 'ow'
}

LETTER_REVERSE = {chr(0x2800 + v): k for k, v in BRAILLE_LETTERS.items()}
CAP_SIGN = chr(0x2800 + 32) # dot 6 (U+2820)
NUM_SIGN = chr(0x2800 + 60) # dots 3,4,5,6 (U+283C)

def to_braille_sentence(text):
    """
    Convert a full plain-text sentence into proper Braille notation,
    handling capitalization indicators, numbers, spaces, and punctuation.
    """
    out = []
    in_num = False
    words = text.split(' ')
    for w_idx, word in enumerate(words):
        if w_idx > 0:
            out.append('⠀')
            in_num = False
            
        low_w = word.lower()
        if low_w == 'the':
            if word[0].isupper():
                out.append(CAP_SIGN)
            out.append(chr(0x2800 + 46))
            continue
        elif low_w == 'and':
            if word[0].isupper():
                out.append(CAP_SIGN)
            out.append(chr(0x2800 + 47))
            continue
            
        for ch in word:
            if ch.isupper():
                out.append(CAP_SIGN)
                low = ch.lower()
                if low in BRAILLE_LETTERS:
                    out.append(chr(0x2800 + BRAILLE_LETTERS[low]))
                in_num = False
            elif ch.isdigit():
                if not in_num:
                    out.append(NUM_SIGN)
                    in_num = True
                let = REV_DIGIT_MAP.get(ch, 'a')
                out.append(chr(0x2800 + BRAILLE_LETTERS[let]))
            elif ch in BRAILLE_LETTERS:
                out.append(chr(0x2800 + BRAILLE_LETTERS[ch]))
                in_num = False
            elif ch in REV_PUNCT_MAP:
                out.append(REV_PUNCT_MAP[ch])
                in_num = False
            elif ch in ['\n', '\r']:
                out.append('\n')
                in_num = False
            else:
                out.append(ch)
                in_num = False
                
    return "".join(out)

def braille_sentence_to_text(braille_str):
    """
    Convert a full Braille sentence (with capital indicators, number signs,
    punctuation, spaces, and contractions) into clean natural text.
    """
    out = []
    cap_next = False
    cap_all = False
    in_number = False
    
    i = 0
    n = len(braille_str)
    while i < n:
        c = braille_str[i]
        
        # Double capital vs Single capital
        if c == CAP_SIGN:
            if i + 1 < n and braille_str[i+1] == CAP_SIGN:
                cap_all = True
                i += 2
            else:
                cap_next = True
                i += 1
            continue
            
        # Number sign
        if c == NUM_SIGN:
            in_number = True
            i += 1
            continue
            
        # Space or line break
        if c in [' ', chr(0x2800), '\n', '\t', '\r']:
            in_number = False
            cap_all = False
            cap_next = False
            out.append('\n' if c in ['\n', '\r'] else ' ')
            i += 1
            continue
            
        # Grade 2 contractions
        if c in CONTRACTIONS:
            word = CONTRACTIONS[c]
            if cap_all:
                out.append(word.upper())
            elif cap_next:
                out.append(word.capitalize())
                cap_next = False
            else:
                out.append(word)
            in_number = False
            i += 1
            continue
            
        # Punctuation
        if c in PUNCT_MAP:
            in_number = False
            out.append(PUNCT_MAP[c])
            i += 1
            continue
            
        # Letters (or digits if inside number sign)
        if c in LETTER_REVERSE:
            ch = LETTER_REVERSE[c]
            if in_number:
                out.append(DIGIT_MAP.get(ch, ch))
            else:
                if cap_all or cap_next:
                    out.append(ch.upper())
                    cap_next = False
                else:
                    out.append(ch)
            i += 1
            continue
            
        # Direct ASCII or other characters
        out.append(c)
        i += 1
        
    result = "".join(out)
    # Clean up redundant spaces while preserving sentence structure
    result = re.sub(r' +', ' ', result).strip()
    return result

def contains_braille(text):
    """Return True if text contains Unicode Braille characters (U+2800 to U+28FF)"""
    return any(0x2800 <= ord(c) <= 0x28FF for c in text)

def detect_braille_from_dots(image):
    """
    OpenCV computer vision algorithm:
    Detects Braille dots from images (scans/photos), groups them into multi-line sentences
    and words, and returns both the decoded plain-text sentence and Braille notation.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
        
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    dots = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 6 or area > 6000:
            continue
        peri = cv2.arcLength(cnt, True)
        if peri == 0:
            continue
        circularity = 4 * np.pi * (area / (peri * peri))
        if circularity > 0.38:
            (x, y), r = cv2.minEnclosingCircle(cnt)
            dots.append((x, y, r))
            
    if len(dots) < 2:
        return "", ""
        
    median_r = np.median([d[2] for d in dots])
    dots_by_y = sorted(dots, key=lambda d: d[1])
    line_gap = max(20, median_r * 6)
    lines = []
    curr_line = [dots_by_y[0]]
    for d in dots_by_y[1:]:
        if d[1] - curr_line[-1][1] < line_gap:
            curr_line.append(d)
        else:
            lines.append(curr_line)
            curr_line = [d]
    lines.append(curr_line)
    
    all_braille_symbols = []
    
    for l_idx, line in enumerate(lines):
        if not line:
            continue
        if l_idx > 0:
            all_braille_symbols.append('⠀')
            
        ys = [d[1] for d in line]
        min_y = min(ys)
        max_y = max(ys)
        y_span = max_y - min_y
        dy = max(10, y_span / 2.0 if y_span > 10 else median_r * 2.8)
        
        line = sorted(line, key=lambda d: d[0])
        diffs = [line[i+1][0] - line[i][0] for i in range(len(line)-1)]
        pos_diffs = [df for df in diffs if df > median_r * 1.5]
        dx = np.median(pos_diffs) if pos_diffs else (dy * 0.9)
        
        # Group dots into cells
        cells = []
        curr_cell = [line[0]]
        for d in line[1:]:
            if (d[0] - curr_cell[0][0]) <= (dx * 1.25):
                curr_cell.append(d)
            else:
                cells.append(curr_cell)
                curr_cell = [d]
        cells.append(curr_cell)
        
        # Determine inter-cell spacing and word-space threshold
        cell_starts = [min(d[0] for d in c) for c in cells]
        cell_diffs = [cell_starts[i+1] - cell_starts[i] for i in range(len(cell_starts)-1)]
        median_cell_gap = np.median(cell_diffs) if cell_diffs else (dx * 2.2)
        word_space_thresh = max(median_cell_gap * 1.5, dx * 3.0)
        
        for c_idx, cell in enumerate(cells):
            # Insert word space gap between words in a sentence
            if c_idx > 0:
                gap = cell_starts[c_idx] - cell_starts[c_idx - 1]
                if gap >= word_space_thresh:
                    all_braille_symbols.append('⠀')
                    
            cell_min_x = min(d[0] for d in cell)
            val = 0
            for d in cell:
                col = 1 if (d[0] - cell_min_x) > (dx * 0.55) else 0
                row = int(round((d[1] - min_y) / dy))
                row = min(2, max(0, row))
                
                bit_idx = col * 3 + row
                if bit_idx == 0: val |= 1
                elif bit_idx == 1: val |= 2
                elif bit_idx == 2: val |= 4
                elif bit_idx == 3: val |= 8
                elif bit_idx == 4: val |= 16
                elif bit_idx == 5: val |= 32
                
            b_char = chr(0x2800 + val)
            all_braille_symbols.append(b_char)
            
    braille_text = "".join(all_braille_symbols)
    decoded_sentence = braille_sentence_to_text(braille_text)
    return decoded_sentence, braille_text

@app.route('/')
def home():
    """Serve the web UI directly on http://localhost:5000/"""
    return send_file('index.html')

@app.route('/languages', methods=['GET'])
def get_languages():
    """Return all available gTTS language codes and names"""
    try:
        return jsonify(gtts.lang.tts_langs())
    except Exception as e:
        return jsonify({'en': 'English', 'ta': 'Tamil', 'hi': 'Hindi'})

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    lang = request.form.get('lang', 'en')
    
    # Validate language code against gTTS supported languages
    available_langs = gtts.lang.tts_langs()
    if lang not in available_langs:
        lang = 'en'
    
    img_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({'error': 'Invalid image'}), 400
    
    detected_braille = ""
    translated_text = ""
    
    # 1. OCR Extraction using Windows native OCR
    try:
        ocr_result = winocr.recognize_cv2_sync(img)
        extracted_text = ocr_result.get('text', '').strip()
    except Exception as e:
        print("OCR error:", e)
        extracted_text = ""

    # Check content type:
    if extracted_text:
        # Case A: Extracted text contains Unicode Braille sentence
        if contains_braille(extracted_text):
            detected_braille = extracted_text
            translated_text = braille_sentence_to_text(extracted_text)
        else:
            # Case B: Standard printed Latin text sentence
            translated_text = extracted_text
            detected_braille = to_braille_sentence(translated_text)
    else:
        # Case C: No OCR text found, run Braille dot sentence detection via OpenCV
        dot_sentence, dot_braille = detect_braille_from_dots(img)
        if dot_sentence:
            translated_text = dot_sentence
            detected_braille = dot_braille
        else:
            translated_text = "No words or Braille detected"
            detected_braille = "—"
    
    # 2. gTTS Audio Generation: Speak the entire recognized sentence
    audio_path = os.path.join(os.path.dirname(__file__), "output.mp3")
    has_audio = False
    
    text_to_speak = translated_text.strip()
    if text_to_speak and text_to_speak not in ["No words or Braille detected", "—"]:
        try:
            tts = gTTS(text=text_to_speak, lang=lang)
            tts.save(audio_path)
            has_audio = True
        except Exception as e:
            print(f"Audio generation error for lang={lang}:", e)
            has_audio = False
    
    return jsonify({
        'braille': detected_braille,
        'text': translated_text,
        'audio_url': '/get-audio' if has_audio else None,
        'lang': lang
    })

@app.route('/get-audio', methods=['GET'])
def get_audio():
    audio_path = os.path.join(os.path.dirname(__file__), "output.mp3")
    if os.path.exists(audio_path):
        as_attachment = request.args.get('download', '0') == '1'
        return send_file(
            audio_path,
            mimetype="audio/mp3",
            as_attachment=as_attachment,
            download_name="braille_speech.mp3"
        )
    return jsonify({'error': 'Audio file not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

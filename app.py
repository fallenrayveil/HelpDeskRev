from flask import Flask, request, jsonify
import os
import pytesseract
import cv2
import logging
import pandas as pd
import re
from fuzzywuzzy import process, fuzz

app = Flask(__name__)

# Path ke Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Path ke tessdata
tessdata_dir_config = r'--tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata"'

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Kamus koreksi umum OCR
corrections = {
    '1P': 'IP',
    'emor': 'error',
    'uier': 'user',
    'layoot': 'layout',
    'kompuler': 'komputer',
    'BM': 'IBM',
    'ekstemal': 'eksternal',
    'Yidak': 'Tidak',
    'Tolik': 'Terima'
    # Tambahkan lebih banyak koreksi di sini jika diperlukan
}

def apply_corrections(text, corrections):
    for typo, correction in corrections.items():
        text = re.sub(r'\b{}\b'.format(re.escape(typo)), correction, text, flags=re.IGNORECASE)
    return text

def correct_subject(subject, available_subjects):
    best_match = process.extractOne(subject, available_subjects, scorer=fuzz.token_sort_ratio)
    corrected_subject = best_match[0] if best_match[1] > 80 else subject  # Ambil hanya jika similarity lebih dari 80%
    return corrected_subject

# Fungsi untuk mendeteksi teks pada bagian "perihal"
def detect_subject(image_path, available_subjects):
    if not os.path.isfile(image_path):
        logging.error("Image file not found")
        return None

    image = cv2.imread(image_path)
    if image is None:
        logging.error("Failed to read image")
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    logging.debug("Image converted to grayscale")

    # Preprocessing tambahan
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    logging.debug("Image preprocessed with GaussianBlur and adaptiveThreshold")

    # Deteksi teks
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(binary, lang='ind', config=f'{tessdata_dir_config} {custom_config}')
    logging.debug(f"OCR detected text: {text}")

    # Mencari bagian "Perihal" atau variasi lainnya
    lines = text.split('\n')
    for line in lines:
        if any(keyword in line for keyword in ['Perihal', 'perihal', 'PERIHAL', 'Subject', 'subject', 'SUBJECT']):
            subject = re.split(r'Perihal:|PERIHAL:|Subject:|SUBJECT:', line, flags=re.IGNORECASE)[-1].strip()
            # Membersihkan hasil OCR dari tanda kutip atau karakter tidak diinginkan lainnya
            subject = re.sub(r'[^a-zA-Z0-9\s]', '', subject).strip()
            # Menambahkan logika untuk memperbaiki kesalahan umum OCR
            subject = apply_corrections(subject, corrections)
            # Koreksi subjek menggunakan fuzzy matching
            corrected_subject = correct_subject(subject, available_subjects)
            logging.debug(f"Cleaned subject found: {corrected_subject}")
            return corrected_subject

    logging.debug("Subject not found")
    return None

# Endpoint untuk mengunggah gambar dan mendeteksi teks
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logging.error("No file uploaded")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    file_path = 'uploaded_image.jpg'
    logging.debug(f"Saving uploaded file to {file_path}")
    file.save(file_path)

    try:
        # Baca file Excel
        excel_path = 'jenis_permasalahan.xlsx'
        df = pd.read_excel(excel_path, sheet_name='Sheet1')
        available_subjects = df['SUBJENIS'].tolist()
        logging.debug(f"Excel data: {df.head()}")
        logging.debug(f"Available subjects in Excel: {available_subjects}")

        subject = detect_subject(file_path, available_subjects)

        if subject:
            logging.debug(f"Subject detected by OCR: {subject}")
            # Lakukan pencarian dengan toleransi lebih rendah jika subjek tidak ditemukan persis
            classification = df[df['SUBJENIS'].apply(lambda x: fuzz.partial_ratio(x.lower(), subject.lower()) > 80)]
            if not classification.empty:
                level = int(classification['LEVEL'].values[0])
                priority = classification['PRIORITAS'].values[0]
                logging.debug(f"Classification result - Level: {level}, Priority: {priority}")

                # Check if subject matches any of the specified ones
                special_subjects = [
                    "kertas habis",
                    "Printer (Passbook/Laporan) tidak dapat mencetak",
                    "Perihali Kabel LAN unplupierputus"
                ]

                if any(subj.lower() in subject.lower() for subj in special_subjects):
                    return jsonify({
                        'alert': 'Silahkan menuju halaman chatbot untuk bantuan lebih lanjut.',
                        'redirect': '/chatbot'
                    })

                return jsonify({
                    'subject': subject,
                    'level': level,
                    'priority': priority
                })
            else:
                logging.error("Subject not found in Excel file")
                return jsonify({'error': 'Subject not found in Excel file'}), 404
        else:
            logging.debug("Subject not found in image")
            return jsonify({'error': 'Perihal not found'}), 400
    except Exception as e:
        logging.error(f"Error reading Excel file or processing image: {e}")
        return jsonify({'error': 'Error processing request'}), 500

if __name__ == '__main__':
    app.run(debug=True)

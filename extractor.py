# extractor.py

import chardet

import io

import pdfplumber

from docx import Document

def detect_encoding(b: bytes):

    res = chardet.detect(b)

    return res.get('encoding') or 'utf-8'

def text_from_txt_bytes(b: bytes):

    enc = detect_encoding(b)

    return b.decode(enc, errors='ignore')

def text_from_pdf_bytes(b: bytes):

    text_parts = []

    with pdfplumber.open(io.BytesIO(b)) as pdf:

        for page in pdf.pages:

            p = page.extract_text()

            if p:

                text_parts.append(p)

    return "\n".join(text_parts)

def text_from_docx_bytes(b: bytes):

    buf = io.BytesIO(b)

    doc = Document(buf)

    paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]

    return "\n".join(paras)

def extract_text_from_file(file_storage):

    """

    Accepts starlette UploadFile (FastAPI file).

    Returns str (extracted text)

    """

    content = file_storage.file.read()

    # reset pointer

    file_storage.file.seek(0)

    fname = (file_storage.filename or "").lower()

    if fname.endswith(".pdf"):

        try:

            return text_from_pdf_bytes(content)

        except Exception:

            return text_from_txt_bytes(content)

    elif fname.endswith(".docx"):

        try:

            return text_from_docx_bytes(content)

        except Exception:

            return text_from_txt_bytes(content)

    else:

        # txt, csv, or unknown — fallback to text decode

        return text_from_txt_bytes(content)
 
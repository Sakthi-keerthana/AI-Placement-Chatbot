"""Resume file handling (currently: PDF text extraction)."""

import fitz


def extract_resume_text(uploaded_file) -> str:
    """Extract plain text from an uploaded PDF resume."""

    file_bytes = uploaded_file.getbuffer()

    with fitz.open(stream=file_bytes, filetype="pdf") as document:
        text = "".join(page.get_text() for page in document)

    return text.strip()
import fitz  # PyMuPDF
import os
from pathlib import Path
from typing import Tuple


class PDFParser:
    """Handles PDF text extraction using PyMuPDF (fitz)."""

    @staticmethod
    def extract_text(file_path: str) -> Tuple[str, int]:
        """
        Extract all text from a PDF file.

        Args:
            file_path: Absolute or relative path to the PDF file.

        Returns:
            Tuple of (extracted_text, page_count)

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            ValueError: If the file is not a valid PDF or has no extractable text.
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not file_path.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF.")

        doc = None
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)

            if page_count == 0:
                raise ValueError("PDF has no pages.")

            full_text_parts = []

            for page_num in range(page_count):
                page = doc[page_num]
                text = page.get_text("text")  # plain text extraction
                if text.strip():
                    full_text_parts.append(f"--- Page {page_num + 1} ---\n{text.strip()}")

            full_text = "\n\n".join(full_text_parts)

            if not full_text.strip():
                raise ValueError(
                    "No extractable text found in PDF. "
                    "The PDF may be image-based (scanned). OCR is not supported in Phase 1."
                )

            return full_text, page_count

        except fitz.FileDataError as e:
            raise ValueError(f"Invalid or corrupted PDF file: {str(e)}")
        finally:
            if doc:
                doc.close()

    @staticmethod
    def validate_pdf(file_bytes: bytes) -> bool:
        """
        Quick validation: checks if the bytes represent a valid PDF.

        Args:
            file_bytes: Raw bytes of the uploaded file.

        Returns:
            True if valid PDF header found.
        """
        # PDF files start with %PDF-
        return file_bytes[:5] == b"%PDF-"

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Returns file size in MB."""
        return os.path.getsize(file_path) / (1024 * 1024)

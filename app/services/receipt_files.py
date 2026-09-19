"""Extract searchable receipt text from uploaded PDF and image files."""

from io import BytesIO


class ReceiptFileError(ValueError):
    """Raised when an uploaded receipt cannot be read."""


def extract_receipt_text(filename: str, content: bytes) -> str:
    """Return text for a supported receipt file, using OCR for images when available."""

    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as exc:
            raise ReceiptFileError("PDF could not be read") from exc
    if suffix in {"jpg", "jpeg", "png"}:
        try:
            from PIL import Image
            import pytesseract

            return pytesseract.image_to_string(Image.open(BytesIO(content))).strip()
        except Exception as exc:
            raise ReceiptFileError("Image OCR is unavailable; enter the receipt details manually") from exc
    raise ReceiptFileError("Upload a PDF, JPG, JPEG, or PNG receipt")

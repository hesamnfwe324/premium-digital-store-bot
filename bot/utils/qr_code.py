import io
import qrcode
from bot.utils.logger import logger


def generate_qr_code(data: str) -> io.BytesIO:
    """Generate a QR code PNG image and return it as a BytesIO buffer."""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"QR code generation error: {e}")
        raise

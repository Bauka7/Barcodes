from io import BytesIO
import os
from pathlib import Path

from reportlab.graphics.barcode import code128
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Department, GeneratedBarcode, GeneratedBatch
from app.services.print_tracking_service import create_printed_batch

LABEL_WIDTH = 126
LABEL_HEIGHT = 71
UNICODE_FONT_NAME = "DejaVuSans"
UNICODE_FONT_FILE_NAME = "DejaVuSans.ttf"
FONT_PATH_ENV_VAR = "DEJAVU_SANS_FONT_PATH"

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FONT_PATHS = (
    BACKEND_ROOT / "assets" / "fonts" / UNICODE_FONT_FILE_NAME,
    Path(r"C:\Windows\Fonts\DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/local/share/fonts/DejaVuSans.ttf"),
)


class GeneratedBatchNotFoundError(LookupError):
    pass


def _find_unicode_font_path() -> Path:
    env_font_path = os.getenv(FONT_PATH_ENV_VAR)
    candidates = []

    if env_font_path:
        candidates.append(Path(env_font_path))

    candidates.extend(DEFAULT_FONT_PATHS)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched_paths = ", ".join(str(path) for path in candidates)
    raise RuntimeError(
        f"{UNICODE_FONT_FILE_NAME} was not found. Place it at "
        f"{BACKEND_ROOT / 'assets' / 'fonts' / UNICODE_FONT_FILE_NAME} "
        f"or set {FONT_PATH_ENV_VAR}. Searched: {searched_paths}"
    )


def register_pdf_fonts() -> str:
    try:
        pdfmetrics.getFont(UNICODE_FONT_NAME)
        return UNICODE_FONT_NAME
    except KeyError:
        pass

    font_path = _find_unicode_font_path()
    pdfmetrics.registerFont(TTFont(UNICODE_FONT_NAME, str(font_path)))
    return UNICODE_FONT_NAME


async def _load_batch_and_barcodes(
    session: AsyncSession,
    batch_id: int,
) -> tuple[GeneratedBatch, list[GeneratedBarcode], str]:
    batch_result = await session.execute(
        select(GeneratedBatch).where(GeneratedBatch.id == batch_id)
    )
    batch = batch_result.scalar_one_or_none()

    if batch is None:
        raise GeneratedBatchNotFoundError(f"Generated batch with id {batch_id} was not found.")

    barcode_result = await session.execute(
        select(GeneratedBarcode)
        .where(GeneratedBarcode.batch_id == batch_id)
        .order_by(GeneratedBarcode.id)
    )
    barcodes = list(barcode_result.scalars().all())

    if not barcodes:
        raise ValueError("Generated batch does not contain barcodes.")

    department_name = ""
    if batch.department_id is not None:
        department_result = await session.execute(
            select(Department.name).where(Department.id == batch.department_id)
        )
        department_name = department_result.scalar_one_or_none() or ""

    return batch, barcodes, department_name


def _draw_centered_text(
    pdf: canvas.Canvas,
    text: str,
    y: float,
    font_name: str,
    font_size: float,
    max_width: float,
) -> None:
    pdf.setFont(font_name, font_size)
    visible_text = text

    while visible_text and pdf.stringWidth(visible_text, font_name, font_size) > max_width:
        visible_text = visible_text[:-1]

    pdf.drawCentredString(LABEL_WIDTH / 2, y, visible_text)


def _draw_barcode(pdf: canvas.Canvas, barcode_value: str) -> None:
    barcode = code128.Code128(
        barcode_value,
        barHeight=18,
        barWidth=0.48,
        humanReadable=False,
    )
    max_width = LABEL_WIDTH - 8
    scale = min(1.0, max_width / barcode.width)
    barcode_width = barcode.width * scale
    x = (LABEL_WIDTH - barcode_width) / 2
    y = 25

    pdf.saveState()
    pdf.translate(x, y)
    pdf.scale(scale, scale)
    barcode.drawOn(pdf, 0, 0)
    pdf.restoreState()


def generate_labels_pdf_bytes(
    batch: GeneratedBatch,
    barcodes: list[GeneratedBarcode],
    department_name: str,
) -> bytes:
    font_name = register_pdf_fonts()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(LABEL_WIDTH, LABEL_HEIGHT))

    label_department_name = department_name or "KazPost"
    for generated_barcode in barcodes:
        pdf.setFillColorRGB(0, 0, 0)
        _draw_centered_text(pdf, label_department_name, 60, font_name, 6.5, LABEL_WIDTH - 8)
        _draw_barcode(pdf, generated_barcode.barcode)
        _draw_centered_text(pdf, generated_barcode.barcode, 6, font_name, 8.2, LABEL_WIDTH - 8)
        pdf.showPage()

    pdf.save()
    return buffer.getvalue()


async def generate_batch_pdf_preview(
    session: AsyncSession,
    batch_id: int,
) -> bytes:
    batch, barcodes, department_name = await _load_batch_and_barcodes(
        session=session,
        batch_id=batch_id,
    )
    return generate_labels_pdf_bytes(
        batch=batch,
        barcodes=barcodes,
        department_name=department_name,
    )


async def generate_batch_pdf_and_track_print(
    session: AsyncSession,
    batch_id: int,
    printed_by: str | None = None,
    printer_name: str | None = None,
    notes: str | None = None,
) -> bytes:
    async with session.begin():
        batch, barcodes, department_name = await _load_batch_and_barcodes(
            session=session,
            batch_id=batch_id,
        )
        pdf_bytes = generate_labels_pdf_bytes(
            batch=batch,
            barcodes=barcodes,
            department_name=department_name,
        )
        await create_printed_batch(
            session=session,
            batch=batch,
            barcodes=barcodes,
            printed_by=printed_by,
            printer_name=printer_name,
            notes=notes,
        )

    return pdf_bytes

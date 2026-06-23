import pdfplumber
import os
import logging

logger = logging.getLogger("jobbot")


def extract_cv_text(cv_path: str) -> str:
    logger.info(f"Intentando leer CV desde: {cv_path}")

    if not os.path.exists(cv_path):
        logger.warning(f"Archivo CV no encontrado: {cv_path}")
        return ""

    file_size = os.path.getsize(cv_path)
    logger.debug(f"CV encontrado — tamano: {file_size} bytes")

    text = ""
    try:
        with pdfplumber.open(cv_path) as pdf:
            total_pages = len(pdf.pages)
            logger.debug(f"PDF abierto — paginas: {total_pages}")
            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    logger.debug(f"Pagina {i}/{total_pages}: {len(page_text)} caracteres extraidos")
                else:
                    logger.warning(f"Pagina {i}/{total_pages}: sin texto extraible (puede ser imagen)")
    except Exception as e:
        logger.error(f"Error leyendo PDF '{cv_path}': {e}", exc_info=True)
        return ""

    text = text.strip()
    logger.info(f"CV procesado — {len(text)} caracteres totales")
    return text

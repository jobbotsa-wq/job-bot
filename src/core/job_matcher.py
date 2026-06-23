import google.generativeai as genai
import json
import re
import logging

logger = logging.getLogger("jobbot")


def setup_gemini(api_key: str):
    logger.info("Configurando cliente Gemini AI")
    if not api_key:
        logger.error("GEMINI_API_KEY vacia — scoring deshabilitado")
        return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    logger.info("Cliente Gemini listo (modelo: gemini-1.5-flash)")
    return model


def score_job(model, profile: dict, cv_text: str, job: dict) -> dict:
    title = job.get("title", "sin titulo")
    company = job.get("company", "sin empresa")
    logger.info(f"Evaluando con Gemini: '{title}' @ {company}")
    logger.debug(f"Descripcion oferta: {len(job.get('description', ''))} chars | CV: {len(cv_text)} chars")

    prompt = f"""
Eres un experto en recursos humanos. Analiza si esta oferta de trabajo es adecuada para el candidato.

PERFIL DEL CANDIDATO:
- Nombre: {profile.get('personal', {}).get('name')}
- Palabras clave buscadas: {', '.join(profile.get('search', {}).get('keywords', []))}
- Modalidad preferida: {', '.join(profile.get('search', {}).get('modality', []))}
- Anos de experiencia: {profile.get('search', {}).get('experience_years', {})}
- Idiomas: {', '.join(profile.get('search', {}).get('languages', []))}

RESUMEN DEL CV:
{cv_text[:2000]}

OFERTA DE TRABAJO:
- Titulo: {job.get('title')}
- Empresa: {job.get('company')}
- Descripcion: {job.get('description', '')[:1500]}

Responde SOLO con un JSON valido con este formato exacto:
{{
  "score": <numero entre 0 y 100>,
  "reason": "<explicacion breve en espanol de maximo 2 oraciones>",
  "apply": <true o false>
}}
"""
    try:
        logger.debug("Enviando prompt a Gemini...")
        response = model.generate_content(prompt)
        raw = response.text.strip()
        logger.debug(f"Respuesta Gemini ({len(raw)} chars): {raw[:200]}")

        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            logger.error(f"Gemini no retorno JSON valido. Respuesta completa: {raw}")
            return {"score": 0, "reason": "Respuesta inesperada de Gemini", "apply": False}

        result = json.loads(match.group())
        logger.info(
            f"Score: {result.get('score')}/100 | apply={result.get('apply')} | "
            f"{result.get('reason', '')[:100]}"
        )
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON de Gemini: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error llamando a Gemini para '{title}': {e}", exc_info=True)

    return {"score": 0, "reason": "Error al analizar con IA", "apply": False}

import google.generativeai as genai
import json
import re


def setup_gemini(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def score_job(model, profile: dict, cv_text: str, job: dict) -> dict:
    """Puntúa qué tan afín es una oferta al perfil. Retorna score 0-100 y razón."""
    prompt = f"""
Eres un experto en recursos humanos. Analiza si esta oferta de trabajo es adecuada para el candidato.

PERFIL DEL CANDIDATO:
- Nombre: {profile.get('personal', {}).get('name')}
- Palabras clave buscadas: {', '.join(profile.get('search', {}).get('keywords', []))}
- Modalidad preferida: {', '.join(profile.get('search', {}).get('modality', []))}
- Años de experiencia: {profile.get('search', {}).get('experience_years', {})}
- Idiomas: {', '.join(profile.get('search', {}).get('languages', []))}

RESUMEN DEL CV:
{cv_text[:2000]}

OFERTA DE TRABAJO:
- Título: {job.get('title')}
- Empresa: {job.get('company')}
- Descripción: {job.get('description', '')[:1500]}

Responde SOLO con un JSON válido con este formato exacto:
{{
  "score": <número entre 0 y 100>,
  "reason": "<explicación breve en español de máximo 2 oraciones>",
  "apply": <true o false>
}}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Extraer JSON aunque venga con texto extra
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[Gemini] Error scoring job: {e}")
    return {"score": 0, "reason": "Error al analizar", "apply": False}

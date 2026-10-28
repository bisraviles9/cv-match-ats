import io
import re
from collections import Counter

import streamlit as st

st.set_page_config(page_title="CV Match ATS", page_icon="🧭", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f5f7fb; }
.block-container { max-width: 1120px; padding-top: 2rem; }
h1, h2, h3 { font-family: 'Manrope', sans-serif; color: #18243a; }
.hero { padding: 1.5rem 0 1rem; }
.hero p { color: #62708a; font-size: 1.08rem; }
.card { background: white; border: 1px solid #e6eaf1; border-radius: 18px; padding: 1.25rem 1.4rem; }
.pill { background: #eaf7f2; color: #13795b; padding: .28rem .7rem; border-radius: 999px; font-weight: 700; font-size: .85rem; }
.small-note { color: #69758a; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)

STOP = set("a al algo algunas algunos ante antes como con contra cual cuando de del desde donde durante e el ella ellas ellos en entre era es esa esas ese eso esos esta estaba estas este esto estos fue ha hacia hasta hay la las le les lo los mas más me mi mis muy ni no nos o para pero por porque que quien se sin sobre su sus te tiene tu tus un una uno unos y ya".split())

@st.cache_data(show_spinner=False)
def extract_text(data: bytes, filename: str) -> str:
    ext = filename.lower().rsplit('.', 1)[-1]
    if ext == "pdf":
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == "docx":
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    if ext == "txt":
        return data.decode("utf-8", errors="ignore")
    raise ValueError("Formato no compatible")

def terms(text: str):
    # Mantiene términos compuestos y siglas; normaliza a minúsculas.
    words = re.findall(r"[a-záéíóúüñ+#.]{2,}(?:\s+[a-záéíóúüñ+#.]{2,}){0,2}", text.lower())
    return [w.strip(" .") for w in words if w.strip(" .") not in STOP and len(w.strip(" .")) > 2]

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())

def analyze(cv: str, job: str):
    cv_norm, job_norm = clean(cv), clean(job)
    job_terms = terms(job)
    counts = Counter(job_terms)
    # Filtra vocabulario genérico: términos que aparecen más de una vez y extrae hasta 30 claves.
    key_terms = [term for term, _ in counts.most_common(45) if term not in STOP]
    # Desduplica términos que incluyen otros términos (p.ej. data y data analysis).
    unique = []
    for term in key_terms:
        if term not in unique:
            unique.append(term)
    found, missing = [], []
    for term in unique[:30]:
        (found if term in cv_norm else missing).append(term)
    score = round(100 * len(found) / max(1, len(found) + len(missing)))
    return score, found, missing

st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown("# 🧭 CV Match ATS")
st.markdown("Compara tu currículum con una vacante y descubre qué palabras clave conviene destacar.")
st.markdown("</div>", unsafe_allow_html=True)
st.info("**Gratis y privado:** el análisis se ejecuta en esta app y no usamos una API de IA. Tu CV no se guarda en una base de datos. El resultado es orientativo: ningún puntaje garantiza pasar un ATS o conseguir una entrevista.")

left, right = st.columns([1, 1], gap="large")
with left:
    st.subheader("1. Tu currículum")
    uploaded = st.file_uploader("Sube tu CV", type=["pdf", "docx", "txt"], help="Formatos aceptados: PDF con texto, Word (.docx) o texto (.txt).")
    if uploaded:
        st.caption(f"Archivo: {uploaded.name} · {uploaded.size / 1024:.0f} KB")
with right:
    st.subheader("2. La vacante")
    job_text = st.text_area("Pega la descripción del puesto", height=190, placeholder="Incluye responsabilidades, requisitos y habilidades solicitadas…")

if st.button("Analizar coincidencia", type="primary", use_container_width=True):
    if not uploaded:
        st.error("Sube tu currículum para empezar.")
    elif len(job_text.strip()) < 40:
        st.error("Pega una descripción de vacante un poco más completa (al menos 40 caracteres).")
    else:
        try:
            cv_text = extract_text(uploaded.getvalue(), uploaded.name)
            if len(cv_text.strip()) < 40:
                st.error("No pude leer suficiente texto. Si es un PDF escaneado como imagen, conviértelo a PDF con texto o usa un archivo DOCX/TXT.")
            else:
                score, found, missing = analyze(cv_text, job_text)
                st.divider()
                st.subheader("Tu resultado")
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("Coincidencia de palabras clave", f"{score}%")
                    st.progress(score / 100)
                with c2:
                    if score >= 75:
                        st.success("Buena coincidencia de términos. Revisa que las habilidades estén respaldadas por ejemplos concretos.")
                    elif score >= 45:
                        st.warning("Coincidencia parcial. Ajusta el CV para reflejar con precisión los requisitos relevantes.")
                    else:
                        st.info("Hay una brecha importante de términos frente a esta vacante. Verifica si el puesto encaja con tu experiencia antes de editar.")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("#### ✅ Encontradas en tu CV")
                    if found:
                        st.write(" · ".join(f"`{x}`" for x in found))
                    else:
                        st.write("No se detectaron coincidencias exactas todavía.")
                with col_b:
                    st.markdown("#### 🔎 No detectadas")
                    if missing:
                        st.write(" · ".join(f"`{x}`" for x in missing))
                    else:
                        st.write("¡Se detectaron todas las palabras clave analizadas!")
                st.markdown("#### Siguientes mejoras")
                if missing:
                    st.write("- Añade solo las habilidades que realmente tienes y que puedas demostrar; no copies requisitos que no correspondan a tu experiencia.")
                    st.write("- Incorpora los términos relevantes de forma natural en experiencia, proyectos o habilidades, idealmente con resultados medibles.")
                st.write("- Usa títulos de sección claros, fechas consistentes y un diseño sencillo. Revisa que el PDF permita seleccionar/copiar el texto.")
                st.caption("El porcentaje mide coincidencia léxica simple; no evalúa contexto, nivel de dominio, formato visual ni criterios internos de cada sistema ATS.")
        except Exception as e:
            st.error(f"No se pudo leer el archivo. Comprueba que no esté dañado o protegido. Detalle: {e}")

with st.expander("¿Qué significa ATS?"):
    st.write("Un ATS es un sistema que algunas empresas usan para organizar postulaciones. Esta herramienta compara palabras de tu CV con las de la vacante; es una guía básica, no una prueba real de un empleador.")
st.markdown("<p class='small-note'>Hecho para ayudarte a adaptar tu CV con honestidad y claridad.</p>", unsafe_allow_html=True)

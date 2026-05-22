import streamlit as st
import re
import io
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from pypdf import PdfReader, PdfWriter
import docx
from PIL import Image
import pytesseract
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

st.set_page_config(page_title="Portal IT", page_icon="🏢", layout="wide")

st.title("🏢 Portal d'Eines IT (Zero-Footprint)")
st.write("Eines locals de procés de dades. **Cap document es guarda al servidor un cop tancada la sessió.**")

@st.cache_resource
def inicialitzar_ia():
    try:
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "ca", "model_name": "ca_core_news_md"}]
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine_obj = provider.create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine_obj, supported_languages=["ca"])
    except Exception as e:
        return None

analyzer = inicialitzar_ia()

# --- 4 PESTANYES ---
pestanya1, pestanya2, pestanya3, pestanya4 = st.tabs([
    "🛡️ Anonimitzador", 
    "📄 Gestió de PDFs", 
    "🖼️ Imatges",
    "🛠️ Eines Avançades"
])

# ==========================================
# PESTANYA 1: LA RENTADORA DE LOGS
# ==========================================
with pestanya1:
    st.header("Anonimitzador de Documents i Logs")
    st.write("Filtre de privacitat per a text, logs i documents administratius.")
    
    def netejar_text_pro(text):
        if not text: return ""
        memoria = {'IP': {}, 'MAC': {}, 'URL': {}, 'CREDENCIAL': {}, 'DNI': {}, 'IBAN': {}, 'EMAIL': {}, 'TELEFON': {}, 'PERSONA': {}}
        
        def obtenir_tag(valor, categoria, prefix):
            valor_net = valor.strip().strip('"\'')
            if valor_net not in memoria[categoria]:
                memoria[categoria][valor_net] = f"<{prefix}_{len(memoria[categoria])+1}>"
            return memoria[categoria][valor_net]

        # 1. FASE EXPRESIONS REGULARS (Dades estructurades)
        def rep_ip(m): return obtenir_tag(m.group(0), 'IP', 'IP')
        def rep_mac(m): return obtenir_tag(m.group(0), 'MAC', 'MAC')
        def rep_url(m): return obtenir_tag(m.group(0), 'URL', 'URL')
        def rep_dni(m): return obtenir_tag(m.group(0).upper(), 'DNI', 'DNI')
        def rep_iban(m): return obtenir_tag(m.group(0).upper().replace(" ", ""), 'IBAN', 'IBAN')
        def rep_email(m): return obtenir_tag(m.group(0), 'EMAIL', 'EMAIL')
        def rep_telefon(m): return obtenir_tag(m.group(0), 'TELEFON', 'TELF')
        def rep_cred(m):
            secret = m.group(len(m.groups()))
            tag = obtenir_tag(secret, 'CREDENCIAL', 'CRED')
            return m.group(0).replace(secret, tag)

        text = re.sub(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', rep_ip, text)
        text = re.sub(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b', rep_mac, text)
        text = re.sub(r'https?://[a-zA-Z0-9.-]+(?::\d+)?(?:/[a-zA-Z0-9./?%&=-]*)?', rep_url, text)
        text = re.sub(r'\b[XYZxyz]?\d{5,8}[A-Za-z]\b', rep_dni, text)
        text = re.sub(r'\b[A-Za-z]{2}\d{2}[ \-]?[A-Za-z0-9]{4}[ \-]?[A-Za-z0-9]{4}[ \-]?[A-Za-z0-9]{4}[ \-]?[A-Za-z0-9]{4}[ \-]?[A-Za-z0-9]{0,4}\b', rep_iban, text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', rep_email, text)
        text = re.sub(r'\b(?:\+34|0034)?[ \-]?[6789]\d{2}[ \-]?\d{3}[ \-]?\d{3}\b', rep_telefon, text)
        text = re.sub(r'(?i)(password|passwd|secret|token|api_key|key|auth)\s*[:=]\s*(["\']?[^\s"\'\n]+["\']?)', rep_cred, text)
        text = re.sub(r'(?i)(?:\s|^)(-p|--password)(\s*=?\s*)(["\']?[^\s"\'\n]+["\']?)', rep_cred, text)

        # 2. FASE INTEL·LIGÈNCIA ARTIFICIAL (Text lliure)
        if analyzer:
            try:
                results = analyzer.analyze(text=text, language="ca", entities=["PERSON"])
                results = sorted(results, key=lambda x: x.start, reverse=True)
                
                # Passem a un "set" en minúscules per a màxima velocitat
                paraules_prohibides = {
                    "dni", "nie", "nif", "bopb", "dogc", "oac", "sepe", 
                    "decret", "president", "presidència", "alcalde", "alcaldessa",
                    "consell", "comarcal", "occidental", "ajuntament", "resolució", 
                    "tribunal", "generalitat", "consorci", "subgrup", "treballadors"
                }
                
                for res in results:
                    if res.score > 0.40:
                        nom_original = text[res.start:res.end]
                        nom_net = nom_original.strip()
                        
                        # Sense restricció de majúscules, només mirem que no sigui paraula clau
                        if len(nom_net) > 2 and nom_net.lower() not in paraules_prohibides:
                            tag = obtenir_tag(nom_original, 'PERSONA', 'PERSONA')
                            text = text[:res.start] + tag + text[res.end:]
            except Exception: pass 
            
        return text

    with st.form("formulari_rentadora"):
        arxiu_pujat = st.file_uploader("Puja un arxiu per anonimitzar el TEXT", type=["txt", "log", "pdf", "docx"], key="anon_uploader")
        text_usuari = st.text_area("O enganxa el text directament:", height=150)
        boto_netejar = st.form_submit_button("Netejar i Anonimitzar", type="primary")

    if boto_netejar:
        text_a_processar = ""
        if arxiu_pujat:
            nom = arxiu_pujat.name.lower()
            if nom.endswith(".pdf"):
                lector = PdfReader(io.BytesIO(arxiu_pujat.read()))
                for p in lector.pages: text_a_processar += p.extract_text() + "\n"
            elif nom.endswith(".docx"):
                doc = docx.Document(io.BytesIO(arxiu_pujat.read()))
                text_a_processar = "\n".join([p.text for p in doc.paragraphs])
            else:
                text_a_processar = arxiu_pujat.getvalue().decode("utf-8")
        elif text_usuari.strip():
            text_a_processar = text_usuari
            
        if text_a_processar:
            with st.spinner("La IA local està analitzant la gramàtica..."):
                resultat = netejar_text_pro(text_a_processar)
            st.success("Document sanititzat amb èxit!")
            st.code(resultat, language="text")
            st.download_button("📥 Descarregar Text Net (.txt)", resultat, "anonimitzat.txt", "text/plain")

# ==========================================
# PESTANYA 2: MANIPULACIÓ DE PDFs
# ==========================================
with pestanya2:
    st.header("Gestió i Estructura de Documents PDF")
    opcio_pdf = st.radio("Operació a realitzar:", ["🔗 Unir diversos PDFs", "✂️ Extreure pàgines", "🛠️ Eliminar i Rotar pàgines"])
    
    if opcio_pdf == "🔗 Unir diversos PDFs":
        pdfs_a_unir = st.file_uploader("Puja els fitxers", type="pdf", accept_multiple_files=True, key="merge_pdfs")
        if pdfs_a_unir and st.button("Fusionar Documents", type="primary"):
            escritor = PdfWriter()
            for arxiu in pdfs_a_unir:
                lector = PdfReader(io.BytesIO(arxiu.read()))
                for pagina in lector.pages: escritor.add_page(pagina)
            pdf_resultant = io.BytesIO()
            escritor.write(pdf_resultant)
            st.success("Fitxers fusionats correctament!")
            st.download_button("📥 Descarregar PDF", pdf_resultant.getvalue(), "Document_Fusionat.pdf", "application/pdf")

    elif opcio_pdf == "✂️ Extreure pàgines":
        pdf_a_tallar = st.file_uploader("Puja el document PDF", type="pdf", key="extract_pdf")
        if pdf_a_tallar:
            lector_tall = PdfReader(io.BytesIO(pdf_a_tallar.read()))
            num_pagines = len(lector_tall.pages)
            pagines_selecc = st.slider("Rang de pàgines a conservar:", 1, num_pagines, (1, num_pagines))
            if st.button("Extreure Segment", type="primary"):
                escritor_tall = PdfWriter()
                for i in range(pagines_selecc[0] - 1, pagines_selecc[1]):
                    escritor_tall.add_page(lector_tall.pages[i])
                pdf_tallat = io.BytesIO()
                escritor_tall.write(pdf_tallat)
                st.success("Segment extret correctament!")
                st.download_button(f"📥 Descarregar Segment", pdf_tallat.getvalue(), f"Extracte.pdf", "application/pdf")

    elif opcio_pdf == "🛠️ Eliminar i Rotar pàgines":
        pdf_a_modificar = st.file_uploader("Puja el document a modificar", type="pdf", key="mod_pdf")
        if pdf_a_modificar:
            lector_mod = PdfReader(io.BytesIO(pdf_a_modificar.read()))
            col1, col2 = st.columns(2)
            with col1: pagines_a_esborrar = st.text_input("Pàgines a ELIMINAR (ex: 2, 5):")
            with col2: rotacio = st.selectbox("Orientació:", ["No rotar", "90 graus", "180 graus", "270 graus"])
            
            if st.button("Aplicar Modificacions", type="primary"):
                try: pag_esborrar_llista = [int(p.strip()) - 1 for p in pagines_a_esborrar.split(",") if p.strip().isdigit()]
                except: pag_esborrar_llista = []
                    
                escritor_mod = PdfWriter()
                graus = 0
                if rotacio == "90 graus": graus = 90
                elif rotacio == "180 graus": graus = 180
                elif rotacio == "270 graus": graus = 270

                for i, pagina in enumerate(lector_mod.pages):
                    if i not in pag_esborrar_llista:
                        if graus != 0: pagina.rotate(graus)
                        escritor_mod.add_page(pagina)
                
                pdf_modificat = io.BytesIO()
                escritor_mod.write(pdf_modificat)
                st.success("Canvis aplicats!")
                st.download_button("📥 Descarregar PDF", pdf_modificat.getvalue(), "Document_Corregit.pdf", "application/pdf")

# ==========================================
# PESTANYA 3: IMATGES PER AL REGISTRE
# ==========================================
with pestanya3:
    st.header("Adaptador d'Imatges per a Expedients")
    opcio_imatge = st.radio("Acció:", ["🗜️ Reduir el pes", "📄 Convertir Fotografia a PDF"])
    
    if opcio_imatge == "🗜️ Reduir el pes":
        imatge_pujada = st.file_uploader("Puja la fotografia", type=["jpg", "jpeg", "png"], key="comp_img")
        if imatge_pujada:
            qualitat = st.slider("Nivell de compressió:", 10, 100, 50)
            if st.button("Comprimir", type="primary"):
                img = Image.open(io.BytesIO(imatge_pujada.read()))
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img_resultant = io.BytesIO()
                img.save(img_resultant, format="JPEG", optimize=True, quality=qualitat)
                st.success("Compressió finalitzada!")
                st.download_button("📥 Descarregar Imatge", img_resultant.getvalue(), "Comprimida.jpg", "image/jpeg")

    elif opcio_imatge == "📄 Convertir Fotografia a PDF":
        foto_a_pdf = st.file_uploader("Puja la foto", type=["jpg", "jpeg", "png"], key="pdf_img")
        if foto_a_pdf and st.button("Transformar a PDF", type="primary"):
            img_pdf = Image.open(io.BytesIO(foto_a_pdf.read()))
            if img_pdf.mode == "RGBA": img_pdf = img_pdf.convert("RGB")
            pdf_resultant = io.BytesIO()
            img_pdf.save(pdf_resultant, format="PDF", resolution=100.0)
            st.success("Fotografia convertida a PDF!")
            st.download_button("📥 Descarregar PDF", pdf_resultant.getvalue(), "Document.pdf", "application/pdf")

# ==========================================
# PESTANYA 4: EINES AVANÇADES (OCR + MARCA D'AIGUA PROFESIONAL)
# ==========================================
with pestanya4:
    st.header("Eines Avançades de Gestió")
    opcio_avancada = st.radio("Què necessites fer?", [
        "🔍 Lector de Text en Imatges (OCR)",
        "🛑 Afegir Marca d'Aigua a un PDF"
    ])

    if opcio_avancada == "🔍 Lector de Text en Imatges (OCR)":
        st.info("Aquesta eina llegeix el text de fotografies sense enviar les dades fora.")
        imatge_ocr = st.file_uploader("Puja la imatge amb el text a llegir", type=["jpg", "jpeg", "png"], key="ocr_uploader")
        
        if imatge_ocr:
            st.image(imatge_ocr, caption="Imatge a analitzar", width=300)
            if st.button("Llegir Text (OCR)", type="primary"):
                with st.spinner("Analitzant la imatge (Això pot trigar uns segons)..."):
                    try:
                        img = Image.open(io.BytesIO(imatge_ocr.read()))
                        text_extret = pytesseract.image_to_string(img, lang='cat+spa+eng')
                        if text_extret.strip():
                            st.success("S'ha pogut llegir el text de la imatge:")
                            st.text_area("Text extret (Pots copiar i enganxar):", value=text_extret, height=200)
                        else:
                            st.warning("No s'ha detectat text llegible a la imatge.")
                    except Exception as e:
                        st.error(f"Error en el motor OCR: {e}")

    elif opcio_avancada == "🛑 Afegir Marca d'Aigua a un PDF":
        st.info("Estampa un text diagonal i semitransparent sobre el document (Marca d'aigua professional).")
        pdf_a_marcar = st.file_uploader("Puja el PDF original", type="pdf", key="watermark_pdf")
        text_marca = st.text_input("Text de la marca d'aigua:", value="ESBORRANY - ÚS INTERN")
        
        if pdf_a_marcar and text_marca:
            if st.button("Estampar Marca d'Aigua", type="primary"):
                try:
                    lector = PdfReader(io.BytesIO(pdf_a_marcar.read()))
                    escritor = PdfWriter()
                    
                    for pagina in lector.pages:
                        ample = float(pagina.mediabox.width)
                        alt = float(pagina.mediabox.height)
                        
                        packet = io.BytesIO()
                        can = canvas.Canvas(packet, pagesize=(ample, alt))
                        can.translate(ample / 2, alt / 2) 
                        can.rotate(45) 
                        
                        mida_font = int(ample / 10)
                        can.setFont("Helvetica-Bold", mida_font)
                        can.setFillColor(Color(1, 0, 0, alpha=0.3)) 
                        
                        can.drawCentredString(0, 0, text_marca)
                        can.save()
                        
                        packet.seek(0)
                        pdf_marca = PdfReader(packet)
                        pagina_marca = pdf_marca.pages[0]
                        
                        pagina.merge_page(pagina_marca)
                        escritor.add_page(pagina)
                        
                    pdf_resultant = io.BytesIO()
                    escritor.write(pdf_resultant)
                    st.success("Marca d'aigua professional estampada!")
                    st.download_button("📥 Descarregar PDF Marcat", pdf_resultant.getvalue(), "Document_Amb_Marca.pdf", "application/pdf")
                except Exception as e:
                    st.error(f"Error en aplicar la marca d'aigua: {e}")

# Rentadora de Logs PRO (Zero-Footprint)

Portal d'eines administratives d'alt rendiment per a la gestió documental. Dissenyat per a la seguretat de les dades i l'eficiència en entorns municipals.

## 🚀 Característiques clau
- **Anonimització Segura:** Detecció de dades sensibles amb IA (spaCy + Presidio) sense sortir del servidor.
- **Gestió de PDF:** Unió, extracció, rotació i segellat amb marques d'aigua professionals.
- **Adaptador d'imatges:** Compressió i conversió a PDF de documents per al registre.
- **OCR Local:** Extracció de text mitjançant Tesseract (motor local).
- **Zero-Footprint:** Arquitectura 100% volàtil: les dades no es guarden mai a disc.

## 🛠️ Stack Tecnològic
- **Backend:** Python 3.10
- **Frontend:** Streamlit
- **Processament:** spaCy (IA), Tesseract (OCR), ReportLab (PDF), Pillow (Imatges)
- **Infraestructura:** Docker & Docker Compose

## 💡 Per què aquest projecte?
Aquest projecte neix per resoldre la dependència de serveis de tercers (Adobe, eines Cloud insegures) i garantir la sobirania tecnològica municipal, assegurant el compliment del RGPD i l'Esquema Nacional de Seguretat.

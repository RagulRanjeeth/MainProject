import base64
import os
import json
import re
import streamlit as st
from jinja2 import Template
from langchain_community.document_loaders import PyPDFLoader
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def reset_state():
    st.session_state['parsed_json'] = None
    st.session_state['selected_template'] = None
    st.session_state['html_content'] = None
    st.session_state['file_saved'] = False
    st.session_state['generated_template'] = None

if 'parsed_json' not in st.session_state:
    st.session_state['parsed_json'] = None
if 'selected_template' not in st.session_state:
    st.session_state['selected_template'] = None
if 'html_content' not in st.session_state:
    st.session_state['html_content'] = None
if 'file_saved' not in st.session_state:
    st.session_state['file_saved'] = False
if 'generated_template' not in st.session_state:
    st.session_state['generated_template'] = None

llm_JSON = ChatGroq(model="gemma2-9b-it", temperature=0.3)
llm_Template_Selector = ChatGroq(model="gemma2-9b-it", temperature=1, cache=False)
llm_Template_Generator = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0.8, cache=False)

template_folder = "templates/"

def extract_text_from_pdf(pdf_path):
    text = ""
    docs = PyPDFLoader(pdf_path).load()
    for doc in docs:
        text += doc.page_content
    return text

def generate_json(text):
    prompt = f"""Convert the following text into structured JSON format suitable for a resume:
    {text}"""
    response = llm_JSON.invoke(prompt)
    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
    st.error("No valid JSON found.")
    return None

def select_template(parsed_json):
    prompt = f"""Based on the following resume data, select the best template from the available options:
        - modern
        - minimalist
        - dark_theme
        - creative
        - corporate
        - elegant
        - tech
        - artistic
        - classic
        - grid_based
    JSON Data: {json.dumps(parsed_json, indent=2)}
    Respond only with the template name."""
    response = llm_Template_Selector.invoke(prompt)
    selected_template = response.content.strip().lower()
    return selected_template if selected_template in ["modern", "minimalist", "dark_theme", "creative", "corporate", "elegant", "tech", "artistic", "classic", "grid_based"] else "tech"

def generate_html(parsed_json, template_name):
    generate_dynamic_template(parsed_json, template_name)
    template_path = os.path.join(template_folder, "generated_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
    template = Template(template_content)
    return template.render(**parsed_json)

# def generate_dynamic_template(parsed_json, template_theme):
    prompt = f"""Generate a professional, modern HTML+CSS+JS portfolio template for the following resume data:
    {json.dumps(parsed_json, indent=2)}
    Use the Theme:{template_theme}. Use Jinja2 placeholders for dynamic data insertion. Use advanced CSS from TailwindCSS. Use FontAwesome icons. Add advanced animations with GSAP and smooth scrolling. Use cards or carousel effects for lists. Ensure modern, sleek, and visually appealing design. Integrate Three.js for interactive 3D effects and include hover animations on buttons. """
    response = llm_Template_Generator.invoke(prompt)
    generated_template = response.content.strip()
    html_match = re.search(r'(<html.*</html>)', generated_template, re.DOTALL)
    if html_match:
        cleaned_template = html_match.group(0)
        template_path = os.path.join(template_folder, "generated_template.html")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(cleaned_template)
        st.session_state['generated_template'] = "generated_template"
        return cleaned_template
    return None

def generate_dynamic_template(parsed_json, template_theme):
    prompt = f"""Generate a professional, modern HTML+CSS+JS portfolio template with a high-level Three.js integration for the following resume data:
    {json.dumps(parsed_json, indent=2)}
    
    **Enhancements:**
    - Use **Three.js** for immersive 3D background with particles or an animated 3D model.
    - Fill all the sections, ensuring no section is left empty.
    - Fil the details correctly the content should always match with the section box.
    -Ensure that the color of the text is always varied
    -Keep all the details in the center.
    -Importantly no block should be empty.
    - If the background color of the grids are light then the text should be dark and vicevers.
    -Ensure the nav bar is placed correctly at the top.
    - Implement **smooth scrolling** and **GSAP transitions**.
    - Use **TailwindCSS** for modern styling.
    - Add **hover effects** and **click interactions** on buttons.
    - Use **cards, grids, or carousel effects** for content.
    - Ensure a **fully responsive design**.
    - Ensure the order is "Name with small intro, Experience, about me, Achievements, Education, Contact details, Link".
    - Ensure you follow the "60/ 30/ 10" principle while designingthe website.
    -Ensure the nav bar is never getting disturbed and ensure there is a minmum gap between the navbar andother sections.
    - Ensure you follow the following templates only:
      "- modern,
        - minimalist,
        - dark_theme,
        - creative,
        - corporate,
        - elegant,
        - tech,
        - artistic,
        - classic,
        - grid_based."

    **Tech Stack:** HTML, CSS (Tailwind), JavaScript (Three.js, GSAP, Angular, React JS).  

    Use **Jinja2 placeholders** for dynamic data insertion. Include proper `<script>` tags and ensure all Three.js animations load efficiently."""
    
    response = llm_Template_Generator.invoke(prompt)
    generated_template = response.content.strip()
    
    html_match = re.search(r'(<html.*</html>)', generated_template, re.DOTALL)
    if html_match:
        cleaned_template = html_match.group(0)
        template_path = os.path.join(template_folder, "generated_template.html")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(cleaned_template)
        st.session_state['generated_template'] = "generated_template"
        return cleaned_template
    
    return None

st.title("Resume to Portfolio Converter")
st.write("Upload your resume PDF to generate a professional portfolio with stunning 3D effects and animations.")
uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf", on_change=reset_state)
generate_portfolio = st.button("Generate Portfolio")

if generate_portfolio and uploaded_file:
    with st.spinner("Processing PDF..."):
        pdf_path = os.path.join("resume", uploaded_file.name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        resume_text = extract_text_from_pdf(pdf_path)
        os.remove(pdf_path)
        if st.session_state['parsed_json'] is None:
            st.session_state['parsed_json'] = generate_json(resume_text)
            with open("parser.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(st.session_state['parsed_json'], indent=4))
        st.session_state['selected_template'] = select_template(st.session_state['parsed_json'])
        st.session_state['html_content'] = generate_html(st.session_state['parsed_json'], st.session_state['selected_template'])
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(st.session_state['html_content'])
        st.session_state['file_saved'] = True
elif uploaded_file:
    st.write("Click on generate portfolio")

if st.session_state['file_saved']:
    st.markdown("### Your interactive portfolio is ready!")
    st.markdown("**If satisfied, click on Download. If not, click again on Generate Portfolio.**")
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=800, scrolling=True)
    st.download_button(label="Download Portfolio", data=html_content, file_name="index.html", mime="text/html")

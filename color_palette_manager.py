import streamlit as st
import colorsys
import json
from datetime import datetime
from fpdf import FPDF
import math
import io

# Configuration de la page
st.set_page_config(
    page_title="Gestionnaire de Palettes - Marketing Tools",
    page_icon="🎨",
    layout="wide"
)

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def hex_to_rgb(hex_color):
    """Convertit HEX en RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Convertit RGB en HEX"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def rgb_to_hsl(rgb):
    """Convertit RGB en HSL"""
    r, g, b = [x/255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (int(h * 360), int(s * 100), int(l * 100))

def hsl_to_rgb(hsl):
    """Convertit HSL en RGB"""
    h, s, l = hsl[0]/360.0, hsl[1]/100.0, hsl[2]/100.0
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))

def calculate_luminance(rgb):
    """Calcule la luminance relative d'une couleur"""
    rgb_normalized = [x/255.0 for x in rgb]
    rgb_linear = []
    for val in rgb_normalized:
        if val <= 0.03928:
            rgb_linear.append(val / 12.92)
        else:
            rgb_linear.append(((val + 0.055) / 1.055) ** 2.4)
    return 0.2126 * rgb_linear[0] + 0.7152 * rgb_linear[1] + 0.0722 * rgb_linear[2]

def calculate_contrast_ratio(rgb1, rgb2):
    """Calcule le ratio de contraste entre deux couleurs"""
    lum1 = calculate_luminance(rgb1)
    lum2 = calculate_luminance(rgb2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)

def get_wcag_level(ratio):
    """Détermine le niveau WCAG basé sur le ratio de contraste"""
    if ratio >= 7:
        return "AAA (texte normal et large)", "✅"
    elif ratio >= 4.5:
        return "AA (texte normal) / AAA (texte large)", "✅"
    elif ratio >= 3:
        return "AA (texte large uniquement)", "⚠️"
    else:
        return "Échec WCAG", "❌"

# ============================================================================
# MODULE 1 : GÉNÉRATEUR DE PALETTES
# ============================================================================

def generate_palette(base_color_hex, harmony_type):
    """Génère une palette selon le type d'harmonie"""
    rgb = hex_to_rgb(base_color_hex)
    h, s, l = rgb_to_hsl(rgb)
    
    palette = {
        "Couleur de base": base_color_hex
    }
    
    if harmony_type == "Monochrome":
        # Variations de luminosité
        palette["Tres clair"] = rgb_to_hex(hsl_to_rgb((h, s, min(90, l + 30))))
        palette["Clair"] = rgb_to_hex(hsl_to_rgb((h, s, min(80, l + 15))))
        palette["Fonce"] = rgb_to_hex(hsl_to_rgb((h, s, max(20, l - 15))))
        palette["Tres fonce"] = rgb_to_hex(hsl_to_rgb((h, s, max(10, l - 30))))
        
    elif harmony_type == "Analogique":
        # Couleurs adjacentes sur le cercle chromatique
        palette["Analogique -30deg"] = rgb_to_hex(hsl_to_rgb(((h - 30) % 360, s, l)))
        palette["Analogique +30deg"] = rgb_to_hex(hsl_to_rgb(((h + 30) % 360, s, l)))
        palette["Analogique -60deg"] = rgb_to_hex(hsl_to_rgb(((h - 60) % 360, s, l)))
        
    elif harmony_type == "Complémentaire":
        # Couleur opposée
        palette["Complementaire"] = rgb_to_hex(hsl_to_rgb(((h + 180) % 360, s, l)))
        palette["Comp. claire"] = rgb_to_hex(hsl_to_rgb(((h + 180) % 360, s, min(80, l + 15))))
        palette["Comp. foncee"] = rgb_to_hex(hsl_to_rgb(((h + 180) % 360, s, max(20, l - 15))))
        
    elif harmony_type == "Triadique":
        # Trois couleurs équidistantes
        palette["Triadique +120deg"] = rgb_to_hex(hsl_to_rgb(((h + 120) % 360, s, l)))
        palette["Triadique +240deg"] = rgb_to_hex(hsl_to_rgb(((h + 240) % 360, s, l)))
        
    elif harmony_type == "Tétradique":
        # Quatre couleurs en rectangle
        palette["Tetradique +90deg"] = rgb_to_hex(hsl_to_rgb(((h + 90) % 360, s, l)))
        palette["Tetradique +180deg"] = rgb_to_hex(hsl_to_rgb(((h + 180) % 360, s, l)))
        palette["Tetradique +270deg"] = rgb_to_hex(hsl_to_rgb(((h + 270) % 360, s, l)))
    
    return palette

# ============================================================================
# MODULE 3 : GÉNÉRATEUR DE NUANCES
# ============================================================================

def generate_shades(base_color_hex, num_shades=9):
    """Génère une échelle de nuances d'une couleur"""
    rgb = hex_to_rgb(base_color_hex)
    h, s, l = rgb_to_hsl(rgb)
    
    shades = {}
    step = 100 / (num_shades + 1)
    
    for i in range(num_shades):
        lightness = int(95 - (i * step))
        shade_name = f"Nuance {i+1} ({lightness}%)"
        shades[shade_name] = rgb_to_hex(hsl_to_rgb((h, s, lightness)))
    
    return shades

# ============================================================================
# MODULE 5 : HARMONISEUR
# ============================================================================

def analyze_harmony(colors):
    """Analyse l'harmonie d'une palette de couleurs"""
    if len(colors) < 2:
        return "Ajoutez au moins 2 couleurs pour analyser l'harmonie."
    
    hues = []
    saturations = []
    lightnesses = []
    
    for color in colors:
        rgb = hex_to_rgb(color)
        h, s, l = rgb_to_hsl(rgb)
        hues.append(h)
        saturations.append(s)
        lightnesses.append(l)
    
    # Analyse de la distribution des teintes
    hue_range = max(hues) - min(hues)
    sat_range = max(saturations) - min(saturations)
    light_range = max(lightnesses) - min(lightnesses)
    
    analysis = []
    
    # Distribution des teintes
    if hue_range < 30:
        analysis.append("✅ Palette monochrome - harmonie par teinte unifiée")
    elif 50 <= hue_range <= 90:
        analysis.append("✅ Palette analogique - harmonie douce")
    elif 150 <= hue_range <= 210:
        analysis.append("✅ Palette complémentaire - fort contraste")
    else:
        analysis.append("⚠️ Teintes variées - vérifier la cohérence visuelle")
    
    # Saturation
    if sat_range < 20:
        analysis.append("✅ Saturation cohérente")
    else:
        analysis.append("⚠️ Saturations très différentes - peut manquer d'unité")
    
    # Luminosité
    if light_range < 30:
        analysis.append("⚠️ Luminosités similaires - manque de hiérarchie")
    elif light_range > 70:
        analysis.append("✅ Bon contraste de luminosité")
    else:
        analysis.append("✅ Luminosités équilibrées")
    
    return "\n".join(analysis)

# ============================================================================
# EXPORTS
# ============================================================================

def export_to_figma_styles(palette, palette_name):
    """Exporte au format JSON compatible avec les plugins Figma Style"""
    styles = []
    for name, color in palette.items():
        rgb = hex_to_rgb(color)
        styles.append({
            "name": f"{palette_name}/{name}",
            "type": "color",
            "value": {
                "r": rgb[0] / 255,
                "g": rgb[1] / 255,
                "b": rgb[2] / 255,
                "a": 1
            }
        })
    return json.dumps({"styles": styles}, indent=2)

def export_to_figma_variables(palette, palette_name):
    """Exporte au format JSON compatible avec Figma Variables"""
    variables = {}
    for name, color in palette.items():
        rgb = hex_to_rgb(color)
        variable_name = f"{palette_name}/{name}".replace(" ", "-").lower()
        variables[variable_name] = {
            "type": "color",
            "value": {
                "r": rgb[0] / 255,
                "g": rgb[1] / 255,
                "b": rgb[2] / 255,
                "a": 1
            }
        }
    return json.dumps({"variables": variables}, indent=2)

def generate_pdf(palette, palette_name, include_contrast=True, include_shades=True):
    """Génère un PDF avec la palette"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    
    # Titre (encode to latin-1 compatible)
    safe_palette_name = palette_name.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, safe_palette_name, ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    
    # Couleurs principales
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Palette principale", ln=True)
    pdf.ln(2)
    
    y_position = pdf.get_y()
    for i, (name, color) in enumerate(palette.items()):
        if i > 0 and i % 3 == 0:
            y_position += 35
            pdf.set_y(y_position)
        
        x_position = 10 + (i % 3) * 65
        pdf.set_xy(x_position, y_position)
        
        # Rectangle de couleur
        rgb = hex_to_rgb(color)
        pdf.set_fill_color(rgb[0], rgb[1], rgb[2])
        pdf.rect(x_position, y_position, 60, 25, "F")
        
        # Nom et codes (remove accents for PDF compatibility)
        safe_name = name.replace('è', 'e').replace('é', 'e').replace('à', 'a').replace('ù', 'u')
        pdf.set_xy(x_position, y_position + 26)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(60, 4, safe_name, align="C")
        pdf.set_xy(x_position, y_position + 30)
        pdf.set_font("Arial", "", 8)
        pdf.cell(60, 3, color.upper(), align="C")
    
    # Matrice de contraste
    if include_contrast and len(palette) >= 2:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Matrice de contraste WCAG", ln=True)
        pdf.ln(2)
        pdf.set_font("Arial", "", 9)
        
        colors_list = list(palette.items())
        for i, (name1, color1) in enumerate(colors_list):
            for j, (name2, color2) in enumerate(colors_list):
                if i < j:
                    rgb1 = hex_to_rgb(color1)
                    rgb2 = hex_to_rgb(color2)
                    ratio = calculate_contrast_ratio(rgb1, rgb2)
                    level, icon = get_wcag_level(ratio)
                    
                    # Remove accents from names
                    safe_name1 = name1.replace('è', 'e').replace('é', 'e').replace('à', 'a').replace('ù', 'u')
                    safe_name2 = name2.replace('è', 'e').replace('é', 'e').replace('à', 'a').replace('ù', 'u')
                    safe_level = level.replace('è', 'e').replace('é', 'e').replace('à', 'a').replace('ù', 'u')
                    
                    pdf.cell(0, 6, f"{icon} {safe_name1} / {safe_name2}: {ratio:.2f}:1 - {safe_level}", ln=True)
    
    # Use BytesIO to avoid encoding issues
    pdf_output = io.BytesIO()
    pdf_string = pdf.output(dest='S')
    if isinstance(pdf_string, str):
        pdf_output.write(pdf_string.encode('latin-1', 'replace'))
    else:
        pdf_output.write(pdf_string)
    return pdf_output.getvalue()

# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

st.title("🎨 Gestionnaire de Palettes - Marketing Tools")
st.markdown("*Outil complet de création et gestion de palettes de couleurs*")

# Initialisation du state
if 'saved_palette' not in st.session_state:
    st.session_state.saved_palette = {}
if 'palette_name' not in st.session_state:
    st.session_state.palette_name = "Ma Palette"

# Tabs pour les modules
tabs = st.tabs([
    "🎨 Générateur de palettes",
    "✅ Vérificateur de contraste",
    "🌈 Générateur de nuances",
    "💾 Explorateur & Export",
    "🔍 Harmoniseur"
])

# ============================================================================
# TAB 1: GÉNÉRATEUR DE PALETTES
# ============================================================================

with tabs[0]:
    st.header("Générateur de palettes")
    st.markdown("Créez des palettes harmonieuses à partir d'une couleur de base")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        base_color = st.color_picker("Couleur de base", "#3B82F6")
        harmony = st.selectbox(
            "Type d'harmonie",
            ["Monochrome", "Analogique", "Complémentaire", "Triadique", "Tétradique"]
        )
        
        if st.button("Générer la palette", type="primary"):
            generated = generate_palette(base_color, harmony)
            st.session_state.saved_palette.update(generated)
            st.success(f"✅ {len(generated)} couleurs ajoutées à votre palette !")
    
    with col2:
        generated = generate_palette(base_color, harmony)
        st.subheader("Aperçu de la palette")
        
        # Affichage en grille
        cols = st.columns(3)
        for idx, (name, color) in enumerate(generated.items()):
            with cols[idx % 3]:
                st.markdown(
                    f"""
                    <div style="background-color: {color}; padding: 40px; border-radius: 8px; 
                                margin-bottom: 10px; border: 1px solid #ddd;">
                    </div>
                    <p style="text-align: center; font-weight: bold;">{name}</p>
                    <p style="text-align: center; font-size: 0.9em; color: #666;">{color.upper()}</p>
                    """,
                    unsafe_allow_html=True
                )

# ============================================================================
# TAB 2: VÉRIFICATEUR DE CONTRASTE
# ============================================================================

with tabs[1]:
    st.header("Vérificateur de contraste WCAG")
    st.markdown("Vérifiez l'accessibilité de vos combinaisons de couleurs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        text_color = st.color_picker("Couleur du texte", "#000000")
        bg_color = st.color_picker("Couleur du fond", "#FFFFFF")
    
    with col2:
        rgb_text = hex_to_rgb(text_color)
        rgb_bg = hex_to_rgb(bg_color)
        ratio = calculate_contrast_ratio(rgb_text, rgb_bg)
        level, icon = get_wcag_level(ratio)
        
        st.metric("Ratio de contraste", f"{ratio:.2f}:1")
        st.info(f"{icon} **Niveau WCAG:** {level}")
        
        # Aperçu visuel
        st.markdown("### Aperçu")
        st.markdown(
            f"""
            <div style="background-color: {bg_color}; padding: 30px; border-radius: 8px;">
                <p style="color: {text_color}; font-size: 16px; margin: 0;">
                    Texte normal (16px)
                </p>
                <p style="color: {text_color}; font-size: 24px; font-weight: bold; margin: 10px 0 0 0;">
                    Texte large (24px bold)
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Suggestions si contraste insuffisant
    if ratio < 4.5:
        st.warning("⚠️ Suggestions pour améliorer le contraste:")
        
        # Assombrir le texte
        h, s, l = rgb_to_hsl(rgb_text)
        darker_text = rgb_to_hex(hsl_to_rgb((h, s, max(0, l - 20))))
        
        # Éclaircir le fond
        h2, s2, l2 = rgb_to_hsl(rgb_bg)
        lighter_bg = rgb_to_hex(hsl_to_rgb((h2, s2, min(100, l2 + 20))))
        
        col_a, col_b = st.columns(2)
        with col_a:
            new_ratio1 = calculate_contrast_ratio(hex_to_rgb(darker_text), rgb_bg)
            st.markdown(f"**Texte plus foncé:** {darker_text}")
            st.markdown(f"Nouveau ratio: {new_ratio1:.2f}:1")
        
        with col_b:
            new_ratio2 = calculate_contrast_ratio(rgb_text, hex_to_rgb(lighter_bg))
            st.markdown(f"**Fond plus clair:** {lighter_bg}")
            st.markdown(f"Nouveau ratio: {new_ratio2:.2f}:1")

# ============================================================================
# TAB 3: GÉNÉRATEUR DE NUANCES
# ============================================================================

with tabs[2]:
    st.header("Générateur de nuances")
    st.markdown("Créez des échelles de couleurs pour vos design systems")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        shade_color = st.color_picker("Couleur de base", "#8B5CF6")
        num_shades = st.slider("Nombre de nuances", 5, 15, 9)
        
        if st.button("Générer les nuances", type="primary"):
            shades = generate_shades(shade_color, num_shades)
            st.session_state.saved_palette.update(shades)
            st.success(f"✅ {len(shades)} nuances ajoutées !")
    
    with col2:
        shades = generate_shades(shade_color, num_shades)
        st.subheader("Échelle de nuances")
        
        # Affichage en barre dégradée
        for name, color in shades.items():
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="background-color: {color}; width: 70%; height: 40px; 
                                border-radius: 4px; margin-right: 15px; border: 1px solid #ddd;">
                    </div>
                    <div style="width: 30%;">
                        <strong>{name.split('(')[0]}</strong><br>
                        <span style="color: #666; font-size: 0.9em;">{color.upper()}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# ============================================================================
# TAB 4: EXPLORATEUR & EXPORT
# ============================================================================

with tabs[3]:
    st.header("Explorateur de palette & Export")
    
    # Nom de la palette
    st.session_state.palette_name = st.text_input(
        "Nom de la palette",
        st.session_state.palette_name
    )
    
    if st.session_state.saved_palette:
        st.subheader("Votre palette actuelle")
        
        # Affichage de toutes les couleurs sauvegardées
        cols = st.columns(4)
        for idx, (name, color) in enumerate(st.session_state.saved_palette.items()):
            with cols[idx % 4]:
                st.markdown(
                    f"""
                    <div style="background-color: {color}; padding: 30px; border-radius: 8px; 
                                margin-bottom: 8px; border: 1px solid #ddd;">
                    </div>
                    <p style="text-align: center; font-size: 0.85em;"><strong>{name}</strong></p>
                    <p style="text-align: center; font-size: 0.8em; color: #666;">{color.upper()}</p>
                    """,
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        
        # Options d'export
        st.subheader("📥 Exporter votre palette")
        
        export_cols = st.columns(3)
        
        with export_cols[0]:
            # Export PDF
            pdf_bytes = generate_pdf(
                st.session_state.saved_palette,
                st.session_state.palette_name,
                include_contrast=True,
                include_shades=True
            )
            st.download_button(
                label="📄 Télécharger PDF",
                data=pdf_bytes,
                file_name=f"{st.session_state.palette_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        with export_cols[1]:
            # Export Figma Styles
            figma_styles_json = export_to_figma_styles(
                st.session_state.saved_palette,
                st.session_state.palette_name
            )
            st.download_button(
                label="🎨 Figma Styles JSON",
                data=figma_styles_json,
                file_name=f"{st.session_state.palette_name.replace(' ', '_')}_styles.json",
                mime="application/json",
                use_container_width=True
            )
        
        with export_cols[2]:
            # Export Figma Variables
            figma_vars_json = export_to_figma_variables(
                st.session_state.saved_palette,
                st.session_state.palette_name
            )
            st.download_button(
                label="🔷 Figma Variables JSON",
                data=figma_vars_json,
                file_name=f"{st.session_state.palette_name.replace(' ', '_')}_variables.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Autres formats
        st.markdown("### Autres formats")
        
        other_cols = st.columns(2)
        
        with other_cols[0]:
            # CSS Variables
            css_vars = ":root {\n"
            for name, color in st.session_state.saved_palette.items():
                var_name = name.replace(" ", "-").lower()
                css_vars += f"  --{var_name}: {color};\n"
            css_vars += "}"
            
            st.download_button(
                label="💅 CSS Variables",
                data=css_vars,
                file_name="palette.css",
                mime="text/css",
                use_container_width=True
            )
        
        with other_cols[1]:
            # JSON simple
            simple_json = json.dumps(st.session_state.saved_palette, indent=2)
            st.download_button(
                label="📋 JSON Simple",
                data=simple_json,
                file_name="palette.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Bouton pour vider la palette
        if st.button("🗑️ Vider la palette", type="secondary"):
            st.session_state.saved_palette = {}
            st.rerun()
    
    else:
        st.info("👆 Utilisez les modules ci-dessus pour créer votre palette, puis revenez ici pour l'exporter !")

# ============================================================================
# TAB 5: HARMONISEUR
# ============================================================================

with tabs[4]:
    st.header("Harmoniseur de palette")
    st.markdown("Analysez et améliorez l'harmonie de vos palettes existantes")
    
    st.subheader("Ajouter des couleurs à analyser")
    
    # Interface pour ajouter plusieurs couleurs
    num_colors = st.number_input("Nombre de couleurs", min_value=2, max_value=10, value=3)
    
    colors_to_analyze = []
    cols = st.columns(min(5, num_colors))
    
    for i in range(num_colors):
        with cols[i % 5]:
            color = st.color_picker(f"Couleur {i+1}", f"#{i*30:02x}{i*50:02x}{i*70:02x}", key=f"harmony_{i}")
            colors_to_analyze.append(color)
    
    if st.button("Analyser l'harmonie", type="primary"):
        analysis = analyze_harmony(colors_to_analyze)
        
        st.subheader("Résultat de l'analyse")
        st.info(analysis)
        
        # Visualisation
        st.subheader("Visualisation")
        color_html = ""
        for color in colors_to_analyze:
            color_html += f'<div style="background-color: {color}; width: {100/len(colors_to_analyze)}%; height: 100px; display: inline-block;"></div>'
        
        st.markdown(
            f'<div style="display: flex; border-radius: 8px; overflow: hidden; border: 1px solid #ddd;">{color_html}</div>',
            unsafe_allow_html=True
        )
        
        # Données détaillées
        st.subheader("Données détaillées")
        data_cols = st.columns(len(colors_to_analyze))
        
        for idx, color in enumerate(colors_to_analyze):
            with data_cols[idx]:
                rgb = hex_to_rgb(color)
                h, s, l = rgb_to_hsl(rgb)
                st.markdown(f"**Couleur {idx+1}**")
                st.markdown(f"HEX: `{color.upper()}`")
                st.markdown(f"RGB: `({rgb[0]}, {rgb[1]}, {rgb[2]})`")
                st.markdown(f"HSL: `({h}°, {s}%, {l}%)`")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("À propos")
    st.markdown("""
    ### 🎨 Gestionnaire de Palettes
    
    **5 Modules puissants:**
    
    1. **Générateur de palettes** - Créez des harmonies automatiques
    2. **Vérificateur de contraste** - Assurez l'accessibilité WCAG
    3. **Générateur de nuances** - Échelles pour design systems
    4. **Explorateur & Export** - PDF + Figma + CSS
    5. **Harmoniseur** - Analysez vos palettes
    
    ---
    
    ### 💡 Astuce
    Combinez les modules ! Par exemple :
    1. Générez une palette complémentaire
    2. Créez des nuances pour chaque couleur
    3. Vérifiez les contrastes
    4. Exportez vers Figma
    
    ---
    
    **Formats d'export:**
    - 📄 PDF avec aperçus visuels
    - 🎨 JSON Figma Styles
    - 🔷 JSON Figma Variables
    - 💅 CSS Variables
    - 📋 JSON simple
    """)
    
    st.markdown("---")
    st.caption(f"Palette actuelle: **{len(st.session_state.saved_palette)}** couleurs")

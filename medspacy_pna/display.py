import re
from spacy import displacy

target_labels = {"PNEUMONIA", "CONSOLIDATION", "INFILTRATE", "OPACITY"}

def keep_ent(ent):
    if ent.label_ not in target_labels:
        return False
    if ent.text.lower() == "cap" and ent._.is_ignored:
        return False
    return True

TPL_ENT = """
<mark class="entity" style="background: {bg}; padding: 0.25em 0.6em; margin: 0 0.25em; line-height: 1.5; border-radius: 0.35em;">
    {text}
    <span style="font-size: 0.8em; font-weight: bold; line-height: 2.5; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">{label}</span>
</mark>
"""

ENTITIES_DIV_DEFAULT = 'class="entities" style="line-height: 2.5'

keep_ents = {
    "PNEUMONIA",
    "OPACITY",
    "CONSOLIDATION",
    "INFILTRATE",
    "RAD_PNEUMONIA"
}

keep_modifiers = {
    "HISTORICAL", "NEGATED_EXISTENCE", "HYPOTHETICAL",
    "POSSIBLE_EXISTENCE", "FAMILY", "POSITIVE_EXISTENCE",

}




DISPLAY_COLORS = {
    "PNEUMONIA": "#ff8c8c",  # Red
    "OPACITY": "#ff8c8c",
    "CONSOLIDATION": "#ff8c8c",
    "INFILTRATE": "#ff8c8c",
    "RAD_PNEUMONIA": "#ff8c8c",

    "POSITIVE_EXISTENCE": "#e3dede",  # gray
    "NEGATED_EXISTENCE": "#e3dede",  # gray
    "POSSIBLE_EXISTENCE": "#e3dede",  # gray
    "HISTORICAL": "#e3dede",  # gray
    #     "diagnoses":
    # Blue for "target sections", other sections light green, similar alpha to blue
    # "Impression" for radiology, "mdm"/"diagnoses"/"a/p" for ED notes

}

TARGET_SECTION_COLOR = "#17becf"
TARGET_SECTION_COLOR = "#96eaf2"
OTHER_SECTION_COLOR = "#c8fae4"

def build_colors(domain, target_section_color=TARGET_SECTION_COLOR):
    colors = dict(DISPLAY_COLORS)
    from .document_classification import get_relevant_sections
    for section in get_relevant_sections()[domain]:
        colors[f"<< {section.upper()} >>"] = target_section_color
    return colors


keep_ents = {
    "PNEUMONIA",
    "OPACITY",
    "CONSOLIDATION",
    "INFILTRATE",
    "RAD_PNEUMONIA"
}

keep_modifiers = {
    "HISTORICAL", "NEGATED_EXISTENCE", "HYPOTHETICAL",
    "POSSIBLE_EXISTENCE", "FAMILY", "POSITIVE_EXISTENCE",

}

LEGEND_TEMPLATE = """
<mark class="entity" style="background: {color}; padding: 0.25em 0.6em; margin: 0 0.25em; line-height: 1.5; border-radius: 0.35em;">
    {text}
<span style="font-size: 1.0em; font-weight: bold; line-height: 2.5; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">{label}</span>
</mark>
"""

def create_legend(domain="emergency", label_colors=None, add_br=False):
    if label_colors is None:
        colors = build_colors(domain)
        label_colors = {
            "Pneumonia": colors["PNEUMONIA"],
            "Assertion Modifier": colors["POSITIVE_EXISTENCE"],
            "Primary Section Title": TARGET_SECTION_COLOR,
            "Other Section Title": OTHER_SECTION_COLOR
        }
    legend = "<h1>Legend</h1>"
    for (label, color) in label_colors.items():
        legend += LEGEND_TEMPLATE.format(text="", label=label, color=color)
        if add_br:
            legend += "</br>"
    legend += "</br>"
    if domain == "emergency":
        nt = "Emergency Note"
    elif domain == "radiology":
        nt = "Radiology Report"
    else:
        nt = "Discharge Summary"
    legend += "<h1>{nt}</h1>".format(nt=nt)
    return legend

def create_html(doc, domain, add_legend=True, context=True, default_section_color="#c8fae4", document_classification=False,
                colors=None,
                line_height=1.25,
                meta=None):
    from medspacy.visualization import _create_color_generator, _create_color_mapping
    from spacy import displacy
    if colors is None:
        colors = build_colors(domain)
    else:
        colors = dict(colors)
    # Make sure that doc has the custom medSpaCy attributes registered
    if not hasattr(doc._, "context_graph"):
        context = False
    if not hasattr(doc._, "sections"):
        default_section_color = False

    ents_data = []

    for target in doc.ents:
        if target.label_ not in keep_ents:
            continue
        ent_data = {
            "start": target.start_char,
            "end": target.end_char,
            "label": target.label_.upper(),
        }
        ents_data.append((ent_data, "ent"))

    if context:
        visualized_modifiers = set()
        for target in doc.ents:
            if target.label_ not in keep_ents:
                continue
            for modifier in target._.modifiers:
                if modifier.category not in keep_modifiers:
                    continue
                if modifier in visualized_modifiers:
                    continue
                ent_data = {
                    "start": modifier.span.start_char,
                    "end": modifier.span.end_char,
                    "label": modifier.category,
                }
                ents_data.append((ent_data, "modifier"))
                visualized_modifiers.add(modifier)
    if default_section_color:
        for section in doc._.sections:
            category = section.category
            if category is None or category.upper() == "OTHER":
                continue


            ent_data = {
                "start": section.title_span.start_char,
                "end": section.title_span.end_char,
                "label": f"<< {category.upper()} >>",
            }
            ents_data.append((ent_data, "section"))
    if len(ents_data) == 0:  # No data to display
        viz_data = [{"text": doc.text, "ents": []}]
        options = dict(template=TPL_ENT)
    else:
        ents_data = sorted(ents_data, key=lambda x: x[0]["start"])

        # If colors aren't defined, generate color mappings for each entity
        # and modifier label and set all section titles to a light gray
        if colors is None:
            labels = set()
            section_titles = set()
            for (ent_data, ent_type) in ents_data:
                if ent_type in ("ent", "modifier"):
                    labels.add(ent_data["label"])
                elif ent_type == "section":
                    section_titles.add(ent_data["label"])
            colors = _create_color_mapping(labels)

            for title in section_titles:

                colors[title] = default_section_color
        else:
            for (ent_data, ent_type) in ents_data:
                if ent_type == "section":
                    if ent_data["label"] not in colors:
                        colors[ent_data["label"]] = default_section_color
        ents_display_data, _ = zip(*ents_data)
        viz_data = [{"text": doc.text, "ents": ents_display_data, }]

        options = {
            "colors": colors,
            "template": TPL_ENT
        }
    html = displacy.render(viz_data, style="ent", manual=True, options=options, jupyter=False)
    if line_height is not None:
        html = re.sub(ENTITIES_DIV_DEFAULT, 'class="entities" style="line-height: {0}'.format(line_height), html)
    if document_classification:
        html = f"<h2>NLP Document Classification: {doc._.document_classification}</h2>" + html
    if meta is not None:
        html = create_meta_string(meta) + html
    if add_legend:
        html = create_legend(domain) + html
    return html


def create_meta(row, keys=("Patient_ID", "Encounter_DateTime")):
    return {key: row[key] for key in keys}


def create_meta_string(meta):
    html = ""
    for k, v in meta.items():
        html += f"<h2>{k}: {v}</h2>"
    return html

import os, shutil, sys
from lxml import etree
from lxml.etree import Element

from datetime import date

DEFAULT_COLOR = (220, 220, 220)

base_schema_string = """<?xml version="1.0" encoding="UTF-8"?>
<eHOST_Project_Configure Version="1.0">
    <Handling_Text_Database>false</Handling_Text_Database>
    <OracleFunction_Enabled>false</OracleFunction_Enabled>
    <AttributeEditor_PopUp_Enabled>false</AttributeEditor_PopUp_Enabled>
    <OracleFunction>true</OracleFunction>
    <AnnotationBuilder_Using_ExactSpan>false</AnnotationBuilder_Using_ExactSpan>
    <OracleFunction_Using_WholeWord>true</OracleFunction_Using_WholeWord>
    <GraphicAnnotationPath_Enabled>true</GraphicAnnotationPath_Enabled>
    <Diff_Indicator_Enabled>true</Diff_Indicator_Enabled>
    <Diff_Indicator_Check_CrossSpan>true</Diff_Indicator_Check_CrossSpan>
    <Diff_Indicator_Check_Overlaps>false</Diff_Indicator_Check_Overlaps>
    <StopWords_Enabled>false</StopWords_Enabled>
    <Output_VerifySuggestions>false</Output_VerifySuggestions>
    <Pre_Defined_Dictionary_DifferentWeight>false</Pre_Defined_Dictionary_DifferentWeight>
    <PreAnnotated_Dictionaries Owner="NLP_Assistant" />
    <attributeDefs />
    <Relationship_Rules />
    <classDefs />
</eHOST_Project_Configure>
"""

base_annotations_string = """<?xml version="1.0" encoding="UTF-8"?>
<annotations textSource="0_10814621490">
    <eHOST_Adjudication_Status version="1.0">
        <Adjudication_Selected_Annotators version="1.0" />
        <Adjudication_Selected_Classes version="1.0" />
        <Adjudication_Others>
            <CHECK_OVERLAPPED_SPANS>false</CHECK_OVERLAPPED_SPANS>
            <CHECK_ATTRIBUTES>false</CHECK_ATTRIBUTES>
            <CHECK_RELATIONSHIP>false</CHECK_RELATIONSHIP>
            <CHECK_CLASS>false</CHECK_CLASS>
            <CHECK_COMMENT>false</CHECK_COMMENT>
        </Adjudication_Others>
    </eHOST_Adjudication_Status>
</annotations>"""

class EhostWriter:

    def __init__(self, annotation_labels=None, annotation_color_mapping=None, context=True, sections=True,
                 span_attributes=None):
        if annotation_labels is None:
            annotation_labels = set()
            self._allow_new_labels = True
        else:
            self._allow_new_labels = False
        self.annotation_labels = annotation_labels
        self.color_cycle = self._create_color_generator()
        if annotation_color_mapping is None:
            annotation_color_mapping = self.create_default_color_mapping(annotation_labels)
        self.annotation_color_mapping = annotation_color_mapping

        self.context = context
        self.sections = sections
        if span_attributes is None:
            span_attributes = {
                'is_family',
                 'is_historical',
                 'is_hypothetical',
                 'is_negated',
                 'is_uncertain',
            }
        self.span_attributes = span_attributes

        self._i = 0

    def write_docs_to_ehost(self, docs, report_ids, directory, schema_file=None, overwrite_directory=True):
        self.prepare_directory(directory, overwrite_directory)
        if schema_file is None:
            self.create_schema_file(directory)
        else:
            import shutil
            shutil.copy(schema_file, os.path.join(directory, "config", 'projectschema.xml'))

        # Now save the texts
        for (doc, report_id) in zip(docs, report_ids):
            self.save_text(doc, report_id, directory)
            xml = self.create_ehost_xml(doc)
            self.save_ehost_xml(xml, report_id, directory)

    def prepare_directory(self, directory, overwrite_directory=True):
        # First, make the parent directory
        if not os.path.exists(directory):
            os.mkdir(directory)
        else:
            if overwrite_directory:
                shutil.rmtree(directory)
            os.mkdir(directory)

        # Now create the three subdirectories
        corpus_dir = os.path.join(directory, "corpus")
        xmls_dir = os.path.join(directory, "xmls")
        saved_dir = os.path.join(directory, "saved")
        config_dir = os.path.join(directory, "config")

        os.mkdir(corpus_dir)
        os.mkdir(xmls_dir)
        os.mkdir(saved_dir)
        os.mkdir(config_dir)

    def create_schema_file(self, root_dir):
        filepath = os.path.join(root_dir, "config", "projectschema.xml")
        xml = etree.fromstring(base_schema_string.encode())
        self.add_public_attributes(xml)
        class_defs = xml.find('classDefs')
        for label, rgb in self.annotation_color_mapping.items():
            self.add_classdef(class_defs, label, rgb)
        with open(filepath, 'wb') as f:
            f.write(etree.tostring(xml, pretty_print=True))
        # print(f"Saved project config at {outpath}")

    def add_classdef(self, class_defs, label, color, inherit=True):
        class_def = Element('classDef')
        name = Element('Name', )
        name.text = label
        class_def.append(name)

        self.add_rgb_tags(class_def, color)

        # Add other tags
        sub = Element('InHerit_Public_Attributes')
        sub.text = str(inherit)
        class_def.append(sub)

        sub = Element('Source')
        sub.text = 'eHOST'
        class_def.append(sub)
        class_defs.append(class_def)

    def add_public_attributes(self, xml):
        # Now add the attributes defined in span_attributes
        attribute_defs = xml.find('attributeDefs')
        for attr in self.span_attributes:
            attribute_def = Element("attributeDef")
            name = Element("Name")
            name.text = attr
            attribute_def.append(name)
            # default_value = Element("defaultValue")
            # default_value.text = "false"
            # attribute_def.append(default_value)
            for value in ["false", "true"]:
                option_def = Element("attributeDefOptionDef")
                option_def.text = value
                attribute_def.append(option_def)

            for name in ["is_Linked_to_UMLS_CUICode_and_CUILabel",
                         "is_Linked_to_UMLS_CUICode",
                         "is_Linked_to_UMLS_CUILabel"]:
                sub_elem = Element(name)
                sub_elem.text = "false"
                attribute_def.append(sub_elem)

            attribute_defs.append(attribute_def)

    def add_rgb_tags(self, class_def, rgb):
        # Add RGB values
        for (value, name) in zip(rgb, ('RGB_R', 'RGB_G', 'RGB_B')):
            sub = Element(name)
            sub.text = str(value)
            class_def.append(sub)

    def save_text(self, doc, report_id, root_dir):
        corpus_dir = os.path.join(root_dir, "corpus")
        filepath = os.path.join(corpus_dir, "{}.txt".format(report_id))
        with open(filepath, "w") as f:
            f.write(doc.text)

        # print("I'm going to exit now:")
        # while True:
        #     pass


    def create_ehost_xml(self, doc):
        xml = etree.fromstring(base_annotations_string.encode())
        # Start with the entity spans
        for ent in doc.ents:
            if self._allow_new_labels is False and ent.label_ not in self.annotation_labels:
                continue
            # Start with the span attributes
            slot_mention_ids = []

            for attr in self.span_attributes:
                if getattr(ent._, attr) == True:
                    self.add_string_slot_mention(ent, attr, xml, self._i)
                    slot_mention_ids.append(self._i)
                    self._i += 1



            if ent.label_ not in self.annotation_color_mapping:
                self.annotation_color_mapping[ent.label_] = DEFAULT_COLOR
            self.add_annotation(ent, xml, self._i)
            self.add_class_mention(ent, ent.label_, xml, self._i, slot_mention_ids)
            self._i += 1

        # Now add optional context modifiers and section headers
        if self.context is True and hasattr(doc._, "context_graph"):
            for ent, modifier in doc._.context_graph.edges:
                if ent.label_ not in self.annotation_labels:
                    continue
                if modifier.category not in self.annotation_color_mapping:
                    self.annotation_color_mapping[modifier.category] = DEFAULT_COLOR
                self.add_annotation(modifier.span, xml, self._i)
                self.add_class_mention(modifier.span, modifier.category, xml, self._i, [])
                self._i += 1
        if self.sections is True and hasattr(doc._, "section_titles"):
            for title in doc._.section_titles:
                category = title._.section_category
                if category is None:
                    continue
                if category not in self.annotation_color_mapping:
                    self.annotation_color_mapping[category] = DEFAULT_COLOR
                self.add_annotation(title, xml, self._i)
                self.add_class_mention(title, category, xml, self._i, [])
                self._i += 1

        return xml

    def save_ehost_xml(self, xml, report_id, root_dir):
        saved_dir = os.path.join(root_dir, "saved")
        filepath = os.path.join(saved_dir, "{}.txt.knowtator.xml".format(report_id))
        with open(filepath, 'wb') as f:
            f.write(etree.tostring(xml, pretty_print=True))


    def add_annotation(self, span, xml, i):
        annotation = Element('annotation')
        # mention id
        mention = Element('mention', id=f'EHOST_Instance_{i}')
        annotation.append(mention)

        # annotator id
        annotator = Element('annotator', id='medSpaCy')
        annotator.text = 'medSpaCy'
        annotation.append(annotator)

        # span
        start = span.start_char
        end = start + len(span.text)
        span = Element('span', start=str(start), end=str(end))
        annotation.append(span)

        # spannedText
        spanned_text = Element('spannedText')
        spanned_text.text = span.text
        annotation.append(spanned_text)


        # creationDate
        # TODO

        xml.append(annotation)

    def add_class_mention(self, span, label, xml, i, slot_mention_ids):
        mention = Element('classMention', id=f'EHOST_Instance_{i}')

        mention_class = Element('mentionClass', id=label)
        # mention_class.text = span.text
        mention.append(mention_class)

        xml.append(mention)

        # Add references to the slot mentions which represent various attributes
        for slot_mention_id in slot_mention_ids:
            slot_mention_ref = Element("hasSlotMention", id=f"EHOST_Instance_{slot_mention_id}")
            mention.append(slot_mention_ref)

    def add_string_slot_mention(self, span, attr, xml, i):
        value = str(getattr(span._, attr)).lower()

        slot_mention = Element("stringSlotMention", id=f'EHOST_Instance_{i}')
        mention_slot = Element("mentionSlot", id=attr)
        slot_mention.append(mention_slot)
        mention_slot_value = Element("stringSlotMentionValue", value=value)
        slot_mention.append(mention_slot_value)

        xml.append(slot_mention)

        #     < stringSlotMention
        #     id = "EHOST_Instance_327" >
        #     < mentionSlot
        #     id = "is_negated" / >
        #     < stringSlotMentionValue
        #     value = "true" / >
        #
        # < / stringSlotMention >

    def create_default_color_mapping(self, labels):
        color_mapping = dict()
        for label in labels:
            hex_color = next(self.color_cycle)
            rgb = self._hex_to_rgb(hex_color)
            color_mapping[label] = rgb
        return color_mapping

    def _create_color_generator(self):
        """Create a generator which will cycle through a list of default matplotlib colors"""
        from itertools import cycle
        colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728',
                  u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']
        return cycle(colors)

    def _hex_to_rgb(self, h):
        h = h.strip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

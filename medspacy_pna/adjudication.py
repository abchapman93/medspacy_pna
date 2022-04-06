import os, glob
import pandas as pd
from lxml import etree

from medspacy.visualization import visualize_ent, visualize_dep
# from medspacy_pna.nlp.utils import build_nlp

DOCUMENT_ANNOTATION_CLASSES = {"DOCUMENT_POSITIVE": "POS", "DOCUMENT_POSSIBLE": "POS", "DOCUMENT_NEGATIVE": "NEG",
                               "DOCUMENT_NOT_MD_NOTE": "NEG", "DOCUMENT_BAD_NOTE": "NEG"}

attributes = ['is_negated', 'is_hypothetical', 'is_uncertain', 'is_historical']

def process_text(nlp, text):
    # Skip preprocessing
    try:
        doc = nlp.tokenizer.tokenizer(text)
    except AttributeError:
        doc = nlp.tokenizer(text)
    for _, component in nlp.pipeline:
        doc = component(doc)
    return doc


# def load_document_annotations(directory, nlp):
def load_ehost_batch(directory, nlp,  sub_directories=None, process_texts=True, annotator=None):

    ehost_df = load_ehost_annotations(directory, sub_directories)

    sub_dfs = []
    if annotator is not None:
        ehost_df["annotator"] = annotator
    annotators = set(ehost_df["annotator"])


    for annotator in annotators:
        sub_df = ehost_df[ehost_df["annotator"] == annotator]

        sub_df[f"{annotator}_document_classification"] = sub_df["document_classification"]
        sub_df[f"{annotator}_normalized_document_classification"] = sub_df[f"{annotator}_document_classification"].apply(lambda x:DOCUMENT_ANNOTATION_CLASSES.get(x))
        sub_dfs.append(sub_df[["filename", f"{annotator}_document_classification", f"{annotator}_normalized_document_classification"]])
    if len(sub_dfs) == 0:
        return pd.DataFrame()
    reference_standard = sub_dfs[0].copy()

    for sub_df in sub_dfs[1:]:
        reference_standard = pd.merge(reference_standard, sub_df, how="outer", on="filename")

    nlp_df = load_nlp_df(directory, nlp, sub_directories, process_texts)
    df = pd.merge(nlp_df, reference_standard, on="filename",how="outer")
    return df

def load_ehost_annotations(directory, sub_directories=None):

    if sub_directories is not None:
        xml_filepaths = []
        batches = []
        for sub_dir in sub_directories:
            xml_filepaths += glob.glob(os.path.join(directory, sub_dir, "saved", "*.xml"))
            batches += [sub_dir for filepath in xml_filepaths]
    else:
        xml_filepaths = glob.glob(os.path.join(directory, "saved", "*.xml"))
        batches = [os.path.basename(directory) for filepath in xml_filepaths]
    annotations = []
    class_mentions = []
    slot_mentions = []
    for filepath, batch in zip(xml_filepaths, batches):
        with open(filepath, "rb") as f:
            xml_text = f.read()
        xml = etree.fromstring(xml_text)
        filename = ".".join(os.path.basename(filepath).split(".")[:-2])
        annotations += [
            parse_annotation(filename, x, batch) for x in xml.findall("annotation") if x is not None]
        class_mentions += [parse_class_mention(filename, x) for x in xml.findall("classMention")]
        slot_mentions += [parse_string_slot_mention(filename, x) for x in xml.findall("stringSlotMention")]

    annotations = pd.DataFrame(annotations)
    class_mentions = pd.DataFrame(class_mentions)
    slot_mentions = pd.DataFrame(slot_mentions)


    ehost_df = pd.merge(pd.merge(annotations, class_mentions,
                                 on=["filename", "mention_id"],
                                 how="inner"),
                        slot_mentions,
                        left_on=["filename", "has_slot_mention"],
                        right_on=["filename", "string_slot_mention_id"],
                        how="left")

    ehost_df = ehost_df[ehost_df["mention_class"].isin(DOCUMENT_ANNOTATION_CLASSES)]
    # print(ehost_df[ehost_df["mention_class"] == "DOCUMENT_NOT_MD_NOTE"])
#     print(ehost_df)
    ehost_df = ehost_df.rename({"mention_class": "document_classification"}, axis=1)
    # TODO: if needed, get attributes

    return ehost_df

def load_nlp_df(directory, nlp, sub_directories=None, process_texts=True):
    if sub_directories is not None:
        text_filepaths = []
        for sub_dir in sub_directories:
            text_filepaths += glob.glob(os.path.join(directory, sub_dir, "corpus", "*.txt"))
    else:
        text_filepaths = glob.glob(os.path.join(directory, "corpus", "*.txt"))
    nlp_dicts = []
    for text_filepath in text_filepaths:
        with open(text_filepath) as f:
            text = f.read()
        if process_texts:
            doc = process_text(nlp, text)
        else:
            doc = None
        filename = os.path.basename(text_filepath)
        if process_texts:
            nlp_doc_class = doc._.document_classification
        else:
            nlp_doc_class = None
        d = {
            "filename": filename
            , "doc": doc
            , "nlp_document_classification": nlp_doc_class
        }
        nlp_dicts.append(d)

    nlp_df = pd.DataFrame(nlp_dicts)

    return nlp_df

def parse_annotation(filename, annotation, batch_name=None):
    d = {"filename": filename}
    mention_id = annotation.find("mention").get("id")
    d["mention_id"] = mention_id
    
    span = annotation.find("span")
    d["start"] = span.get("start")
    d["end"] = span.get("end")
    for key in ["annotator", "text", "creation_date"]:
        try:
            d[key] = annotation.find(key).text
        except:
            d[key] = None
#     d["annotator"] = annotation.find("annotator").text
#     d["text"] = annotation.find("spannedText").text
#     d["creation_date"] = annotation.find("creationDate").text
    d["batch_name"] = batch_name
    return d


def parse_class_mention(filename, class_mention):
    mention_id = class_mention.get("id")
    mention_class = class_mention.find("mentionClass").get("id")
    try:
        has_slot_mention = class_mention.find("hasSlotMention").get("id")
    except:
        has_slot_mention = None
    return {"mention_id": mention_id,
            "filename": filename,
            "has_slot_mention": has_slot_mention,
            "mention_class": mention_class,
            "filename": filename}


def parse_string_slot_mention(filename, string_slot_mention):
    mention_id = string_slot_mention.get("id")
    mention_slot = string_slot_mention.find("mentionSlot").get("id")
    value = string_slot_mention.find("stringSlotMentionValue").get("value")
    d = {"filename": filename, "string_slot_mention_id": mention_id}
    d["attribute"] = mention_slot
    d["value"] = value
    return d

def create_ents_df(df, nlp=None, reprocess_sent=False,
                   df_cols=("TIUDocumentSID", "final_document_classification", "nlp_document_classification")):
    ents = []
    medspacy_attrs = ("is_family", "is_historical", "is_hypothetical", "is_ignored",
                      "is_negated", "is_template", "is_uncertain", "section_title")

    for i, row in df.iterrows():
        for ent in row["doc"].ents:
            d = {
                "span": ent,
                "lower": ent.text.lower(),
                "label": ent.label_,
                "is_negated": ent._.is_negated,
                "sent": ent.sent,
                "nlp_document_classification": row["doc"]._.document_classification,
            }
            for col in df_cols:
                d[col] = row[col]
            for attr in medspacy_attrs:
                d[attr] = getattr(ent._, attr)
            target_rule = ent._.target_rule
            if target_rule is None:
                literal = ent.text.lower()
            else:
                literal = target_rule.literal
            d["literal"] = literal
            ents.append(d)

    ents_df = pd.DataFrame(ents)

    if reprocess_sent:
        if nlp is None:
            raise ValueError()
        ents_df["doc2"] = list(nlp.pipe([sent.text for sent in ents_df["sent"]]))
        ents_df["sent_classification"] = ents_df["doc2"].apply(lambda x: x._.document_classification)

    return ents_df

class MedspaCyVisualizerWidget:

    def __init__(self, docs, nlp, annotated_labels=None):

        """Create an IPython Widget Box displaying medspaCy's visualizers.
        The widget allows selecting visualization style ("Ent", "Dep", or "Both")
        and a slider for selecting the index of docs.

        For more information on IPython widgets, see:
            https://ipywidgets.readthedocs.io/en/latest/index.html

        Parameters:
            docs: A list of docs processed by a medspaCy pipeline

        """

        import ipywidgets as widgets
        from IPython.display import display

        self.docs = docs
        self.nlp = nlp
        if annotated_labels is None:
            annotated_labels = ["" for doc in docs]
        self.annotated_labels = annotated_labels
        self.slider = widgets.IntSlider(
            value=0,
            min=0,
            max=len(docs) - 1,
            step=1,
            description='Doc:',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d'
        )
        self.radio = widgets.RadioButtons(options=["Ent", "Dep", "Both"])
        self.layout = widgets.Layout(display='flex',
                                     flex_flow='column',
                                     align_items='stretch',
                                     width='100%')
        self.radio.observe(self._change_handler)
        self.slider.observe(self._change_handler)
        self.next_button = widgets.Button(description="Next")
        self.next_button.on_click(self._on_click_next)
        self.previous_button = widgets.Button(description="Previous")
        self.previous_button.on_click(self._on_click_prev)
        self.refresh_button = widgets.Button(description="Refresh")
        self.refresh_button.on_click(self._change_handler)
        self.output = widgets.Output()
        self.box = widgets.Box(
            [widgets.HBox([self.radio, self.previous_button,self.next_button]),
             self.slider,
             self.refresh_button,
             self.output],
            layout=self.layout
        )

        self.display()
        self.current_doc = self.docs[self.slider.value]
        with self.output:
            self._visualize_doc()

    def display(self):
        """Display the Box widget in the current IPython cell."""
        from IPython.display import display as ipydisplay
        ipydisplay(self.box)

    def _change_handler(self, change):
        self.current_doc = self.docs[self.slider.value]
        with self.output:
            self._visualize_doc()

    def _visualize_doc(self):
        self.output.clear_output()
        gold_label = self.annotated_labels[self.slider.value]
        if isinstance(self.current_doc, str):
            doc = self.nlp(self.current_doc)
        else:
            doc = self.current_doc
        if self.radio.value.lower() in ("dep", "both"):
            visualize_dep(doc)
        if self.radio.value.lower() in ("ent", "both"):
            # visualize_ent(doc)
            visualize_ent_gold_classification(doc, gold_label)

    def _on_click_next(self, b):
        if self.slider.value < len(self.docs) - 1:
            self.slider.value += 1

    def _on_click_prev(self, b):
        if self.slider.value > 0:
            self.slider.value -= 1

    def set_docs(self, docs):
        "Replace the list of docs to be visualized."
        self.docs = docs
        self._visualize_doc(self.docs[0])

def visualize_ent_gold_classification(doc, gold_label):
    from IPython.display import display, HTML
    html = ""
    html += f"<h1>Annotated label: {gold_label}</h1>"
    html += f"<h1>Predicted label: {doc._.document_classification}</h1>"
    html += visualize_ent(doc, jupyter=False)
    display(HTML(html))

LABELS = ["STABLY_HOUSED", "UNSTABLY_HOUSED", "UNKNOWN", ]
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def create_confusion_matrix(y1, y2, labels, margins=True):

    conf = pd.DataFrame(confusion_matrix(y1, y2, labels=LABELS), columns=LABELS)
    conf.index = LABELS

    if margins:
        cols_sum = conf.sum(axis=0)
        cols_sum.name = f"{labels[0]}_total"
        conf = conf.append(cols_sum)

        rows_sum = conf.sum(axis=1)
        rows_sum.name = f"{labels[1]}_total"
        conf = pd.concat([conf, rows_sum], axis=1)

    return conf


def plot_confusion_matrix(y1, y2, labels, margins=True):
    conf = create_confusion_matrix(y1, y2, labels, margins)
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(conf, ax=ax, annot=True)
    ax.set_title("Confusion Matrix of Document Clasifications")
    ax.set_ylabel(labels[0])
    ax.set_xlabel(labels[1])

    # Fix cut off plot
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom + 0.5, top - 0.5)

    return fig, ax
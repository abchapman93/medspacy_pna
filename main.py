import os
from argparse import ArgumentParser
import warnings
import pandas as pd

from medspacy.io import DocConsumer, DbConnect, DbWriter

from src.util import build_nlp, create_connection_sql13
from src.constants import DOMAINS
from spacy.tokens import Span, Doc

import pyodbc

DTYPE_ATTRS = {
    "ent": [
      'text',
      'start_char',
      'end_char',
      'label_',
      'is_negated',
      'is_uncertain',
      'is_historical',
      'is_hypothetical',
      'is_family',
      'section_category',
      'snippet'
    ],
    "context": [
        'ent_text',
          'ent_label_',
          'ent_start_char',
          'ent_end_char',
          'modifier_text',
          'modifier_category',
          'modifier_direction',
          'modifier_start_char',
          'modifier_end_char',
          'modifier_scope_start_char',
          'modifier_scope_end_char'],
    "section": [
        'section_category',
      'section_title_text',
      'section_title_start_char',
      'section_title_end_char',
      'section_text',
      'section_text_start_char',
      'section_text_end_char',],
    "doc": ["text", "document_classification"]
}

TARGET_COLUMNS = {
    "doc": [
        ("document_id", "bigint"),
        ("text", "varchar(max)"),
        ("document_classification", "varchar(10)"),
        ("document_domain", "varchar(25)"),
    ],
    "ent": [
        ("document_id", "bigint"),
        ('text', "varchar(1000)"),
         ('start_char', "int"),
         ('end_char', "int"),
         ('label_', "varchar(1000)"),
         ('is_negated', "int"),
         ('is_uncertain', "int"),
         ('is_historical', "int"),
         ('is_hypothetical', "int"),
         ('is_family', "int"),
         ('section_category', "varchar(1000)"),
         ('snippet', "varchar(5000)")
    ],
     "context": [
        ('document_id', 'bigint'),
        ('ent_text', 'varchar(100)'),
          ('ent_label_', 'varchar(100)'),
          ('ent_start_char', 'int'),
          ('ent_end_char', 'int'),
          ('modifier_text', 'varchar(100)'),
          ('modifier_category', 'varchar(50)'),
          ('modifier_direction', 'varchar(25)'),
          ('modifier_start_char', 'int'),
          ('modifier_end_char', 'int'),
          ('modifier_scope_start_char', 'int'),
          ('modifier_scope_end_char', 'int')
     ],
    "section": [
        ('document_id', 'bigint'),
        ('section_category', 'varchar(100)'),
      ('section_title_text', 'varchar(100)'),
      ('section_title_start_char', 'int'),
      ('section_title_end_char', 'int'),
      ('section_text', 'varchar(max)'),
      ('section_text_start_char', 'int'),
      ('section_text_end_char', 'int'),
    ],
}


DOMAIN_TABLES = {
    "emergency": "[Pneumonia].[EDProviderDocumentSample]",
    "radiology": "[Pneumonia].[ChestXrayRadiologyReportTextSample]",
    "discharge": "[Pneumonia].[DischargeSummaryDocumentSample]"
}

ID_COLS = {
    "emergency": "TIUDocumentSID",
    "radiology": "RadiologyNuclearMedicineReportSID",
    "discharge": "TIUDocumentSID"
}

DEST_SCHEMA = "CSDE_BSV.Pneumonia"
HTML_DIR = "Z:\\CSDE_BSV\\Alec\\Pneumonia\\output\\htmls_0314"

def get_snippet(ent):
    sent_start = ent.sent.start
    if sent_start > 0:
        start = ent.doc[sent_start-1].sent.start
    else:
        start = sent_start
    sent_end = ent.sent.end
    if sent_end < len(ent.doc)-1:
        end = ent.doc[sent_end].sent.end
    else:
        end = sent_end
    snippet = ent.doc[start:end]
    if len(snippet.text_with_ws) >= 5000:
        return snippet[:10].text_with_ws
    else:
        return snippet.text_with_ws

try:
    Span.set_extension("snippet", getter=get_snippet)
except:
    pass

def process_domain_texts(domain, truncate, html=False, limit=1000):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        nlp = build_nlp(domain)

    doc_consumer = DocConsumer(nlp, dtypes="all", dtype_attrs=DTYPE_ATTRS)
    nlp.add_pipe(doc_consumer)

    df = get_domain_texts(domain, limit)
    print(f"Processing {len(df)} docs from domain {domain}")
    docs = list(nlp.pipe(df["ReportText"]))
    df["doc"] = docs

    write_docs(df, domain, truncate)
    if html:
        write_htmls(df, domain)

def get_domain_texts(domain, limit=None):
    if limit is None:
        limit = 1000
    table = DOMAIN_TABLES[domain]
    query = f"SELECT TOP {limit} * FROM {table}"
    conn = create_connection_sql13()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def write_docs(df, domain, truncate=False):
    conn = create_connection_sql13()
    nlp_conn = DbConnect(conn=conn)
    cursor = conn.cursor()
    id_col = ID_COLS[domain]
    for dtype, col_tups in TARGET_COLUMNS.items():
        cols, col_types = zip(*col_tups)
        dest_table = f"{DEST_SCHEMA}.NLP_{dtype.title()}"
        if truncate:
            print("Truncating", dest_table)
            cursor.execute(f"TRUNCATE TABLE {dest_table}")
        writer = DbWriter(nlp_conn, destination_table=dest_table, doc_dtype=dtype,
                          cols=cols, col_types=col_types,
                          create_table=False, drop_existing=False)

        for i, row in df.iterrows():
            doc = row["doc"]
            doc_data = doc._.get_data(dtype, as_rows=True)
            # Add TIUDocumentSID
            doc_data = [(row[id_col],) + row_data for row_data in doc_data]
            # Add document domain for the doc table
            if dtype == "doc":
                doc_data = [row_data+(domain,) for row_data in doc_data]
            try:
                if doc_data:
                    writer.write_data(doc_data)
            except pyodbc.DataError:
                print("Skipping row", i)
                conn = create_connection_sql13()
                nlp_conn = DbConnect(conn=conn)
                cursor = conn.cursor()
                writer.db = nlp_conn
    conn.close()

def write_htmls(df, domain):
    html_dir = os.path.join(HTML_DIR, domain)
    if not os.path.exists(html_dir):
        os.mkdir(html_dir)
    print(f"Saving {len(df)} htmls to", html_dir)

    from medspacy.visualization import visualize_ent
    for i, row in df.iterrows():
        doc = row["doc"]
        id_col = ID_COLS[domain]
        document_id = row[id_col]
        filepath = os.path.join(html_dir,
                                f"{doc._.document_classification}_{row[id_col]}.html")
        html = ""
        for field in [id_col]:
            html += f"<h1>{row[field]}</h1>"
        html += f"<h1>{doc._.document_classification}</h1>"
        html += visualize_ent(doc, jupyter=False)

        with open(filepath, "w") as f:
            f.write(html)

def main():
    truncate = args.truncate
    for domain in domains:
        process_domain_texts(domain, truncate, args.html, limit=args.num_docs)
        # Only truncate once
        truncate = False

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-d", "--domain", choices=DOMAINS + ("all",), default="all")
    parser.add_argument("-t", "--truncate", action="store_true")
    parser.add_argument("--html", action="store_true")
    parser.add_argument("-n", "--num-docs", type=int, default=1000)
    args = parser.parse_args()
    if args.domain == "all":
        domains = tuple(DOMAINS)
    else:
        domains = (args.domain,)
    main()
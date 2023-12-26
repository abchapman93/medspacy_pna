from src.util import build_nlp
import pandas as pd
from datetime import datetime

from argparse import ArgumentParser

from medspacy.io.db import DbConnect, DbWriter

SOURCE_TABLES = {
    "radiology": "NLP.Document_Queue_Radiology",
    "discharge": "NLP.Document_Queue_Discharge",
    "emergency": "NLP.Document_Queue_Emergency",
}
TARGET_TABLES = {
    "radiology": {
        "doc": "NLP.Doc_Radiology",
        "ent": "NLP.Ent_Radiology"
    },
    "discharge": {
        "doc": "NLP.Doc_Discharge",
        "ent": "NLP.Ent_Discharge"
    },
    "emergency": {
        "doc": "NLP.Doc_Emergency",
        "ent": "NLP.Ent_Emergency"
    }
}
ID_COLS = {
    "radiology": "",
    "discharge": "",
    "emergency": "",
}
TEXT_COLS = {
    "radiology": "Text",
    "discharge": "ReportText",
    "emergency": "ReportText"
}

SCHEMAS = {
    "radiology": ("linked",),
    "discharge": ("full", "diagnoses"),
    "emergency": ("full",)
}

MIN_DATE = "2021-01-01"
MAX_DATE = "2021-01-31"
LOG_TABLE = "NLP.Execute_Log"


def create_connection(autocommit=True):
    return


def init_log(conn, domain):
    cursor = conn.cursor()
    cursor.execute(f"""INSERT INTO {LOG_TABLE} (Domain, InsertDateTime) VALUES (?, GETDATE())""", (domain,))
    cursor.execute(f"SELECT MAX(Execute_Log_ID) FROM {LOG_TABLE}")
    execute_id = cursor.fetchone()[0]

    cursor.close()
    return execute_id


def log_batch(conn, execute_id, batch_size, start_time):
    time = (datetime.now() - start_time).seconds
    query = f"""UPDATE {LOG_TABLE} SET DocumentCount = (ISNULL(DocumentCount, 0) + ?), RunTime = ? WHERE Execute_Log_ID = ?"""
    cursor = conn.cursor()

    cursor.execute(query, (batch_size, time, execute_id))

    cursor.close()


def close_log(conn, execute_id, rslt=0, rslt_msg=None):
    query = f"""UPDATE {LOG_TABLE} SET Result = ?, ResultMsg = ? WHERE Execute_Log_ID = ?"""
    cursor = conn.cursor()

    cursor.execute(query, (rslt, rslt_msg, execute_id))

    cursor.close()


def get_source_data_documents(conn, domain, num_docs=500):
    if domain == "radiology":
        df = get_source_data_radiology(conn, num_docs)
    elif domain == "discharge":
        df = get_source_data_discharge(conn, domain, num_docs)
    else:
        df = get_source_data_emergency(conn, domain, num_docs)
    return df


def get_source_data_discharge(conn, domain, num_docs=500):
    df = None
    return df


def get_source_data_emergency(conn, domain, num_docs=500):
    df = None
    return df


def get_source_data_radiology(conn, num_docs=500):
    df = None
    return df


def wrangle_df(df, domain):
    if domain == "radiology":
        df = wrangle_df_radiology(df)
    elif domain == "emergency":
        df = wrangle_df_emergency(df)
    return df


def wrangle_df_radiology(df):
    """Cast date columns to datetime objects and concatenate texts"""
    group_by_cols = [ID_COLS["radiology"]]
    grouped = df.groupby(group_by_cols)
    grouped = grouped.agg({TEXT_COLS["radiology"]: "".join})
    return grouped.reset_index()


def wrangle_df_emergency(df):
    """Cast date columns to datetime objects and concatenate texts"""
    df[TEXT_COLS["emergency"]] = df.apply(
        lambda row: modify_emergency_text(row[TEXT_COLS["emergency"]], row["Addendum"]), axis=1)
    group_by_cols = ["Parent" + ID_COLS["emergency"]]
    grouped = df.groupby(group_by_cols)
    grouped = grouped.agg({TEXT_COLS["emergency"]: "".join})
    grouped = grouped.reset_index()
    return grouped.rename({"Parent" + ID_COLS["emergency"]: ID_COLS["emergency"]}, axis=1)


def modify_emergency_text(text, is_addendum):
    if is_addendum:
        return "ADDENDUM:\n\n" + text
    else:
        return text


def create_db_writers(conn, domain, doc_attrs, ent_attrs):
    nlp_conn = DbConnect(conn=conn)
    doc_writer = DbWriter(nlp_conn, TARGET_TABLES[domain]["doc"],
                          create_table=False, drop_existing=False,
                          write_batch_size=100, cols=doc_attrs,
                          col_types=["" for x in doc_attrs]  # Don't actually need this if we're not creating a table
                          )
    ent_writer = DbWriter(nlp_conn, TARGET_TABLES[domain]["ent"],
                          create_table=False, drop_existing=False,
                          write_batch_size=100, cols=ent_attrs,
                          col_types=["" for x in ent_attrs]  # Don't actually need this if we're not creating a table
                          )
    return doc_writer, ent_writer


def process_texts(df, nlp, domain, doc_writer, ent_writer, batch_size, conn, batch_id, start_time):
    num_batches = len(df) // batch_size + 1

    for batch_num in range(num_batches):
        start = batch_num * batch_size
        end = start + batch_size
        print(f"{start} / {len(df)}")
        try:
            sub_df = df.iloc[start:end].copy()
        except IndexError:
            break
        process_batch(sub_df, nlp, domain, doc_writer, ent_writer, conn, batch_id, start_time)


def process_batch(df, nlp, domain, doc_writer, ent_writer, conn, batch_id, start_time):
    docs = list(nlp.pipe(df[TEXT_COLS[domain]], disable=["document_classifier"]))
    clf = nlp.get_pipe("document_classifier")
    doc_data_rows = []
    ent_data_rows = []
    df["doc"] = docs
    for i, row in df.iterrows():
        doc = row["doc"]

        nlp.get_pipe("doc_consumer")(doc)
        # doc_data = row["doc"]._.get_data("doc", as_rows=True)
        ent_data = row["doc"]._.get_data("ent", as_rows=True)
        for schema in SCHEMAS[domain]:
            doc_data_rows.append((row[ID_COLS[domain]], clf.classify_document(doc, schema=schema), schema))
        ent_data_rows += [(row[ID_COLS[domain]],) + d for d in ent_data]
    # print(doc_data_rows)
    # print(ent_data_rows[:5])
    if len(doc_data_rows):
        doc_writer.db.write(doc_writer.insert_query, doc_data_rows)
    if len(ent_data_rows):
        ent_writer.db.write(ent_writer.insert_query, ent_data_rows)
    #     if len(doc_data):
    #         writer.db.write(writer.insert_query, doc_data)
    print(f"Wrote {len(df)} rows")
    log_batch(conn, batch_id, len(df), start_time)
    return True

def main():
    conn = create_connection()
    batch_id = init_log(conn, args.domain)

    df = get_source_data_documents(conn, args.domain, num_docs=args.num_docs)
    print(df)
    nlp = build_nlp(args.domain, doc_consumer=True)
    print(nlp.pipe_names)
    print(df.head())
    print(f"Processing {len(df)} documents")
    start_time = datetime.now()

    doc_attrs = [ID_COLS[args.domain], "document_classification", "classification_schema"]
    ent_attrs = [ID_COLS[args.domain]] + nlp.get_pipe("doc_consumer").dtype_attrs["ent"]
    doc_writer, ent_writer = create_db_writers(conn, args.domain, doc_attrs, ent_attrs)

    process_texts(df, nlp, args.domain, doc_writer, ent_writer, args.batch_size, conn, batch_id, start_time)
    # doc_writer.db.close()
    conn.close()
    runtime = (datetime.now() - start_time).seconds

    print(f"Procssed {len(df)} documents in {runtime} seconds")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-d", "--domain", choices=("emergency", "discharge", "radiology"))

    parser.add_argument("-n", "--num-docs", type=int, default=500)
    parser.add_argument("-b", "--batch-size", type=int, default=25)

    args = parser.parse_args()

    main()

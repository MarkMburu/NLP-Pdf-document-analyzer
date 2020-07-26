import streamlit as st
from analytics import get_words_in_sentances, get_headers, get_frequent_words, get_comparison_similar_words
from utils import read_pdf_file, get_sections
import base64
import pickle
import os
import json
import plotly.graph_objs as go
import pandas as pd

BACKUP_FILE = "db.json"
db = {}
if os.path.exists(BACKUP_FILE):
    db = json.load(open(BACKUP_FILE, 'r+'))

TOOL_OPTIONS=["Should, Shall, Must", "Headers", "Query", "Section Words"]
COMPARE_OPTIONS = ["Should, Shall, Must", "Query Comparison"]

DOWNLOAD_BUTTON_STYLE = """
    background-color:#37a879;
    border-radius:28px;
    border:1px solid #37a879;
    display:inline-block;
    cursor:pointer;
    color:#ffffff;
    font-family:Arial;
    font-size:12px;
    padding:8px 15px;
    text-decoration:none;
    text-shadow:0px 1px 0px #2f6627;
"""

def display_result(df, filename, header):
    """Display a dataframe along with the option to download the data.
    
    Arguments:
        df {pd.DataFrame} -- Dataframe to display
        filename {str} -- Name of file to downlaod
        header {str} -- Title of dataframe
    """
    st.header(header)
    st.table(df)
    st.markdown(download_button(df, filename), unsafe_allow_html=True)

def display_words(word_dict, fig=False, target=None):
    """Function used to display multiple sub-groups of words
    
    Arguments:
        word_dict {dict} -- Dictionary with the following format: {Word: DataFrame}
    """
    for word in word_dict:
        key = word
        word = word.replace('_2', '')
        if word=='must':
            st.header("Hard Requirements")
        elif word=='shall':
            st.header("Soft Requirements")

            
        word_btn = st.checkbox(word.title() + " - " + str(word_dict[word].shape[0]), key=key+"_button")
        if word_btn:
            if fig:
                plot_distributions(word_dict[key], target)
            display_result(word_dict[key], word.title() + '.csv', word.title())

def plot_distributions(df, target):
    if df.shape[0] > 0 and df.shape[1] > 0:
        df[target] = df[target].apply(lambda x: ' '.join(x.split()[:2]))
        new_df = df[target].value_counts() / df.shape[0]
        fig = go.Figure([go.Bar(x=new_df.index, y=new_df.values, text=(new_df*100).round(2).astype(str) + '%', textposition='auto')], layout=dict(width=1000, height=700, font=dict(size=15),  yaxis=dict(tickformat='%', title="Distribution"), title="Section Scores"), )
        fig.update_xaxes(automargin=True)
        st.write(fig)

def download_button(df, filename="download"):
    csv = df.to_csv()
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a name="download" href="data:file/csv;base64,{b64}" download="{filename}.csv">\
        <button style="{DOWNLOAD_BUTTON_STYLE}">Download Figure Data</button></a>'
    return href

def get_pages_ui(key=1):
    mode = st.selectbox("Selection Mode", ["New File", "Existing File"], key=f"selection_{key}")
    pages = None
    sections = None
    name=None
    if mode == "New File":
        name = st.text_input("Filename", key=f"name_{key}")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key=f"file_uploader_{key}")
        if uploaded_file is not None:
            pages = get_pages(uploaded_file)
            _, sections = get_sections(pages)
            
    else:
        file_name = st.selectbox("Previos File", sorted(list(db.keys())), key=f"file_name_{key}")
        if file_name:
            pages = db[file_name]
            _, sections = get_sections(pages)
            name = file_name

    return pages, sections, name

st.title("PDF Tool")
st.header("Singular File Exploration")

@st.cache
def get_pages(file):
    """Get list of all pages in a pdf file
    
    Arguments:
        file {file} -- Input PDF file
    
    Returns:
        list -- List of all pages in pdf
    """
    pdf = read_pdf_file(file)
    pages = [i for i in pdf]
    return pages

pages, sections_1, name = get_pages_ui()

if pages is not None and name:
    multi_select = st.selectbox("Choose Tool Output", options=TOOL_OPTIONS, key="first_file_mulit")
    if multi_select == TOOL_OPTIONS[0]:
        word_results = get_words_in_sentances(pages, ["must", "should", "shall"], sections_1)
        d = pd.Series({i:j.shape[0] for i,j in word_results.items()})
        st.write(d)
        st.write(go.Figure(
            data=[go.Pie(labels=d.index, values=d.values)]
            )
            )

        display_words(word_results, fig=True, target="Section")
    elif multi_select == TOOL_OPTIONS[1]:
        display_result(get_headers(pages), "headers", "Headers")
    elif multi_select == TOOL_OPTIONS[2]:
        st.header("Searching the PDF")
        query = st.text_input("Please enter a query to search", key="query_input")
        run_query = st.button("Run Query!", key="run_query")
        if query:
            results = get_words_in_sentances(pages, [query])
            display_words(results)
    elif multi_select == TOOL_OPTIONS[3]:
        word_results = get_frequent_words(pages)
        display_words(word_results)


    st.header("Comparing Different Files")    
    pages_2, sections_2, name_2 = get_pages_ui(key=2)

    if pages_2 is not None and name_2:
        multi_select_2 = st.selectbox("Choose Comparison Output", options=TOOL_OPTIONS, key="second_file_mulit")

        if multi_select_2 == COMPARE_OPTIONS[0]:
            display_words(get_comparison_similar_words(pages, pages_2, ["must", "should", "shall"],))
        elif multi_select_2 == COMPARE_OPTIONS[1]:
            query = st.text_input("Please enter a query to search", key="query_input")
            run_query = st.button("Run Query!", key="run_query")
            if query:
                results = get_words_in_sentances(pages, [query])
                results_2 = get_words_in_sentances(pages_2, [query])
                display_words(results)
    
    db[name] = pages
    json.dump(db, open(BACKUP_FILE, "w+"))


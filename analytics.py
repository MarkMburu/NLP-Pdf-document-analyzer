from utils import read_pdf_file, clean_pdf_page, get_sections, clean_text, get_similar_sentences
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import CountVectorizer
import re


@st.cache(allow_output_mutation=True)
def get_words_in_sentances(pages, words, sections = None):
    
    """Get all words in the words parameter
    
    Arguments:
        pages {list} -- list of pages
        words {list} -- list of words
    
    Returns:
        dict -- Dictionary containing the results of the query in the foramt {Word:DataFrame}
    """
    words = [w.strip().lower() for w in words]
    outputs = {}
    for word in words:
        all_matches = []

        for page_ind, page in enumerate(pages):
            clean_page = clean_pdf_page(page)
            for sentance in clean_page:
                if word in sentance.lower():
                    d = {"Sentance": sentance, "Page": page_ind + 1}

                    if sections is not None:
                        d['Section'] = sections[page_ind+1]
                    all_matches.append(d)

        outputs[word] = pd.DataFrame(all_matches)

    return outputs


@st.cache
def get_headers(pages):
    """Find Section headers and sub headers in a dataframe

    
    Arguments:
        pages {list} -- list of pages to extract headers from
    
    Returns:
        list -- list of all header titles
    """
    results = []
    page_nums = []
    page_num = 0
    for page in pages:
        clean_page = clean_pdf_page(page)
        for i in clean_page:
            if (
                i.startswith("Section") and "page" not in i
            ):  # If the sentence starts with Secion X.
                results.append(i)
                page_nums.append(page_num + 1)
            elif re.findall("^(\d+\.\d+\.*)(?![\d\.])", i) and not re.findall(
                "\.\.\.", i
            ):  # Else if the sentence begins with a section id (3.2.1, 1.1, etc)
                results.append(i)
                page_nums.append(page_num + 1)
        page_num += 1

    last_num = 1
    cleaned_results = []
    cleaned_page_nums = []
    for ind, val in enumerate(results):
        if str(val).lower() == "section.":
            continue

        if "section" in str(val).lower() or int(val.split(".")[0]) == last_num:
            cleaned_results.append(val)
            cleaned_page_nums.append(page_nums[ind])
        elif int(val.split(".")[0]) == last_num + 1:
            cleaned_results.append(val)
            cleaned_page_nums.append(page_nums[ind])
            last_num += 1

    df = pd.DataFrame(
        [cleaned_page_nums, cleaned_results], index=["Page Number", "Header"]
    ).T
    return df


@st.cache
def get_frequent_words(pages):
    """Find the most common words in a list of pages
    
    Arguments:
        pages {list} -- list of pages
    
    Returns:
        dict -- Dictionary containing the section namea and values inside
    """
    sections, _ = get_sections(pages)
    sections = {key: clean_text(" ".join(val)) for key, val in sections.items()}

    cv = CountVectorizer(min_df=1, max_df=0.8)
    cv.fit(sections.values())

    for key in sections:
        trans = cv.transform([sections[key]]).toarray()[0]
        s = pd.Series(trans, index=cv.get_feature_names()).sort_values(ascending=False)
        s = (
            s[s > 0][:10]
            .to_frame(name="Count")
            .reset_index()
            .rename(columns={"index": "Word"})
        )
        sections[key] = s

    return sections

def get_comparison_similar_words(pages_1, pages_2, words):
    """Finds similar sentences between two dataframes
    
    Arguments:
        pages_1 {list} -- list of first set of pages
        pages_2 {list} -- list of second set of pages
        words {list} -- list of words to be included in the search
    
    Returns:
        dict -- dictionary of results
    """
    
    pages_1_words = get_words_in_sentances(pages_1, words)
    pages_2_words = get_words_in_sentances(pages_2, words)


    

    results = {}
    for word in words:
        if pages_2_words[word].shape[0] == 0 or pages_1_words[word].shape[0]==0:
            results[word +"_2"]=pd.DataFrame()
        else:
            results[word +"_2"]=get_similar_sentences(pages_1_words[word], pages_2_words[word])

    return results
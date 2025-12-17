# frontend/app.py

import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"


def add_context_page():
    st.header("Add Context")

    with st.form("add_context_form"):
        title = st.text_input("Title", placeholder="e.g. Professional Bio, Resume, Portfolio Summary")
        category = st.text_input("Category", value="professional", help="e.g. professional, personal, skills")
        content = st.text_area("Content", height=200, placeholder="Paste your text here...")

        submitted = st.form_submit_button("Save Context")

        if submitted:
            if not title or not content:
                st.error("Title and content are required.")
                return

            payload = {
                "title": title,
                "category": category,
                "content": content,
            }

            try:
                resp = requests.post(f"{API_BASE}/contexts", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(f"Saved! ID: {data['id']}")
                else:
                    st.error(f"Error: {resp.status_code} - {resp.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")


def query_context_page():
    st.header("Query Context")

    query = st.text_input("What do you want to retrieve?",
                          placeholder="e.g. 'Summarize my professional experience'")
    category = st.text_input("Filter by category (optional)",
                             placeholder="e.g. professional")
    top_k = st.number_input("Top K results", min_value=1, max_value=20, value=5, step=1)

    if st.button("Search"):
        if not query:
            st.error("Query is required.")
            return

        payload = {
            "query": query,
            "category": category or None,
            "top_k": top_k,
        }

        try:
            resp = requests.post(f"{API_BASE}/query", json=payload)
            if resp.status_code == 200:
                data = resp.json()

                st.subheader("Context Bundle (copy this into any AI tool)")
                st.code(data["context_bundle"], language="markdown")

                st.subheader("Raw Results")
                for i, r in enumerate(data["results"], start=1):
                    st.markdown(f"**[{i}] {r['title']}** (category: `{r['category']}`, distance: {r['distance']:.4f})")
                    with st.expander("Show content"):
                        st.write(r["content"])
            else:
                st.error(f"Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")


def list_contexts_page():
    st.header("All Stored Contexts")

    try:
        resp = requests.get(f"{API_BASE}/contexts")
        if resp.status_code == 200:
            items = resp.json()
            if not items:
                st.info("No context stored yet.")
                return

            for i, item in enumerate(items, start=1):
                st.markdown(f"### [{i}] {item['title']} (category: `{item['category']}`)")
                st.write(item["content"])
                st.caption(f"ID: {item['id']}")
        else:
            st.error(f"Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        st.error(f"Request failed: {e}")


def main():
    st.set_page_config(page_title="Personal Context OS", layout="wide")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Add Context", "Query Context", "List Contexts"],
    )

    if page == "Add Context":
        add_context_page()
    elif page == "Query Context":
        query_context_page()
    elif page == "List Contexts":
        list_contexts_page()


if __name__ == "__main__":
    main()

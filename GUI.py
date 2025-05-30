import streamlit as st
import pandas as pd
from io import BytesIO
import os

st.set_page_config(layout="wide")
st.title("📋 Legal QA Annotation Tool")
if "user_id" in st.session_state:
    st.markdown(f"👤 **Current Annotator:** `{st.session_state.user_id}`")
def highlight_tags(text):
    tag_styles = {
        "Issue": "background-color: #ffcccc; font-weight: bold;",
        "Reason": "background-color: #ccffcc; font-weight: bold;",
        "Conclusion": "background-color: #ccccff; font-weight: bold;"
    }
    for tag, style in tag_styles.items():
        text = text.replace(f"<{tag}>", f'<span style="{style}">')
        text = text.replace(f"</{tag}>", "</span>")
    return text

def clean_summary_text(text):
    if pd.isna(text):
        return ""
    text = str(text).replace("\n", " ").replace("\r", " ")
    text = text.replace("$", r"\$")  # escape dollar signs
    return " ".join(text.split())

if "user_id" not in st.session_state:
    user_id = st.selectbox("Select your annotator ID:", ["", "ka", "matt"])
    if user_id != "":
        st.session_state.user_id = user_id
        st.success(f"Logged in as: {user_id}")
        st.rerun()
    else:
        st.warning("Please select your ID to start annotating.")
        st.stop()

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.session_state.df = df if "df" not in st.session_state else st.session_state.df
    if "annotations" not in st.session_state:
        st.session_state.annotations = {}

    visible_index = st.number_input("Example #", min_value=1, max_value=len(df), step=1)
    index = visible_index - 1  # Convert to zero-based index
    row = df.iloc[index]
    st.subheader("📄 Summary")
    summary = clean_summary_text(row["ann_summary"])
    # Legend
    st.markdown("### 🟦 Annotation Legend")
    st.markdown("""
    - <span style='background-color:#ffcccc; padding:2px 5px;'>Issue</span>: Key issue in the case  
    - <span style='background-color:#ccffcc; padding:2px 5px;'>Reason</span>: Supporting reasons or arguments  
    - <span style='background-color:#ccccff; padding:2px 5px;'>Conclusion</span>: Final decision or claim
    """, unsafe_allow_html=True)

    st.markdown(f"**Summary:**<br>{highlight_tags(summary)}", unsafe_allow_html=True)
    st.subheader("🧠 Question")
    st.write(row["question"])
    st.subheader("🎯 Answer")
    st.write(row["answer"])
    # st.subheader("💡 Reason for Asking")
    # st.write(row["reason"])

    with st.form("annotation_form"):
        existing_annotation = st.session_state.annotations.get(index, {})
        question_type = st.selectbox("Question Type", ["", "Issue", "Reason", "Conclusion", "Factual"], index=["", "Issue", "Reason", "Conclusion", "Factual"].index(existing_annotation.get("question_type", "")),)
        question_type_reason = st.text_area("Reason for Question Type",
            value=existing_annotation.get("question_type_reason", ""),
        )   

        persona = st.selectbox("Persona", ["", "Layperson", "Professional"],
        index=["", "Layperson", "Professional"].index(existing_annotation.get("persona", "")),
)
        persona_reason = st.text_area("Reason for Persona",
            value=existing_annotation.get("persona_reason", ""),
        )

        factual = st.selectbox("Answer Factual Accuracy", ["", "Correct", "Incorrect", "Unclear"],
        index=["", "Correct", "Incorrect", "Unclear"].index(existing_annotation.get("answer_factual_accuracy", "")),
        )

        grounding = st.selectbox("Answer Grounding", ["", "Correct", "Incorrect", "Unclear"],
        index=["", "Correct", "Incorrect", "Unclear"].index(existing_annotation.get("answer_grounding", "")),
        )
        responsiveness = st.selectbox("Answer Responsiveness", ["", "Correct", "Incorrect", "Unclear"], index=["", "Correct", "Incorrect", "Unclear"].index(existing_annotation.get("answer_responsiveness", "")))

        comment = st.text_area("Comments (Optional)",
            value=existing_annotation.get("comment", ""),
        )

        submitted = st.form_submit_button("✅ Save Annotation")
        st.caption("⚠️ Please click 'Save Annotation' after finishing each example!")
        if submitted:
            st.session_state.annotations[index] = {
                "question_type": question_type,
                "question_type_reason": question_type_reason,
                "persona": persona,
                "persona_reason": persona_reason,
                "answer_factual_accuracy": factual,
                "answer_grounding": grounding,
                "answer_responsiveness": responsiveness,
                "comment": comment,
            }
            st.success(f"Annotation for example #{visible_index} saved.")

    original_filename = uploaded_file.name
    base_name = os.path.splitext(original_filename)[0]         # qa_pairs_1996canlii6900_A_TODO
    base_name_clean = base_name.replace("_TODO", "")           # qa_pairs_1996canlii6900_A
    filename = f"{st.session_state.user_id}_{base_name_clean}.xlsx"

    if st.button("📥 Download All Annotations"):
        result = pd.DataFrame.from_dict(st.session_state.annotations, orient="index")
        result["index"] = result.index
        final = df.copy()
        for _, row in result.iterrows():
            i = row["index"]  # This is the row number in df
            for col in result.columns:
                if col != "index":
                    final.at[i, col] = row[col]
        output = BytesIO()
        final.to_excel(output, index=False, engine='openpyxl')
        st.download_button("Download Annotated Excel", output.getvalue(), file_name=filename)
import streamlit as st
import pandas as pd

# Load data with error handling
def load_data(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

@st.cache_data
def get_data(path: str) -> pd.DataFrame:
    return load_data(path)

def main():
    st.title("Coordinator App")

    # Sidebar: CSV path
    data_path = st.sidebar.text_input("Data CSV Path", "data/contacts.csv")
    df = get_data(data_path)

    # Early exit if no data
    if df.empty:
        st.warning("No data available. Check the path or file.")
        return

    # Ensure required columns
    required = {"name", "phone"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        return

    # Names list
    names = sorted(df["name"].unique())
    if not names:
        st.warning("No names found in data.")
        return

    selected_name = st.selectbox("Select a contact", names)

    # Display phone
    subset = df[df["name"] == selected_name]
    if subset.empty:
        st.error(f"No record found for '{selected_name}'")
        return

    # Show first matching record safely
    record = subset.iloc[0]  # safe because subset is not empty
    st.write(f"**Phone:** {record['phone']}")

    st.markdown("---")
    st.header("Details")
    for column, value in record.items():
        st.write(f"**{column}:** {value}")

    if st.button("Refresh Data"):
        st.experimental_rerun()

if __name__ == "__main__":
    main()

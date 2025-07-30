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
# Cached loader to avoid re-reading CSV on every rerun
def get_data(path: str) -> pd.DataFrame:
    return load_data(path)

# Main app function
def main():
    st.title("Coordinator App")

    # Sidebar: CSV path input
    data_path = st.sidebar.text_input(
        "Data CSV Path (must include 'group' & 'name' columns)",
        "data/contacts.csv"
    )
    df = get_data(data_path)

    # Exit early if data could not be loaded
    if df.empty:
        st.warning("No data available. Please check your CSV path and file contents.")
        return

    # Validate required columns
    expected_cols = {"group", "name"}
    missing = expected_cols - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return

    # Build and display group selector
    groups = sorted(df["group"].dropna().unique())
    if not groups:
        st.warning("No groups found in the data. Make sure 'group' column has values.")
        return

    selected_group = st.selectbox("Select a group to view contacts", groups)

    # Filter DataFrame by selected group and list names
    group_df = df[df["group"] == selected_group]
    if group_df.empty:
        st.warning(f"No contacts found in group: {selected_group}")
    else:
        st.subheader(f"Contacts in Group: {selected_group}")
        for idx, row in group_df.iterrows():
            name = row.get("name", "<Unnamed>")
            st.write(f"- {name}")

    # Optional: Reload data
    if st.button("Refresh Data"):
        st.experimental_rerun()

# Entry point
if __name__ == "__main__":
    main()

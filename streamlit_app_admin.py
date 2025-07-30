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

    # Sidebar: CSV path input
    data_path = st.sidebar.text_input("Data CSV Path", "data/contacts.csv")
    df = get_data(data_path)

    # Early exit if no data
    if df.empty:
        st.warning("No data available. Check the path or file.")
        return

    # Ensure 'group' and 'name' columns exist
    required = {"group", "name"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        return

    # Group selection
    groups = sorted(df["group"].dropna().unique())
    if not groups:
        st.warning("No groups found in data.")
        return

    selected_group = st.selectbox("Select a group", groups)

    # Filter by selected group and display names
    group_df = df[df["group"] == selected_group]
    if group_df.empty:
        st.warning(f"No contacts found in group '{selected_group}'")
    else:
        st.header(f"Contacts in Group: {selected_group}")
        # Display list of names under the selected group
        names = group_df["name"].dropna().tolist()
        st.write("\n".join(f"- {n}" for n in names))

    # Refresh button
    if st.button("Refresh Data"):
        st.experimental_rerun()

if __name__ == "__main__":
    main()

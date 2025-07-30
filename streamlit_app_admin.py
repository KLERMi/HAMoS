import streamlit as st
import pandas as pd

# Cache data loading for performance
def load_data(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

@st.cache_data
def cached_load(path: str) -> pd.DataFrame:
    return load_data(path)

def main():
    st.title("Coordinator App")

    # Sidebar input for data path
    data_path = st.sidebar.text_input("Data CSV path", "data/contacts.csv")
    df = cached_load(data_path)

    if df.empty:
        st.warning("No data available. Please check the CSV path or file contents.")
        return

    # Verify required columns
    required_cols = {"name", "phone"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return

    # Build mapping of name to phone (first occurrence)
    name_to_phone = df.groupby("name")["phone"].first().to_dict()
    names = sorted(name_to_phone.keys())

    if not names:
        st.warning("No contacts found in the data.")
        return

    selected_name = st.selectbox("Select a contact", names)

    # Safe phone lookup
    selected_phone = name_to_phone.get(selected_name)
    if selected_phone:
        st.write(f"**Phone:** {selected_phone}")
    else:
        st.error(f"No phone number found for '{selected_name}'")

    st.markdown("---")
    st.header("Contact Details")

    # Filter and display details
    filtered = df[df["name"] == selected_name]
    if filtered.empty:
        st.warning(f"No detailed record found for '{selected_name}'")
    else:
        # Show the first row of the filtered DataFrame
        record = filtered.iloc[0]
        for col, val in record.items():
            st.write(f"**{col.capitalize()}:** {val}")

    # Button to refresh (rerun) the app
    if st.button("Refresh Data"):
        st.experimental_rerun()

if __name__ == "__main__":
    main()

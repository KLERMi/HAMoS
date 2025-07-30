import streamlit as st
import pandas as pd

# Load your data into a DataFrame
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def main():
    st.title("Coordinator App")

    # Replace with your actual data path
    data_path = st.sidebar.text_input("Data CSV path", "data/contacts.csv")
    try:
        df = load_data(data_path)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    # Ensure required columns exist
    required_cols = {'name', 'phone'}
    if not required_cols.issubset(df.columns):
        st.error(f"Data is missing required columns: {required_cols - set(df.columns)}")
        return

    # Create mapping of names to phones (first occurrence)
    name_to_phone = df.groupby('name')['phone'].first().to_dict()

    # Select a name
    names = sorted(name_to_phone.keys())
    if not names:
        st.warning("No names available in the data.")
        return

    selected_name = st.selectbox("Select a contact", names)

    # Lookup phone safely
    selected_phone = name_to_phone.get(selected_name)
    if not selected_phone:
        st.error(f"No phone number found for '{selected_name}'")
    else:
        st.write(f"**Phone:** {selected_phone}")

    # Further filtering example
    st.markdown("---")
    st.header("Contact Details")

    filtered = df[df['name'] == selected_name]
    if filtered.empty:
        st.warning(f"No detailed record found for '{selected_name}'")
    else:
        # Display the first matching record or all
        st.write(filtered.iloc[0])  # or st.table(filtered)

    # Example of triggering rerun safely
    if st.button("Refresh Data"):
        st.experimental_rerun()

if __name__ == '__main__':
    main()

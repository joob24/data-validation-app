import streamlit as st
import pandas as pd
from io import BytesIO

# Fungsi validasi
def validate_data(df, column, validation_type):
    errors = []
    sample_errors = []
    total_validated = len(df[column])
    
    if validation_type == "Completeness validation":
        # Cek data kosong (null, NaN, atau string kosong)
        errors = df[df[column].isnull() | (df[column].astype(str).str.strip() == '')].index.tolist()
        sample_errors = df.loc[errors[:10], [column]] if errors else pd.DataFrame()
    
    elif validation_type == "Format validation String":
        # Cek apakah ada data yang bukan text (hanya angka atau format lain)
        invalid = []
        for idx, value in df[column].items():
            if pd.notna(value):
                # Cek jika value adalah angka murni atau bukan string
                if isinstance(value, (int, float)) or str(value).replace('.', '').replace('-', '').isdigit():
                    invalid.append(idx)
        errors = invalid
        sample_errors = df.loc[invalid[:10], [column]] if invalid else pd.DataFrame()
    
    elif validation_type == "Format validation Date":
        # Cek apakah ada data yang bukan format date
        invalid = []
        for idx, value in df[column].items():
            if pd.notna(value):
                try:
                    pd.to_datetime(value)
                except:
                    invalid.append(idx)
        errors = invalid
        sample_errors = df.loc[invalid[:10], [column]] if invalid else pd.DataFrame()
    
    elif validation_type == "Format validation Numerik":
        # Cek apakah ada data yang bukan numerik
        invalid = df[~pd.to_numeric(df[column], errors='coerce').notnull()].index.tolist()
        errors = invalid
        sample_errors = df.loc[invalid[:10], [column]] if invalid else pd.DataFrame()
    
    elif validation_type == "Uniqueness validation":
        # Cek data ganda/duplikat
        duplicates = df[df.duplicated(subset=[column], keep=False)].index.tolist()
        errors = duplicates
        sample_errors = df.loc[duplicates[:10], [column]] if duplicates else pd.DataFrame()
    
    return total_validated, len(errors), sample_errors

# Fungsi untuk mendapatkan semua data bermasalah
def get_problematic_data(df, column, validation_type):
    if validation_type == "Completeness validation":
        return df[df[column].isnull() | (df[column].astype(str).str.strip() == '')]
    
    elif validation_type == "Format validation String":
        invalid_indices = []
        for idx, value in df[column].items():
            if pd.notna(value):
                if isinstance(value, (int, float)) or str(value).replace('.', '').replace('-', '').isdigit():
                    invalid_indices.append(idx)
        return df.loc[invalid_indices] if invalid_indices else pd.DataFrame()
    
    elif validation_type == "Format validation Date":
        invalid_indices = []
        for idx, value in df[column].items():
            if pd.notna(value):
                try:
                    pd.to_datetime(value)
                except:
                    invalid_indices.append(idx)
        return df.loc[invalid_indices] if invalid_indices else pd.DataFrame()
    
    elif validation_type == "Format validation Numerik":
        invalid_indices = df[~pd.to_numeric(df[column], errors='coerce').notnull()].index.tolist()
        return df.loc[invalid_indices] if invalid_indices else pd.DataFrame()
    
    elif validation_type == "Uniqueness validation":
        return df[df.duplicated(subset=[column], keep=False)]
    
    return pd.DataFrame()

# Inisialisasi session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None
if 'cleaned_df' not in st.session_state:
    st.session_state.cleaned_df = None

# Halaman Pertama: Upload dan Judul
if st.session_state.page == 'home':
    st.title("Dataset Validation and Cleaning")
    st.title("by joe_wevil")
    st.write("Upload your files dataset  (CSV or XLSX) to begin.")
    
    uploaded_file = st.file_uploader("choose here", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state.df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                st.session_state.df = pd.read_excel(uploaded_file)
            st.success("file successfully uploaded!")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    if st.session_state.df is not None and st.button("Process"):
        st.session_state.page = 'preview'
        st.rerun()

# Halaman Kedua: Preview Data
elif st.session_state.page == 'preview':
    st.title("Preview Dataset")
    if st.session_state.df is not None:
        st.write("column list:")
        st.write(list(st.session_state.df.columns))
        
        st.write("Sample 5 Data from Dataset (Complete Table):")
        st.dataframe(st.session_state.df.head(5))  # Tampilkan tabel maksimal 5 baris
        
        st.write(f"Total collums: {len(st.session_state.df.columns)}")  # Tambahan keterangan jumlah kolom
        st.write(f"Total rows: {len(st.session_state.df)}")  # Tambahan keterangan jumlah baris
        
        selected_column = st.selectbox("Enter the column header name for validation.:", st.session_state.df.columns)
        validation_type = st.selectbox("Select validation type:", [
            "Completeness validation",
            "Format validation String",
            "Format validation Date",
            "Format validation Numerik",
            "Uniqueness validation"
        ])
        
        if st.button("Proccess"):
            total, error_count, sample_errors = validate_data(st.session_state.df, selected_column, validation_type)
            st.session_state.validation_result = {
                'column': selected_column,
                'type': validation_type,
                'total': total,
                'error_count': error_count,
                'sample_errors': sample_errors
            }
            st.session_state.page = 'results'
            st.rerun()
    else:
        st.error("No datasets available. Return to main page.")
        if st.button("Return"):
            st.session_state.page = 'home'
            st.rerun()

# Halaman Ketiga: Hasil Validasi
elif st.session_state.page == 'results':
    st.title("Validation Results")
    if st.session_state.validation_result:
        result = st.session_state.validation_result
        st.write(f"The number of validated data in the column '{result['column']}': {result['total']}")
        st.write(f"Validation results '{result['type']}': {result['error_count']} problematic dataset found.")
        
        if result['error_count'] > 0:
            # Ambil minimal 10 baris lengkap (semua kolom) dari data bermasalah
            sample_rows = st.session_state.df.loc[result['sample_errors'].index[:10]] if len(result['sample_errors']) > 0 else pd.DataFrame()
            if not sample_rows.empty:
                st.write("Minimum sample of 10 problematic data (complete table):")
                st.dataframe(sample_rows)
            else:
                st.write("No problematic data samples are available.")
            
            # Opsi Tindakan
            st.write("---")
            st.subheader("Action Options:")
            
            # Ambil semua data bermasalah
            problematic_data = get_problematic_data(st.session_state.df, result['column'], result['type'])
            
            # Opsi 1: Download semua data bermasalah
            if not problematic_data.empty:
                csv_problematic = problematic_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download All Problematic Data",
                    data=csv_problematic,
                    file_name=f"data_bermasalah_{result['column']}.csv",
                    mime="text/csv",
                    key="download_problematic"
                )
                
                # Opsi 2: Hapus data bermasalah
                st.write("")
                if st.button("🗑️ Delete All Problematic Data"):
                    # Hapus baris bermasalah dari dataframe
                    st.session_state.cleaned_df = st.session_state.df.drop(problematic_data.index).reset_index(drop=True)
                    st.session_state.page = 'cleaned'
                    st.rerun()
        else:
            st.success("There is no problematic data.")
        
        st.write("---")
        if st.button("Back to Preview"):
            st.session_state.page = 'preview'
            st.rerun()
    else:
        st.error("No validation results. Return to preview.")
        if st.button("back"):
            st.session_state.page = 'preview'
            st.rerun()

# Halaman Keempat: Data Setelah Cleaning
elif st.session_state.page == 'cleaned':
    st.title("Data After Cleaning")
    if st.session_state.cleaned_df is not None:
        st.success("✅ Data cleaning successful! Problematic data has been removed..")
        
        st.write(f"**Total rows before cleaning:** {len(st.session_state.df)}")
        st.write(f"**Total rows after cleaning:** {len(st.session_state.cleaned_df)}")
        st.write(f"**Total rows deleted:** {len(st.session_state.df) - len(st.session_state.cleaned_df)}")
        
        st.write("---")
        st.write("**Clean Data Preview (Maximum 10 Rows):**")
        st.dataframe(st.session_state.cleaned_df.head(10))
        
        # Download data bersih
        st.write("---")
        csv_cleaned = st.session_state.cleaned_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download All Clean Data",
            data=csv_cleaned,
            file_name="data_cleaned.csv",
            mime="text/csv",
            key="download_cleaned"
        )
        
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back to Preview"):
                st.session_state.page = 'preview'
                st.rerun()
        with col2:
            if st.button("Back to Home"):
                st.session_state.page = 'home'
                st.session_state.df = None
                st.session_state.cleaned_df = None
                st.session_state.validation_result = None
                st.rerun()
    else:
        st.error("No data cleaned. Return to preview.")
        if st.button("Back"):
            st.session_state.page = 'preview'
            st.rerun()


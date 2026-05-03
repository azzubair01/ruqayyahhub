import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title('Stock Discrepancy Checker')

col1, col2 = st.columns(2)

with col1:
    descrepancy_file = st.file_uploader(label='Upload Discrepancy file', key='file_uploader_descrepancy', type=['xlsx', 'xls'])
    if descrepancy_file is not None:
        df_descrepancy = pd.read_excel(descrepancy_file)
        
        # Generate a column to indicate if the Material has duplicated rows
        if 'Material' in df_descrepancy.columns:
            df_descrepancy['Is Duplicated Material'] = df_descrepancy.duplicated(subset=['Material'], keep=False)

        with st.expander('View Discrepancy Data', expanded=False):
            st.dataframe(df_descrepancy)

with col2:
    zlp_file = st.file_uploader(label='Upload ZP file', key='file_uploader_zlp', type=['xlsx', 'xls'])
    if zlp_file is not None:
        df_zlp = pd.read_excel(zlp_file)
        
        # Generate a column to indicate if SAPITM is not a subcharacter of IMDESC
        if 'SAPITM' in df_zlp.columns and 'IMDESC' in df_zlp.columns:
            df_zlp['Is Old Part Number'] = df_zlp.apply(
                lambda row: str(row['SAPITM']) not in str(row['@ITEM']),
                axis=1
            )

        with st.expander('View ZP Data', expanded=False):
            st.dataframe(df_zlp)

if descrepancy_file is not None and zlp_file is not None:
    # Include the new column in the merge if it exists
    cols_to_keep_desc = ['Material', 'Description', 'Total Qty P58', 'Total Qty 3PL']
    if 'Is Duplicated Material' in df_descrepancy.columns:
        cols_to_keep_desc.append('Is Duplicated Material')
        
    cols_to_keep_zlp = ['SAPITM', 'IMDESC', 'LBSOH']
    if 'Is Old Part Number' in df_zlp.columns:
        cols_to_keep_zlp.append('Is Old Part Number')
        
    combined_df = pd.merge(
        left=df_descrepancy[cols_to_keep_desc],
        right=df_zlp[cols_to_keep_zlp],
        left_on='Material',
        right_on='SAPITM',
        how='left'
    ).drop_duplicates(subset=['Material'])
    st.dataframe(combined_df.set_index('Material'), width='stretch')

else:
    st.warning('Please upload both files')

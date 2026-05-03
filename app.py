import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title('Stock Discrepancy Checker')

col1, col2 = st.columns(2)

with col1:
    warehouse_file = st.file_uploader(label='Upload Warehouse file', key='file_uploader_warehouse',
                                type=['xlsx', 'xls'], accept_multiple_files=False)
    if warehouse_file is not None:
        df_warehouse = pd.read_excel(warehouse_file)
        df_warehouse_filtered = df_warehouse[df_warehouse['Storage Location']==2010]
        cols_to_keep_warehouse = ['Material', 'Storage Location', 'Unrestricted']

        with st.expander('View Warehouse Data', expanded=False):
            st.dataframe(df_warehouse_filtered, hide_index=True)


with col2:
    zlp_file = st.file_uploader(label='Upload ZP file', key='file_uploader_zlp',
                                type=['xlsx', 'xls'], accept_multiple_files=False)
    if zlp_file is not None:
        df_zlp = pd.read_excel(zlp_file)
        cols_to_keep_zlp = ['@ITEM', 'SAPITM', 'IMDESC', 'LBSOH']

        
        # Generate a column to indicate if SAPITM is not a subcharacter of IMDESC
        if 'SAPITM' in df_zlp.columns and '@ITEM' in df_zlp.columns:
            df_zlp['Is Old Part Number'] = df_zlp.apply(
                lambda row: str(row['SAPITM']) not in str(row['@ITEM']),
                axis=1
            )
            if 'Is Old Part Number' in df_zlp.columns:
                cols_to_keep_zlp.append('Is Old Part Number')

        with st.expander('View ZP Data', expanded=False):
            st.dataframe(df_zlp, hide_index=True)


if warehouse_file is not None and zlp_file is not None:

    df_combined = pd.merge(left=df_warehouse_filtered[cols_to_keep_warehouse], right=df_zlp[cols_to_keep_zlp],
                           left_on='Material', right_on='SAPITM', how='left')
    df_combined = df_combined.drop_duplicates(subset=['Material'])
    df_combined[['Unrestricted', 'LBSOH']] = df_combined[['Unrestricted', 'LBSOH']].fillna(0)
    df_combined['Is Stock Discrepancy'] = df_combined.apply(lambda x: True if x['Unrestricted'] != x['LBSOH'] else False, axis=1)

    col1, col2 = st.columns(2)
    with col1:
        st.info(f'Parts having old part number: {df_combined["Is Old Part Number"].sum()}/{len(df_combined)}')
    with col2:
        st.info(f'Parts having stock discrepancy: {df_combined["Is Stock Discrepancy"].sum()}/{len(df_combined)}')

    st.dataframe(df_combined.set_index('Material'), width='stretch')

    st.divider()

    st.title('Validate Discrepancy File')
    col1, col2 = st.columns(2)

    with col1:
        col1_1, col1_2 = st.columns([2,1])
        with col1_1:
            descrepancy_file = st.file_uploader(label='Upload Discrepancy file', key='file_uploader_descrepancy',
                                            type=['xlsx', 'xls'], accept_multiple_files=False)
        if descrepancy_file is not None:
            df_descrepancy = pd.read_excel(descrepancy_file)
            with col1_2:
                location = st.multiselect('Select Location', df_descrepancy['Location'].unique(), default=2010)
            df_descrepancy = df_descrepancy[df_descrepancy['Location'].isin(location)]

            # Generate a column to indicate if the Material has duplicated rows
            if 'Material' in df_descrepancy.columns:
                df_descrepancy['Is Duplicated Material'] = df_descrepancy.duplicated(subset=['Material'], keep=False)

                # Include the new column in the merge if it exists
            cols_to_keep_desc = ['Material', 'Description', 'Total Qty P58', 'Total Qty 3PL']
            if 'Is Duplicated Material' in df_descrepancy.columns:
                cols_to_keep_desc.append('Is Duplicated Material')

            with st.expander('View Discrepancy Data', expanded=False):
                st.info(f'Unique Part Number: {len(df_descrepancy["Material"].unique().tolist())}')
                st.dataframe(df_descrepancy, hide_index=True)

    with col2:
        if warehouse_file and descrepancy_file:
            warehouse_material = set(df_combined['Material'])
            discrepancy_material = set(df_descrepancy['Material'])
            duplicated_material = set(df_descrepancy[df_descrepancy['Is Duplicated Material']==True]['Material'])

            unknown_material = discrepancy_material - warehouse_material
            st.info(f'Part Number missing in warehouse: {len(unknown_material)}')
            st.write(unknown_material)

            st.info(f'Part Number duplicated: {len(duplicated_material)}/{len(discrepancy_material)}')
            st.write(duplicated_material)

else:
    st.warning('Please upload both files')

st.divider()

st.title('Validate Storage Location Discrepancy')
col1, col2 = st.columns(2)
with col1:
    sales_report = st.file_uploader(label='Upload Sales Report', key='file_uploader_sales_report',
                                    type=['xlsx', 'xls'], accept_multiple_files=False)
    if sales_report is not None:
        df_sales_report = pd.read_excel(sales_report)

        with st.expander('View Sales Report Data', expanded=False):
            st.dataframe(df_sales_report, hide_index=True)
            df_sales_report = df_sales_report.groupby(['Vendor Material Code', 'SO#/RCN#'])['Qty'].sum().reset_index()

        df_warehouse['Storage Location'] = df_warehouse['Storage Location'].fillna(0).astype(int).astype(str)
        df_sales_report['SO#/RCN#'] = df_sales_report['SO#/RCN#'].astype(str)
        df_sales_combined = pd.merge(left=df_warehouse[['Material', 'Storage Location', 'Unrestricted']],
                                     right=df_sales_report[['Vendor Material Code', 'SO#/RCN#', 'Qty']],
                                     left_on=['Material', 'Storage Location'], right_on=['Vendor Material Code', 'SO#/RCN#'],
                                     how='inner')
        df_sales_combined['Storage Location Discrepancy'] = df_sales_combined.apply(lambda x: True if x['Unrestricted'] != x['Qty'] else False, axis=1)
        with col2:
            st.info(f'Storage Location Discrepancy: {df_sales_combined["Storage Location Discrepancy"].sum()}/{len(df_sales_combined)}')
            st.dataframe(df_sales_combined, hide_index=True)


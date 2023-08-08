import streamlit as st
import pandas as pd
import os

def list_csv_files_in_current_directory():
    current_directory = os.getcwd()
    csv_files = [file for file in os.listdir(current_directory) if file.endswith('.csv')]
    return csv_files

def main():
    st.title("CSV Column Modifier")


    csv_files = list_csv_files_in_current_directory()

    if not csv_files:
        st.warning("No CSV files found in the current directory.")
        return

    uploaded_file = st.selectbox("Select a CSV file:", csv_files)
    # 使用pandas读取CSV文件
    df = pd.read_csv(uploaded_file)

    # 显示原始CSV数据
    st.header("Original CSV Data")
    st.dataframe(df)
    # 选择要修改的列名
    selected_column = st.selectbox("Select a column to modify:", df.columns)

    # 获取要修改的列数据
    column_data = df[selected_column]
    # 修改列数据
    new_values = st.text_area("Enter new values for the column (separated by comma):","{column_data}")
    new_values_list = new_values.split(',')
    column_data = pd.Series(new_values_list)

    with st.form("modify"):
        if st.form_submit_button("Sumbit"):
            df[selected_column] = column_data

            # 显示修改后的CSV数据
            st.header("Modified CSV Data")
            st.dataframe(df)

            # 保存修改后的数据到原始CSV文件（覆盖原来的文件）
            df.to_csv(uploaded_file, index=False)
            st.success("File updated successfully!")

if __name__ == "__main__":
    main()


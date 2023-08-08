import streamlit as st
import os

def main():
    # 创建文件上传器
    with st.form("Create DataItem"):
        uploaded_file = st.file_uploader("Upload a file", type=["csv", "txt"])

        submit = st.form_submit_button("Upload")
        if uploaded_file is not None and submit: 
            # 获取上传的文件名
            filename = uploaded_file.name

            # 获取当前脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # 拼接保存文件的路径
            save_path = os.path.join(script_dir, filename)

            # 保存文件
            with open(save_path, "wb") as f:
                f.write(uploaded_file.read())

            # 显示成功上传的消息
            st.success(f"File '{filename}' has been uploaded and saved successfully.")

        csv_files = list_csv_files_in_current_directory()

        if not csv_files:
            st.warning("No CSV files found in the current directory.")
            return

        selected_file = st.selectbox("Select a CSV file:", csv_files)
        dsName = st.text_input("dsname","")

        if st.form_submit_button("Select File"):
            st.write(f"Selected CSV file: {selected_file}")
            st.write(f"Selected Ds name: {dsName}")

def list_csv_files_in_current_directory():
    current_directory = os.getcwd()
    csv_files = [file for file in os.listdir(current_directory) if file.endswith('.csv')]
    return csv_files


if __name__ == "__main__":
    main()


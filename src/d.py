import streamlit as st

def main():
    # 在主页面的左上角添加一个侧边栏
    st.sidebar.title("Sidebar 1")
    st.sidebar.write("This is the content of Sidebar 1.")

    # 在主页面的右上角添加另一个侧边栏
    st.write("Main Page")
    st.sidebar.title("Sidebar 2")
    st.sidebar.write("This is the content of Sidebar 2.")

if __name__ == "__main__":
    main()


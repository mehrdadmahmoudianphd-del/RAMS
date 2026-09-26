@echo off
cd /d "D:\Papers\Conf\Logestic\rams_app"
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
pause
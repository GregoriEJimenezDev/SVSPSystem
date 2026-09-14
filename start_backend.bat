@echo off
cd C:\Users\user\OneDrive\Desktop\SVSP2\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
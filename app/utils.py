import PyPDF2
import docx2txt
from fastapi import UploadFile
import io

async def extract_text_from_file(file: UploadFile):
    content = await file.read()
    file_extension = file.filename.split(".")[-1].lower()
    
    text = ""
    if file_extension == "pdf":
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        for page in pdf_reader.pages:
            text += page.extract_text()
    elif file_extension in ["docx", "doc"]:
        text = docx2txt.process(io.BytesIO(content))
    else:
        # 텍스트 파일 등으로 가정
        text = content.decode("utf-8")
        
    return text

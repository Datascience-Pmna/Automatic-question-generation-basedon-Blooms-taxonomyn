import streamlit as st
from QGBlooms import generate_questions
from reportlab.pdfgen import canvas
import io
import pandas as pd
import textwrap

class SessionState(object):
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

st.set_page_config(page_title="BoomyQ", page_icon=":books:",layout="wide")

st.markdown(f"<h1 style='text-align: center;'>BloomyQ</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center;'>An automatic question generator based on Bloom's taxonomy</h3>", unsafe_allow_html=True)
st.write('\n')
st.write('\n')
st.write('\n')
st.write('\n')
def print_levels_to_page(qst,level):
    st.write(" ")
    #st.write(f"==================={level}=================")
    st.markdown(f"<h3>{level}</h3>", unsafe_allow_html=True)
    for i in qst:
        st.write(f"{'➤ '} {i}")

def print_levels_to_pdf(qst,level,y_pos,pdf):
    if y_pos <= 40:
        pdf.showPage()
        y_pos = 750 
    
    pdf.setFont('Helvetica-Bold', 16) 
    # pdf.drawString(100, y_pos,'\n') 
    # y_pos -= 20   
    pdf.drawString(100, y_pos, level)
    y_pos -= 20

    pdf.setFont('Helvetica', 12)
    for i in qst:
        sentences = i.split(". ")
        for sentence in sentences:
            wrapped_lines = textwrap.wrap(sentence, width=80)
            if len(wrapped_lines) > 0:
                pdf.drawString(100, y_pos, "- " + wrapped_lines[0])
                y_pos -= 20
                if y_pos <= 40:
                    pdf.showPage()
                    y_pos = 750
            for line in wrapped_lines[1:]:
                pdf.drawString(120, y_pos, line)
                y_pos -= 20

                if y_pos <= 40:
                    pdf.showPage()
                    y_pos = 750  
    pdf.drawString(100, y_pos,' ')  
    y_pos -= 20  
    return y_pos         

col1, col2 = st.columns(2)
with col1:
    
    # Browse button for inputting text
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        text = uploaded_file.read()
        text = text.decode('utf-8')  # convert bytes to string
    else:
        text = st.text_area("Enter some text")

    L,R = st.columns(2)
    with R:
        if st.button("Reset"):
            st.experimental_rerun()
    with L:
        # Button for generating questions
        if st.button("Generate Questions"):
            questions = generate_questions(text)
            l1,l2,l3,l4,l5,l6,oth = questions
            if questions is not None:
                #st.write("Generated Questions:")
        
                # Create a buffer for the PDF
                pdf_buffer = io.BytesIO()

                # Create a new PDF object
                pdf = canvas.Canvas(pdf_buffer)

                # Write some text to the PDF
                pdf.setFont('Helvetica-Bold', 24)
                pdf.drawString(100, 750, "Generated Questions:")

                # Write each question to the PDF
                y_pos = 700
                y_pos = print_levels_to_pdf(l1,'Knowledge Level',y_pos, pdf)
                y_pos = print_levels_to_pdf(l2,'Understand Level',y_pos, pdf)
                y_pos = print_levels_to_pdf(l3,'Apply Level',y_pos, pdf)
                y_pos = print_levels_to_pdf(l4,'Analyze Level',y_pos, pdf)
                y_pos = print_levels_to_pdf(l5,'Evaluate Level',y_pos, pdf)
                y_pos = print_levels_to_pdf(l6,'Create Level',y_pos, pdf)
                y_pos = print_levels_to_pdf(oth,'Yes/No Questions',y_pos, pdf)
                pdf.save()
                pdf_bytes = pdf_buffer.getvalue()
        
                with col2:
                        st.text("")
                        st.text("")

                        st.write(f"<h2 style='text-align: center;'>Here the Questions !!!!!</h2>", unsafe_allow_html=True)

                        left,right = st.columns([3,1])
                        with right:
                            st.download_button(label="Download as PDF", data=pdf_bytes, file_name="questions.pdf")
                        with left:
                            # Display the generated questions on the left column
                            print_levels_to_page(l1,'Knowledge Level')
                            print_levels_to_page(l2,'Understand Level')
                            print_levels_to_page(l3,'Apply Level')
                            print_levels_to_page(l4,'Analyze Level')
                            print_levels_to_page(l5,'Evaluate Level')
                            print_levels_to_page(l6,'Create Level')
                            print_levels_to_page(oth,'Yes/No Questions')



from flask import Flask, render_template, request, redirect, url_for, jsonify
import logging
import os, pytesseract, requests, base64
from flask import current_app as app
from pdf2image import convert_from_path
import openai

# Library Paths
# Download pytesseract and poppler
pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
path = '/usr/local/Cellar/poppler/23.06.0/bin'
#poppler_path = '/usr/local/bin'

app = Flask(__name__)

# Variable Set-up
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_PATH = 'Documents'
app.config['UPLOAD_PATH'] = UPLOAD_PATH

# ----------------- FUNCTIONS -----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#   Converts PDF into Image
def pdf_to_img(filename):
    images = convert_from_path('Documents/' + filename)
    for img in images:
        img.save('Documents/CV_Image.png', 'PNG')

#   Calls Image to Text and returns text
def process_ocr():
    directory  =  f'Documents/'
    os.makedirs(directory, exist_ok=True)

    file_path = os.path.join(directory, 'CV_Image.png')
    text = img_to_text(file_path)
    return text

#   Image to Text
def img_to_text(file_path):
    return pytesseract.image_to_string(file_path)

#   Text transfer to file
def text_to_file(text):
    directory  =  f'Documents/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, 'CVOCR.txt')
    with open(file_path, 'w') as file:
        file.write(text)

#   Send ChatGPT prompt with text context
def getChatGPTJSON():
    logging.warning("ENTERED FUNCTION!!!!!!!!!!!!!!")

    openai.api_key = "ponerAPIKEY"
    
    directory = f'Documents/'
    file_path = os.path.join(directory, 'CVOCR.txt')
    with open(file_path, 'r') as file:
        file_contents = file.read()
    
    myPrompt = 'Create a JSON that fills ONLY the following fields ( About Description called aboutDescription, Full Name called fullName, Job Title called title, Country called country, State called state, City called city, Phone Number called phoneNumber, School Name called schoolName, Degree called degree, Specialization 1 called specialization1, Specialization2 called specialization2, Past Work Title called pastWTitle, Past Work Start Date called pastWStart, Past Work End Date called pastWEnd, Past Work Description called pastWDescription), using only the information provided from a Curriculum Vitae: " ' + file_contents + ' ” . Do NOT send any comments or explanations, only code.'

    completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": myPrompt}
        ]
    )

    print(completion.choices[0].message.content)

    file_path = os.path.join(directory, 'CVGPT.txt')
    with open(file_path, 'w' ) as file:
        file.write(completion.choices[0].message.content)
    logging.warning("EXITING FUNCTION!!!!!!!!!!!!!!!!")
    return completion.choices[0].message.content



# ----------------- APP ROUTES -----------------
@app.route("/generate-json", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return upload_file()
    return render_template("index.html")


def upload_file():
    logging.warning('Entered function!')
    if request.method == 'POST':

        # Checks if the request method was POST, 
        logging.warning('Entered POST method!')
        file = request.files['file']

        if file.filename == '':
            return render_template("fail.html", message="No file selected")
        

        if file and allowed_file(file.filename):
            file.save(os.path.join(app.config['UPLOAD_PATH'], file.filename))
            # Saves PDF into Image file
            pdf_to_img(file.filename)
            # Saves PDF text into Variable
            text = process_ocr()
            # Save Text into TXT file
            text_to_file(text)

            response = getChatGPTJSON()

            return response
    return logging.warning('No jala!')

@app.route("/uploaded/<filename>")
def file_uploaded(filename):
    return render_template("done.html", name=filename)

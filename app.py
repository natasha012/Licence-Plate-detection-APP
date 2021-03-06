# app.py
from model import model 
from flask import Flask, flash, request, redirect, url_for, render_template, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
import cv2
from flask import json
from matplotlib import pyplot as plt
import numpy as np
import imutils
import easyocr
import json   

def model(filename):
    img = cv2.imread(filename)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #Noise reduction
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17) 
    #Edge detection
    edged = cv2.Canny(bfilter, 30, 200) 

    #returning list of contours
    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
    #returning contours
    contours = imutils.grab_contours(keypoints)           
    #returning 10 sorted contours on the basis of descending contour area
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10] 

    #finding the location of number plate 
    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break

    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [location], 0,255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)

    (x,y) = np.where(mask==255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2+1, y1:y2+1]

    #cv2.imwrite("plate_img.jpg", cropped_image)

    f = open('static/owner.json',)
    data = json.load(f)
    reader = easyocr.Reader(['en'])
    result = reader.readtext(cropped_image)
    result = data[result[0][-2]]
    f.close()
    return result


UPLOAD_FOLDER = 'static/uploads/'

app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #print('upload_image filename: ' + filename)
        flash('Image successfully uploaded and owner details are displayed below')
        location = 'static/uploads/'+filename
        data=model(location)
        return render_template('index.html', result = data ,filename= filename)

    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

if __name__ == "__main__":
    app.run(debug=True, port = 1234)
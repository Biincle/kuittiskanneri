import os
import pprint
import subprocess
from flask import Flask, request, redirect, url_for
from flask import send_from_directory
from werkzeug.utils import secure_filename

import autocorrect
import receiptparser

# Store pics temporarily on api server
OCR_SCRIPT = './ocr.sh'
UPLOAD_FOLDER = 'uploads/'
STATIC_FOLDER = '../web-client/'
ALLOWED_EXTENSIONS = set(['png','jpg','jpeg','gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
autocorrect.init('wordlist.txt')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET','POST'])
def upload_file():
    if request.method == 'POST':
        image_file = request.files['file']
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            print("Save filename " + filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.mkdir(app.config['UPLOAD_FOLDER'])
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    # GET
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
    <p><input type=file name=file>
    <input type=submit value=Upload>
    </form>
    '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                                filename)

@app.route('/ocr/<filename>')
def ocr_testing(filename):
    if allowed_file(filename):
        imagepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(imagepath):
            image_text = ""
            proc = subprocess.Popen([OCR_SCRIPT, imagepath],
                                    stdout=subprocess.PIPE)
            for line in iter(proc.stdout.readline, ''):
                image_text += line.rstrip() + '\n'

            image_text = image_text.decode('utf-8')

            corrected_text = autocorrect.correct_text_block(image_text)

            if corrected_text is unicode:
                corrected_text = corrected_text.encode('utf-8')

            parse_result = receiptparser.parse_receipt(corrected_text)

            return '''
            <!doctype html>
            <pre>%s</pre>
            <hr>
            <pre>%s</pre>
            ''' % (corrected_text, pprint.pformat(parse_result))

    return '''
    <!doctype html>
    <p>Error occurred or image not found.</p>
    '''


@app.route('/static/<path:filename>')
def web_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)


@app.route('/')
def web_app():
    print("static app")
    return send_from_directory(STATIC_FOLDER, 'index.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8002, debug=True)


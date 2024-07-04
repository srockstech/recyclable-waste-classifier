from flask import Flask, request, render_template, redirect, jsonify
from flask_jsglue import JSGlue
import util
import os
from werkzeug.utils import secure_filename
import boto3

application = Flask(__name__)

def download_from_s3(bucket_name, key, download_path):
    s3 = boto3.client('s3', region_name=os.environ['REGION'], aws_access_key_id=os.environ['ACCESS_KEY_ID'], aws_secret_access_key=os.environ['SECRET_ACCESS_KEY'])
    s3.download_file(bucket_name, key, download_path)

# Retrieve environment variables
bucket_name = os.environ['S3_BUCKET_NAME']
cert_key = os.environ['CERT_KEY']
key_key = os.environ['KEY_KEY']

# Define paths for the download certificate and key
cert_path = '/temp/cert.pem'
key_path = '/temp/key.pem'

# Download the certificate and key from S3
download_from_s3(bucket_name, cert_key, cert_path)
download_from_s3(bucket_name, key_key, key_path)

# JSGlue is use for url_for() working inside javascript which is help us to navigate the url
jsglue = JSGlue() # create a object of JsGlue
jsglue.init_app(application) # and assign the app as a init app to the instance of JsGlue

util.load_artifacts()
#home page
@application.route("/")
def home():
    return render_template("home.html")

#classify waste
@application.route("/classifywaste", methods = ["POST"])
def classifywaste():
    image_data = request.files["file"]
    #save the image to upload
    basepath = os.path.dirname(__file__)
    image_path = os.path.join(basepath, "uploads", secure_filename(image_data.filename))
    image_data.save(image_path)

    predicted_value, details, video1, video2 = util.classify_waste(image_path)
    os.remove(image_path)
    return jsonify(predicted_value=predicted_value, details=details, video1=video1, video2=video2)

@application.before_request
def before_request():
    if not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# here is route of 404 means page not found error
@application.errorhandler(404)
def page_not_found(e):
    # here i created my own 404 page which will be redirect when 404 error occured in this web app
    return render_template("404.html"), 404

if __name__ == "__main__":

    context = (
        cert_path,
        key_path
    )
    # For Production:
    from waitress import serve
    application.run(host="0.0.0.0", port=443, ssl_context=context)

    # For Development:
    # application.run(debug=True)
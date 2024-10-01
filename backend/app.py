# app.py
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from openai import AzureOpenAI
import pdfplumber
import os
import azure.cognitiveservices.speech as speechsdk
from datetime import datetime, timedelta
from docx import Document
from flask_cors import CORS
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app)  # Enable CORS

# Replace with your Azure Storage connection string
CONNECTION_STRING = ""
INPUT_CONTAINER = "inputdocuments"
OUTPUT_CONTAINER = "outputaudio"

ACCOUNT_KEY = ""

# Replace with your Azure Speech Service credentials
SPEECH_KEY = ""
SPEECH_REGION = "eastus"

endpoint = ""
deployment = "gpt-35-turbo"
subscription_key = ""

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    blob_client = blob_service_client.get_blob_client(container=INPUT_CONTAINER, blob=file.filename)

    # Upload file to input container
    blob_client.upload_blob(file, overwrite=True)

    # Extract text based on file type
    if file.filename.endswith('.pdf'):
        text = extract_text_from_pdf(file)
    elif file.filename.endswith('.docx'):
        text = extract_text_from_docx(file)
    else:
        return jsonify({"error": "Unsupported file type. Only PDF and DOCX are allowed."}), 400

    # Convert text to audio and upload to output container
    audio_url = convert_text_to_audio_and_upload(text, file.filename)

    # Generate summary
    summary = summarize_text(text)

    # Convert summary to audio and upload
    summary_audio_url = convert_text_to_audio_and_upload(summary, f"summary_{file.filename}")

    return jsonify({
        'audioUrl': audio_url,
        'summaryAudioUrl': summary_audio_url
    })

def summarize_text(text):
    client = AzureOpenAI(
    azure_endpoint = endpoint,
    api_key = subscription_key,
    api_version = "2024-05-01-preview",
    )
    response = client.chat.completions.create(
        model=deployment,  # Replace with your model name (e.g., "gpt-35-turbo")
        messages=[
            {"role": "user", "content": f"Please summarize the following text: {text}"}
        ],
        max_tokens=300,  # Adjust based on desired summary length
        temperature=0.7,
    )
    
    return response.choices[0].message.content

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file):
    text = ""
    doc = Document(file)
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def convert_text_to_audio_and_upload(text, original_filename):
    audio_filename = original_filename.rsplit('.', 1)[0] + '_audio.mp3'

    # Set up the Azure Speech Service
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_filename)

    # Create a synthesizer to convert text to speech
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Perform text-to-speech
    synthesizer.speak_text(text)

    # Upload to the output container
    output_blob_client = blob_service_client.get_blob_client(container=OUTPUT_CONTAINER, blob=audio_filename)
    with open(audio_filename, "rb") as audio_file:
        output_blob_client.upload_blob(audio_file, overwrite=True)

    # Generate SAS token for the audio file
    sas_token = generate_sas_token(audio_filename)
    audio_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{OUTPUT_CONTAINER}/{audio_filename}?{sas_token}"

    return audio_url

def generate_sas_token(blob_name):
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=OUTPUT_CONTAINER,
        blob_name=blob_name,
        account_key=ACCOUNT_KEY,  # Add the account key here
        permission=BlobSasPermissions(read=True),
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)  # SAS token valid for 1 hour
    )
    return sas_token

if __name__ == '__main__':
    app.run(port=5000)
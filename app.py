from flask import Flask, render_template, request, Response, send_file
from pytube import YouTube
from urllib.parse import quote
import os
import subprocess
import requests

current_directory = os.path.dirname(os.path.realpath(__file__ if '__file__' in locals() else sys.executable))
ffmpeg_path = os.path.join(current_directory, 'ffmpeg.exe')

app = Flask(__name__)

yt = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    global yt
    video_url = request.form['video_url']
    yt = YouTube(video_url)
    video_streams = yt.streams.filter(only_video=True)
    audio_streams = yt.streams.filter(only_audio=True)
    combined_streams = yt.streams.filter(progressive=True)    
    
    return render_template('results.html', video_streams=video_streams, audio_streams=audio_streams, combined_streams=combined_streams)

@app.route('/process_and_download', methods=['POST'])
def process_and_download():
    global yt
    selected_video_stream_itag = request.form['selected_video_stream']
    selected_audio_stream_itag = request.form['selected_audio_stream']
    video_stream = yt.streams.get_by_itag(selected_video_stream_itag)
    audio_stream = yt.streams.get_by_itag(selected_audio_stream_itag)

    video_download_directory = os.path.join(current_directory, 'video')
    audio_download_directory = os.path.join(current_directory, 'audio')
    video_file_path = video_stream.download(output_path=video_download_directory)
    audio_file_path = audio_stream.download(output_path=audio_download_directory)

    combined_directory = os.path.join(current_directory, 'combined')
    os.makedirs(combined_directory, exist_ok=True)
    file_name = quote(yt.title)
    combined_file_path = os.path.join(combined_directory, f'{file_name}.mp4')
    cmd = [
        ffmpeg_path,
        '-i', video_file_path,
        '-i', audio_file_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        combined_file_path
    ]
    subprocess.run(cmd)

    return send_combined_file(combined_file_path)

@app.route('/download_combined', methods=['POST'])
def download_combined():
    global yt
    selected_combined_stream_itag = request.form['selected_combined_stream']
    combined_stream = yt.streams.get_by_itag(selected_combined_stream_itag)
    return send_combined_file_from_url(combined_stream.url)

@app.route('/download_pre_combined', methods=['POST'])
def download_pre_combined():
    global yt
    selected_pre_combined_stream_itag = request.form['selected_pre_combined_stream']
    pre_combined_stream = yt.streams.get_by_itag(selected_pre_combined_stream_itag)
    return send_pre_combined_file_from_url(pre_combined_stream.url)

def send_combined_file(file_path):
    return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

def send_combined_file_from_url(url):
    response = requests.get(url, stream=True)
    content_type = response.headers.get('Content-Type', 'application/octet-stream')
    file_name = response.headers.get('Content-Disposition', 'combined_stream.mp4').split('filename=')[-1]
    
    return Response(response.iter_content(chunk_size=1024), content_type=content_type, headers={'Content-Disposition': f'attachment; filename="{file_name}"'})

def send_pre_combined_file_from_url(url):
    response = requests.get(url, stream=True)
    content_type = response.headers.get('Content-Type', 'application/octet-stream')
    file_name = response.headers.get('Content-Disposition', 'pre_combined_stream.mp4').split('filename=')[-1]
    
    return Response(response.iter_content(chunk_size=1024), content_type=content_type, headers={'Content-Disposition': f'attachment; filename="{file_name}"'})

if __name__ == '__main__':
    app.run(debug=True)

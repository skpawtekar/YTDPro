from flask import Flask, render_template, request, Response
from pytube import YouTube
import requests
from urllib.parse import quote

app = Flask(__name__)

# Function to calculate the chunk size based on file size
def calculate_chunk_size(file_size):
    if file_size < 10 * 1024 * 1024:  # If the file is smaller than 10MB
        return 256 * 1024  # Use a chunk size of 256KB
    elif file_size < 100 * 1024 * 1024:  # If the file is smaller than 100MB
        return 1 * 1024 * 1024  # Use a chunk size of 1MB
    else:
        return 4 * 1024 * 1024  # For larger files, use a 4MB chunk size

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/display_streams', methods=['POST'])
def display_streams():
    try:
        video_url = request.form['video_url']
        yt = YouTube(video_url)
        available_streams = list(yt.streams)

        # Extract information from each stream object
        stream_info = []
        for idx, stream in enumerate(available_streams):
            quality = stream.resolution
            file_format = stream.mime_type.split('/')[1]
            file_size = stream.filesize  # Get the file size in bytes

            # Determine if the stream is progressive (both audio and video)
            is_progressive = stream.is_progressive

            # You can convert the file size to a more human-readable format (e.g., MB or GB)
            file_size_mb = file_size / (1024 * 1024)  # Convert bytes to megabytes

            # Determine the stream type based on the progressive attribute
            stream_type = 'Video and Audio' if is_progressive else 'Video Only' if 'video' in stream.type else 'Audio Only'

            stream_info.append({'quality': quality, 'file_format': file_format, 'file_size_mb': file_size_mb, 'stream_type': stream_type, 'index': idx})

        return render_template('display_streams.html', stream_info=stream_info, video_url=video_url)
    except Exception as e:
        return render_template('error.html', error_message=str(e))

@app.route('/download_selected', methods=['POST'])
def download_selected():
    try:
        video_url = request.form['video_url']
        selected_index = int(request.form['stream_index'])
        yt = YouTube(video_url)
        available_streams = list(yt.streams)

        if 0 <= selected_index < len(available_streams):
            selected_stream = available_streams[selected_index]
            return render_template('download.html', video_title=yt.title, selected_stream=selected_stream, selected_index=selected_index, video_url=video_url)
        else:
            return render_template('error.html', error_message="Invalid stream index")
    except Exception as e:
        return render_template('error.html', error_message=str(e))

@app.route('/download_video', methods=['POST'])
def download_video():
    try:
        video_url = request.form['video_url']
        selected_index = int(request.form['stream_index'])
        yt = YouTube(video_url)
        available_streams = list(yt.streams)

        if 0 <= selected_index < len(available_streams):
            selected_stream = available_streams[selected_index]

            # Get the stream URL
            stream_url = selected_stream.url

            # Use HEAD request to get the total file size
            response_head = requests.head(stream_url)
            total_file_size = int(response_head.headers.get('Content-Length', 0))

            # Calculate the chunk size based on the file size
            chunk_size = calculate_chunk_size(total_file_size)

            # Encode the filename using urllib.parse.quote
            filename = quote(f'{yt.title}.{selected_stream.subtype}')

            # Create a response that streams the video using requests
            response = Response(stream_with_requests(stream_url, chunk_size), content_type=selected_stream.mime_type)

            # Set the content disposition with the properly encoded filename
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

            # Set the Content-Length header to inform the browser of the total file size
            response.headers['Content-Length'] = str(total_file_size)

            return response
        else:
            return render_template('error.html', error_message="Invalid stream index")
    except Exception as e:
        return render_template('error.html', error_message=str(e))


def stream_with_requests(url, chunk_size):
    """Generator function to yield video chunks using requests."""
    with requests.get(url, stream=True) as response:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk

if __name__ == '__main__':
    app.run(debug=True)

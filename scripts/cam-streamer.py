"""A Python script to stream Raspi Camera output

Really inspited by Picamera recipe at https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming


Author: Alfredo -Rainbowbreeze- Morresi
"""

import io
import picamera
import logging
import socketserver
import datetime
from threading import Condition
from http import server

PAGE="""\
<html>
<head>
<title>PiCamera MJPEG streaming</title>
</head>
<body>
<h1>PiCamera MJPEG Streaming</h1>
<img src="stream.mjpg" width="800" height="600" />
</body>
</html>
"""

class StreamingOutput(object):
    """Define an output format suitable for streaming MJPEG on a web page
    """
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    """Handles the different requests for the streaming
    """
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()

        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                output = self.server.output
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))

        elif self.path == '/capture.html':
            
            try:
                # Create a filename using current date
                d = datetime.datetime.now()
                filename = "pictures/picture_{:%Y%m%d-%H%M%S.jpg}".format(d)
                self.server.camera.capture(filename, use_video_port = True)
                message = "Saved current frame to " + filename
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', len(message))
                self.end_headers()
                self.wfile.write(message.encode('utf-8'))
                self.log_message(message)

            except Exception as err:
                error_message = "Error while saving picture: {0}".format(err)
                self.send_error(500, message=error_message)  # Internal Server Error
                self.log_error(error_message)

        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    """Class to stream

    The class stores also instance variable used by the Handler to complete some requests.
    In particular, the PiCamera StreamingOutput object, and the PiCamera module itself

    https://docs.python.org/3/library/http.server.html#module-http.server
    """
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, output, picamera, *args, **kwargs):
        self.output = output
        self.camera = picamera
        super().__init__(*args, **kwargs)


    
def main():
    with picamera.PiCamera() as camera:
        # It's a RaspiCam 1.3, so the following resolution is the max available
        #  to obtain full FoV
        # https://picamera.readthedocs.io/en/release-1.13/fov.html#camera-modes
        camera.resolution = (2592, 1944)
        # Max 15 frames at this resolution
        camera.framerate = 12
        output = StreamingOutput()
        # Start the streaming. Because the page shows the camera output at
        #  800x600, the resize is done on-the-fly directly by the camera
        # https://picamera.readthedocs.io/en/release-1.13/recipes1.html#capturing-resized-images
        camera.start_recording(output, format='mjpeg', resize=(800, 600))
        try:
            address = ('', 8000)
            server = StreamingServer(output, camera, address, StreamingHandler)
            server.serve_forever()
        finally:
            camera.stop_recording()


if __name__ == "__main__":
    main()

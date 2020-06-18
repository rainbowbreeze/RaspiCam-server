"""A Python script to stream Raspi Camera output, and capture frames

Really inspited by Picamera recipe at https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming

Method documentation uses the Sphinx markup, a de-facto standard
 https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#python-signatures


Author: Alfredo -Rainbowbreeze- Morresi
"""

import io
import sys
import getopt
import logging
import socketserver
import datetime
import picamera
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
                output = self.server._output
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
                filename = self.server._output_folder + "picture_{:%Y%m%d-%H%M%S.jpg}".format(d)
                self.server._camera.capture(filename, use_video_port = True)
                message = "Saved current frame to " + filename
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', len(message))
                self.end_headers()
                self.wfile.write(message.encode('utf-8'))
                self.log_message(message)
                #TODO return the image instead of a text
            except Exception as err:
                error_message = "Error while saving picture: {0}".format(err)
                self.send_error(500, message=error_message)  # Internal Server Error
                self.log_error(error_message)

        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    """Class to stream the camera, with some enhancements

    The class stores also instance variable used by the Handler to complete some requests.
    In particular, the PiCamera StreamingOutput object, and the PiCamera module itself

    https://docs.python.org/3/library/http.server.html#module-http.server
    """
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, output, picamera, output_folder, *args, **kwargs):
        """Adding a could of variables to the standard constructor

        :param StreamingOutput output: the streaming output used by PiCamera
        :param PiCamera picamera: the PiCamera object itself
        :param str output_folder: the folder where images will be saved
        """
        self._output = output
        self._camera = picamera
        self._output_folder = output_folder
        if self._output_folder[-1] != "/":
            self._output_folder = self._output_folder + "/"
        super().__init__(*args, **kwargs)

def usage():
    logging.warning("Please specify the --folder (or -f) argument, the folder where to save the pictures")

    
def main(script_name, argv):
    """
    :param str script_name: the name of this script
    :param object argv: the array with the command line arguments
    """
    output_folder = None
    
    # Read command line arguments
    try:
        opts, args = getopt.getopt(argv, "f:", ["folder="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-f", "--folder"):
            output_folder = arg

    if None == output_folder:
        usage()
        sys.exit(2)

    print("Starting the PiCam server, saving pictures under {0}".format(output_folder))
    logging.info("Starting the PiCam server, saving pictures under {0}".format(output_folder))
    #TODO check for the output folder and, in case, create it

    with picamera.PiCamera() as camera:
        # It's a RaspiCam 1.3, so the following resolution is the max available
        # https://picamera.readthedocs.io/en/release-1.13/fov.html#camera-modes
        #  to obtain full FoV
        camera.resolution = (2592, 1944)
        # Max 15 frames at this resolution
        camera.framerate = 12
        output = StreamingOutput()
        # Start the streaming. Because the page shows the camera output at
        #  800x600, the resize is done on-the-fly, directly by the camera
        # https://picamera.readthedocs.io/en/release-1.13/recipes1.html#capturing-resized-images
        camera.start_recording(output, format='mjpeg', resize=(800, 600))
        try:
            address = ('', 8000)
            server = StreamingServer(output, camera, output_folder, address, StreamingHandler)
            server.serve_forever()
        finally:
            camera.stop_recording()


if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])

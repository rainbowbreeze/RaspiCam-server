# RaspiCam-server
A server + utils to manage a Raspberry Pi Camera


## Installation
Please refer to [Picamera install guide](https://picamera.readthedocs.io/en/release-1.13/install.html). But, in theory, the system should be already configured to run the server


## Base logic
The scipt create a server streaming camera video using M-JPEG format. It can be reached via http://%server_ip%:8000
In addition, visiting the url http://%server_ip%/capture.html it captures the current frame on a file

## Start the streaming server as a linux server


## Capturing images at given time
In order to capture images at a given time (for example, for a timelapse), create a cronjob for the given interval

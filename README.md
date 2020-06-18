# RaspiCam-server
A server + utils to manage a Raspberry Pi Camera


## Installation
To run the server, please refer to [Picamera install guide](https://picamera.readthedocs.io/en/release-1.13/install.html). But, in theory, the system should be already configured to run the server

For the additional commands (capture an image using a cronjob, backup of images), the following packages are required  
curl, rsync


## Base logic
The scipt create a server streaming camera video using M-JPEG format. It can be reached via http://%server_ip%:8000
In addition, visiting the url http://%server_ip%/capture.html captures the current frame on a file


## Start the streaming server as a linux server
A [systemd Service](https://wiki.debian.org/systemd/Services) concept is used to start the streamer at reboot

Create /etc/systemd/system/raspicam-server.service file
```
[Unit]
Description=RaspiCam Server
After=network.target

[Service]
Type=simple
Restart=always
ExecStart=python3 %Your_script_dir%/cam-streamer.py --folder %folder_where_download_pictures%

[Install]
WantedBy=multi-user.target
```

Enable the server:
```
sudo systemctl enable raspicam-server.service
```
The command output should look like
Created symlink /etc/systemd/system/multi-user.target.wants/raspicam-server.service → /etc/systemd/system/raspicam-server.service.

And, finally, start the server:
```
sudo systemctl start raspicam-server.service
```

To check the status:
```
sudo systemctl status raspicam-server.service
```

TODO: run the service with non-priviledged user. Potentially, using this tutorial
https://indomus.it/guide/come-installare-e-configurare-home-assistant-su-un-raspberry-pi-gia-in-uso/#autostart


## Capturing images at given time
In order to capture images at a given time (for example, for a timelapse), create a cronjob for the given interval.

First, check the script has execution permission
```
chmod +x %Your_script_dir%/capture_frame.sh
```

The following examples runs at every 15th minute past every hour from 7 through 18 on every day-of-week from Monday through Saturday.

crontab -e  
```
*/15 7-18 * * 1-6 %Your_script_dir%/capture_frame.sh
```



Some links on how to manage cronjobs
- [How To Add Jobs To cron Under Linux or UNIX](https://www.cyberciti.biz/faq/how-do-i-add-jobs-to-cron-under-linux-or-unix-oses/)
- [Crontab guru](https://crontab.guru/every-5-minutes)
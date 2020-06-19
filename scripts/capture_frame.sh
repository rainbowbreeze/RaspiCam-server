#!/bin/bash


check_for_rainbow_notify_and_curl()  {
  # Inspired by https://stackoverflow.com/questions/592620/how-can-i-check-if-a-program-exists-from-a-bash-script
  if ! hash rainbow-notifyadmin.sh 2>/dev/null; then
    echo "rainbow-notifyadmin.sh command not found, quit" 
    exit 2
  fi
  if ! hash curl 2>/dev/null; then
    echo "curl command not found, quit" 
    exit 2
  fi
}


main() {
    # call the RaspiCam Server with the url to save the current frame
    #curl http://127.0.0.1:8000/capture.html
    curl --fail http://localhost:8000/capture.html 2>/dev/null;

    local result_code=$?
    # As per curl exit statuses at https://ec.haxx.se/usingcurl/usingcurl-returns ,
    #  22 is used when something goes wrong server side, and no output is
    #  desired
    #  The  -f, --fail has to be used to obtain the status code. Otherwise
    #   it's always 0, regardless the server error
    if [ "$result_code" = "0" ]; then
        echo "Error with result code: ${result_code}"
        # Some error happened
        rainbow-notify-admin.sh "Cannot extract a frame from the camera, error code $result_code"
    fi
}


check_for_rainbow_notify_and_curl
main

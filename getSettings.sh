gphoto2 --auto-detect > cameraLog.txt
echo -en "\n" >> cameraLog.txt
gphoto2 --get-config=iso >> cameraLog.txt
echo -en "\n" >> cameraLog.txt
gphoto2 --get-config=shutterspeed >> cameraLog.txt
echo -en "\n" >> cameraLog.txt
gphoto2 --get-config=f-number >> cameraLog.txt
echo -en "\n" >> cameraLog.txt

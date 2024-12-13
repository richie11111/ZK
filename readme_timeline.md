This code takes the json export of a Google timeline from an Android phone and converts it to an Excel file focusing on time and location. I use a Samsung S21 plus and exported my timeline to my computer. 
To export the timeline --> Your phone can export a JSON file with the Timeline data it has, similar to the old Takeout.
Android: Go to device Settings > Location > Location Services > Timeline > "Export Timeline data" button"
Use this python code to convert that timeline.json to a csv file. You will need to replace the file location with your own in the python code. You may have to do some formatting of the csv file afterwards to get it looking the way you want. 
I ran this python code using Microsoft Visual Studio. Copy and paste the source code into Visual Studio, reeplace the file locations with where your input json file is and where you want the csv file to be then run it.
Please let me know how it goes.

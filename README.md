# apple_health_xml_to_workout
Take the data from an exported XML file from Apple Health and prepare workouts to be logged by Apple Shortcuts.

After running apple_export.py in Python, it generates a file called "workouts_with_mets_and_weight.csv" with the following headings: workoutActivityType, duration, distance, calories, and startDate. Save the CSV file as workouts.csv in a folder called "health" in your iCloud folder (or somewhere on your iPhone). Add the Apple Shortcut from the link below to your Shortcuts app then run the shortcut.
[Log Workouts from CSV to iPhone](https://www.icloud.com/shortcuts/1576ba7255c44180b184ce321e0b1bfc)




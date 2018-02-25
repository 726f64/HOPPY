# HOPPY
A Smart Irrigation System using a Raspberry Pi. This is my entry to the Farnell Element14 'Mixing Electronics and Water' held Spring 2018. The aim of E14's competition is to use electronics in a way that can help save water. Search https://www.element14.com for details.

The idea for this project is that the Pi can access the WWW and more specifically a weather API. I've chosen the MetOffice's site as I live in the UK and it seemed quite simple to get started (I've never really done much with Python nor APIs/JSON before). The API returns JSON data to the Pi about the upcoming weather. I will try and make a sensible algorithm in there to determine if the irrigation system waters the plants or not. 

Such a system would likely not be too useful in places where water is plentiful or from mains supplies - however I think it will be really useful if the water is perhaps roof run off to a water barrel. This should prevent watering the plants and using the barrel's supply up when the next day is is probably going to rain anyway.

import speech_recognition as sr
import time as t
import gtts

def SpeechToText():
        r = sr.Recognizer()   #Speech recognition
        with sr.Microphone() as source:
            print("Say something!")

            r.adjust_for_ambient_noise(source, duration=5)

            audio = r.listen(source)
            
           
        try:
            message = r.recognize_google(audio)
            print("User: " + message)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))
        return message
SpeechToText()

# importing the pyttsx library 
import pyttsx3 
def play_text(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 105)
    engine.say(text) 
    engine.runAndWait() 

# play_text("9 9 5 3 2 2 3 6 4 9")
# play_text("Please Enter your  ID")
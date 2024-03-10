#headers:
import tkinter as tk
from tkinter import Toplevel, Listbox
from PIL import Image, ImageTk
import pandas
from urllib.request import urlopen #why is this blue
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
import time
from tkinter.scrolledtext import ScrolledText
from io import BytesIO

class analysis(object):

    def __init__(self):

        self.chatList = []

        self.APIURL = "https://api-inference.huggingface.co/models/google/gemma-2b-it"
        self.headers = {"Authorization": "Bearer <INSERT API KEY HERE> "} #I have omitted my Huggingface API key for obvious reasons. If you want to test the program you will have to get your own - sorry :)

        self.selectedDriver = None
        self.selectedDriverNumber = None

        sessions = urlopen("https://api.openf1.org/v1/sessions?")
        sessionData = json.loads(sessions.read().decode('utf-8'))
        self.session = sessionData[-1]["session_key"]
        newUrl = "https://api.openf1.org/v1/drivers?session_key=" + str(self.session)
        drivers = urlopen(newUrl)
        self.driversData = json.loads(drivers.read().decode('utf-8'))
    
        self.root = tk.Tk()
        self.root.title("F1 Proto")

        # initialize the flags
        self.driver_window_open = False
        self.mode_window_open = False
        self.chatbotOpen = False
        self.radioWindowOpen = False

        width = 1280
        height = 720
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.root.geometry(alignstr)
        self.root.resizable(width=False, height=False)

        bg_image = Image.open("interfaceFiles/liveMenu.png")
        bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = tk.Label(self.root, image=bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label.image = bg_photo

        self.chatbot_Window_Button = tk.Button(self.root, text="Open AI Analyst", command=self.chatbotWindow,bg="#68c6c3",fg="black")
        self.chatbot_Window_Button.place(x=470,y=700)

        self.radio_window_button = tk.Button(self.root, text="Open Radio Listener", command=self.radioWindow,bg="#68c6c3",fg="black")
        self.radio_window_button.place(x=700,y=700)

        self.open_driver_window_button = tk.Button(self.root, text="Open Driver Select", command=self.driverWindow,bg="#68c6c3",fg="black")
        self.open_driver_window_button.place(x=10,y=700)

        self.open_mode_window_button = tk.Button(self.root, text="Open Mode Select", command=self.modeWindow,bg="#68c6c3",fg="black")
        self.open_mode_window_button.place(x=230,y=700)

        self.selected_driver_label = tk.Label(self.root, text="No driver selected", bg="#68c6c3",fg="black")
        self.selected_driver_label.place(x=10, y=680) 

        self.mode_window_label = tk.Label(self.root, text="Default Mode: Single Sector Mode", bg="#68c6c3",fg="black")
        self.mode_window_label.place(x=230,y=680)

        self.graph_Window_button = tk.Button(self.root, text="Toggle Graph Details", command=self.openGraph,bg="#68c6c3",fg="black")
        self.graph_Window_button.place(x=840,y=700)

        self.selectedMode = "Single Sector Mode"

        self.radioNumber = 0
        self.chatHistory = ""

        self.showGraph = False

        self.start_updating()
        self.root.mainloop()

    def radioWindow(self):
        if not self.radioWindowOpen:

            self.radioWindowOpen = True
            self.rwin = Toplevel(self.root)
            self.rwin.title = ("Radio Listener")

            self.rwin.protocol("WM_DELETE_WINDOW", self.onRadioClose)

            width = 640
            height = 360
            screenwidth = self.rwin.winfo_screenwidth()
            screenheight = self.rwin.winfo_screenheight()
            alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) // 2, (screenheight - height) // 2)
            self.rwin.geometry(alignstr)
            self.rwin.resizable(width=False, height=False)

            searchbutton = tk.Button(self.rwin, command=self.getRadio,text="Get Team Radio")
            searchbutton.place(relx=0.2,rely=0.9,relwidth=0.8,relheight=0.1)

            rwinlabel = tk.Label(self.rwin, text="Team Radio URL Links")
            rwinlabel.place(relx=0.2,y=0,relwidth=0.8,relheight=0.1)

            self.radioListbox = tk.Listbox(self.rwin)
            self.radioListbox.place(x=0,rely=0.1, relwidth=0.2,relheight=0.9)

            self.radios = ScrolledText(self.rwin, state='disabled', wrap=tk.WORD)
            self.radios.place(relx=0.2,rely=0.1,relheight=0.8,relwidth=0.8)

            driversSet = set()

            for driver in self.driversData:
                driversSet.add(driver["full_name"])

            for driver in driversSet:
                self.radioListbox.insert(tk.END, driver)

            teamLabel = tk.Label(self.rwin, text="Drivers:")
            teamLabel.place(x=0,y=0,relwidth=0.2,relheight=0.1)

    def getRadio(self):
        selected_index = self.radioListbox.curselection()
        print(selected_index)
        if selected_index:
            selectedRadioListen = self.radioListbox.get(selected_index[0])

            for driver in self.driversData:
                if driver["full_name"] == selectedRadioListen:
                    self.radioNumber = driver["driver_number"]
                    print(self.radioNumber)

        if self.radioNumber != 0:
                radioURL = "https://api.openf1.org/v1/team_radio?session_key="+str(self.session)+"&driver_number="+str(self.radioNumber)
                print(radioURL)
                radios = urlopen(radioURL)
                radioEntries = json.loads(radios.read().decode('utf-8'))
                print(radioEntries)
                for radioEntry in radioEntries:
                    self.radios.insert(tk.END, radioEntry["recording_url"], "\n")
   
    def onRadioClose(self):
        self.radioWindowOpen=False
        self.radioNumber = 0
        self.rwin.destroy()

    def chatbotWindow(self):
        if not self.chatbotOpen:
            self.chatbotOpen = True
            self.cwin = Toplevel(self.root)
            self.cwin.title("AI Analyst")

            self.cwin.protocol("WM_DELETE_WINDOW", self.on_chatBot_window_close)

            width = 640
            height = 360
            screenwidth = self.cwin.winfo_screenwidth()
            screenheight = self.cwin.winfo_screenheight()
            alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) // 2, (screenheight - height) // 2)
            self.cwin.geometry(alignstr)
            self.cwin.resizable(width=False, height=False)

            self.chat_history = ScrolledText(self.cwin, state='disabled', wrap=tk.WORD)
            self.chat_history.place(x=0,y=0, relheight=0.8,relwidth=1)

            self.chat_input = tk.Entry(self.cwin)
            self.chat_input.place(rely=0.82,x=0, relheight=0.15,relwidth=1)
            self.chat_input.bind("<Return>", self.send_message)

    def query(self, input):
            
            payload = {

                "inputs": self.chatHistory,
                "parameters": {"max_new_tokens": 250}
            }
            
            response = requests.post(self.APIURL, headers=self.headers, json=payload).json()
            generated_text = response[0]["generated_text"]
            answerPrefixx = 'model'
            actualResponse = generated_text.rsplit(answerPrefixx)[-1].strip()
            self.chatList.append(input)
            self.updateChatHistoryistory("Analyst: " + actualResponse)
            self.updateChatHistoryistory("\n")
            return actualResponse
    
    def send_message(self, event):

        user_message = self.chat_input.get()

        self.updateChatHistoryistory(f"You: {user_message}")
        self.updateChatHistoryistory("\n")

        self.chat_input.delete(0, tk.END)

        self.chatHistory += ("<rules> you are an f1 data analyst. please try to keep your answers super short. <start_of_turn>user " + user_message + "<end_of_turn> <start_of_turn>model")

        self.query(user_message)

    def on_chatBot_window_close(self):
        self.chat_history = "";
        self.chatbotOpen = False
        self.cwin.destroy()
        
    def updateChatHistoryistory(self, message):
        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, message + "\n")
        self.chat_history.configure(state='disabled')
        self.chat_history.yview(tk.END)

    def driverWindow(self):
        if not self.driver_window_open: 
            self.driver_window_open = True  
            self.dwin = Toplevel(self.root)
            self.dwin.title("Driver Select")
            
            self.dwin.protocol("WM_DELETE_WINDOW", self.on_driver_window_close)
            
            self.driver_listbox = Listbox(self.dwin)
            self.driver_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            confirm_button = tk.Button(self.dwin, text="Confirm", command=self.confirm_driver)
            confirm_button.pack(pady=10)

            driversSet = set()

            for driver in self.driversData:
                driversSet.add(driver["full_name"])

            for driver in driversSet:
                self.driver_listbox.insert(tk.END, driver)      
    
    def confirm_driver(self):
        selected_index = self.driver_listbox.curselection()
        if selected_index:
            self.selectedDriver = self.driver_listbox.get(selected_index[0])

            for driver in self.driversData:
                if driver["full_name"] == self.selectedDriver:
                    self.selectedDriverNumber = driver["driver_number"]
                    self.selectedTeamColour = driver["team_colour"]
                    driverMug = driver["headshot_url"]
                    print(driverMug)
                    print(self.selectedDriverNumber)

            if driverMug:
                with urlopen(driverMug) as mug:
                    mugData = mug.read()
                
                pil_image = Image.open(BytesIO(mugData))
                tk_image = ImageTk.PhotoImage(pil_image)

                mug = tk.Label(self.root, image=tk_image)
                mug.place(x=0,y=582)

                mug.image = tk_image

            self.selected_driver_label.config(text=f"Selected Driver: {self.selectedDriver}")
            self.selected_driver_label.config(bg="#" + str(self.selectedTeamColour))
            self.dwin.destroy()
            self.driver_window_open = False
        else:
            print("No driver selected")

    def on_driver_window_close(self):
        self.driver_window_open = False
        self.dwin.destroy()
    
    def modeWindow(self):
        if not self.mode_window_open:
            self.mode_window_open = True
            self.mwin = Toplevel(self.root)
            self.mwin.title = ("Mode Select")

            self.mwin.protocol("WM_DELETE_WINDOW", self.on_mode_window_close)

            self.mode_listbox = Listbox(self.mwin)
            self.mode_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

            confirm_mode_button = tk.Button(self.mwin, text="Confirm", command=self.confirm_mode)
            confirm_mode_button.pack(pady=10)

            self.mode_listbox.insert(tk.END, "Single Sector")
            self.mode_listbox.insert(tk.END, "Compare Sector")
            self.mode_listbox.insert(tk.END, "Per Sector Gap")      

    def confirm_mode(self):
        selected_index = self.mode_listbox.curselection()
        if selected_index:
            self.selectedMode = self.mode_listbox.get(selected_index[0])
    
    def on_mode_window_close(self):
        self.mode_window_open = False
        self.mwin.destroy()
        
        self.mode_window_label.config(text=f"Selected Mode: {self.selectedMode}")
        self.mwin.destroy()
        self.mode_window_open = False

    def openGraph(self):
        self.showGraph = not self.showGraph
    
    def start_updating(self):
        
        if self.selectedDriverNumber:

            lapUrl = "https://api.openf1.org/v1/laps?session_key="+str(self.session)+"&driver_number="+str(self.selectedDriverNumber) 
            lapJson = urlopen(lapUrl) 
            self.lapData = json.loads(lapJson.read().decode('utf-8'))
            df = pd.DataFrame(self.lapData)

            plt.figure(figsize=(12, 6))
            
            # Set the face and edge color to black
            plt.rcParams['axes.facecolor'] = 'black'
            plt.rcParams['axes.edgecolor'] = 'white'
            plt.rcParams['axes.labelcolor'] = 'white'
            plt.rcParams['xtick.color'] = 'white'
            plt.rcParams['ytick.color'] = 'white'
            plt.rcParams['grid.color'] = 'white'

            if self.selectedMode == "Single Sector":
                plt.plot(df['lap_number'], df['duration_sector_1'], color='cyan', label='Sector 1')
                plt.plot(df['lap_number'], df['duration_sector_2'], color='magenta', label='Sector 2')
                plt.plot(df['lap_number'], df['duration_sector_3'], color='yellow', label='Sector 3')

            elif self.selectedMode == "Per Sector Gap":
                print("N/A - Feature not present yet.")

            plt.title('Lap Duration Over Laps: ' + self.selectedDriver)
            plt.xlabel('Lap Number', color = 'white')
            plt.ylabel('Lap Duration (seconds)',color = 'white')

            plt.grid(True)
            
            legend = plt.legend(facecolor='lightgray') 
            plt.setp(legend.get_texts(), color='black')

            plt.savefig("data/lap_times.png", facecolor='black')

            if self.showGraph:
                plt.show()
            else:
                plt.close()

            graph_image = Image.open("data/lap_times.png")
            graph_photo = ImageTk.PhotoImage(graph_image)
            graph_label = tk.Label(self.root, image=graph_photo)
            graph_label.place(x=100,rely=0.14, width=1100, relheight= 0.8)
            graph_label.image = graph_photo

        self.root.after(1000, self.start_updating)
 
if __name__ == "__main__":
    app = analysis()

# Program by Elliott Jones (with a bit of help from GPT-4)
# Created 02/03/2024
# 
# 02/03 - Added main menu
# 04/03 - Added pandas and matplotlib for graph manipulation
# 06/03 - Begun AI model solution
# 09/03 - Added radio listener, beautified main menu, finally got AI working
# 10/13 - Further polished main meny, cleaned up code for final submission - well done me :D
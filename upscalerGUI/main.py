import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
import os
import glob
import requests
from PIL import Image
import numpy as np
import io
from urllib.request import urlretrieve

#FileChooser
class Box(BoxLayout):
    def __init__(self, callback):
        super().__init__()
        #Parent for dismissing the popup
        self.parent = None
        #Callback for updating the selected file/directory
        self.callback = callback

    def open(self, filename):
        if self.parent != None:
            self.parent.dismiss()
        self.callback(filename)
    
#Main Page
class Main(BoxLayout):
    def __init__(self):
        super().__init__()

        self.saved_file_path = ""
        self.path_is_directory = False
        self.api_url = "http://localhost:5000/predict"
        self.use_alt_api = True
        self.alt_api_url = "https://api.picsart.io/tools/1.0/upscale"
        self.alt_api_key = "xVCxSVMNlrOa1ZGBjiXUelQZvcMIoIXf"
        #Valid image files
        self.IMG_EXTENSIONS = ['.jpg','.jpeg', '.png', '.ppm', '.bmp','.tif']
        #Label that tracks loaded file/directory
        self.loaded_label = Label(text="")
        self.add_widget(self.loaded_label)

        self.button = Button(text="Abrir explorador")
        self.add_widget(self.button)
        self.button.bind(on_release=self.open)

        self.request_button = Button(text= "Fazer inferência")
        self.add_widget(self.request_button)
        self.request_button.bind(on_release=self.make_request)

    def open(self, instance):
        box = Box(self.save_filepath)
        popup = Popup(title='Explorador de Arquivos', content=box, size_hint=(None, None), size=(800, 400))
        box.parent = popup
        popup.open()
    
    def save_filepath(self, filename):
        if len(filename) != 0 and self.is_valid_file(filename[0]):
            self.saved_file_path = filename[0]
            #print(filename)
            if self.path_is_directory:
                #Sets the label format
                label_text = ""
                for image in self.get_image_files(filename[0], no_extension=True):
                    label_text += image+'\n'
                self.loaded_label.text = label_text
            else:
                self.loaded_label.text = os.path.basename(filename[0])

        else:
            self.saved_file_path = ""
            self.loaded_label.text = ""
    
    def is_valid_file(self, filename):
        if os.path.isdir(filename):
            if len(self.get_image_files(filename)) !=0:
                self.path_is_directory = True
                return True
            else:
                self.path_is_directory = False
                return False
        else:
            if any(filename.endswith(extension) for extension in self.IMG_EXTENSIONS):
                self.path_is_directory = False
                return True
    
    def get_image_files(self, filename, no_extension=False):
        image_list = []
        for extension in self.IMG_EXTENSIONS:
            search = filename+'/*'+extension
            image_list += glob.glob(search)
        if no_extension:
            for i in range(len(image_list)):
                image_list[i] =  os.path.basename(image_list[i])
            return image_list
        else:
            return image_list

    def make_request(self, instance):
        if self.saved_file_path != "":
            if self.path_is_directory:
                for f in self.get_image_files(self.saved_file_path):
                    file = [(os.path.basename(f), open(f, 'rb'))]
                    response = self.send_request(file)
                    self.save_response_files(response, file[0][0])
            else:
                file = [(os.path.basename(self.saved_file_path), open(self.saved_file_path, 'rb'))]
                response = self.send_request(file)
                print(response.json())
                self.save_response_files(response, file[0][0])

    def send_request(self, file):
        if not self.use_alt_api:
            response = requests.post(url=self.api_url, 
                                    files=file)
            return response
        else:
            print(file)

            files = { "image": (file[0][0], file[0][1], "image/png") }
            payload = {
                "upscale_factor": "x2",
                "format": "PNG"
            }
            headers = {"accept": "application/json",
                       "X-Picsart-API-Key": self.alt_api_key}
        
            response = requests.post(self.alt_api_url, data=payload, files=files, headers=headers)
            return response
    
    def save_response_files(self, response, filename):
        if self.use_alt_api:
            if response.status_code == 200 and response.json()['status'] == 'success':
                query_parameters = {"downloadformat": "png"}
                download_response = requests.get(response.json()['data']['url'], params=query_parameters, stream=True)
                with open(filename, 'wb') as f:
                    f.write(download_response.content)
        else:
            image = Image.open(io.BytesIO(response.content))
            image.save(filename, "PNG")



class MyApp(App):
    def build(self):
        self.title = "Upscaler"
        return Main()

if __name__ == "__main__":
    MyApp().run()
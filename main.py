from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse 
import pandas as pd 
import nltk
from nltk.tokenize import word_tokenize 
from nltk.corpus import wordnet  
import numpy as np

#nltk.data.path.append(r'C:\Users\1\AppData\Local\Programs\Python\Python311\Lib\site-packages\nltk')
nltk.data.path.append(r'C:\Users\1\OneDrive\Desktop\Bootcamp_IA\ProyectoFinalGrupo11\venv\Lib\site-packages\nltk')

nltk.download('punkt') 
nltk.download('wordnet') 
nltk.download('punkt_tab')

# Cargar el archivo CSV en un DataFrame de Pandas
file_path = r"C:\Users\1\OneDrive\Desktop\Bootcamp_IA\ProyectoFinalGrupo11\dataset\Calidad_del_Agua_para_Consumo_Humano_en_Colombia_20250215.csv"


# Diccionario de reemplazo para quitar tildes
reemplazos = {
    'á': 'a',
    'é': 'e',
    'í': 'i',
    'ó': 'o',
    'ú': 'u',
    'Á': 'A',
    'É': 'E',
    'Í': 'I',
    'Ó': 'O',
    'Ú': 'U'}

# Función para reemplazar tildes usando el diccionario
def quitar_tildes(s):
    for acentuada, sin_tilde in reemplazos.items():
        s = s.replace(acentuada, sin_tilde)
    return s


# Función para cargar el dataset de mediciones desde un archivo CSV
def load_water():
    df = pd.read_csv(file_path, encoding="utf-8", sep=";", on_bad_lines="skip", dtype=str)
    df["IRCA"] = pd.to_numeric(df["IRCA"], errors='coerce') #Convertir la columna 'Salario' a numérica
    df = df.dropna()  # Elimina todas las filas que contienen al menos un valor faltante
    df['Departamento'] = df['Departamento'].apply(quitar_tildes)
    df['Municipio'] = df['Municipio'].apply(quitar_tildes)
    return df.fillna('').to_dict(orient='records')

# Cargamos la base al iniciar la API para no leer el archivo cada vez que alguien pregunte por ellas.
water_list = load_water()


# Función para encontrar sinónimos de una palabra
def get_synonyms(word): 
    # Usamos WordNet para obtener distintas palabras que significan lo mismo.
    return{lemma.name().lower() for syn in wordnet.synsets(word) for lemma in syn.lemmas()}


# Creamos la aplicación FastAPI, que será el motor de nuestra API
# Esto inicializa la API con un nombre y una versión
app = FastAPI(title="Informe de mediciones de calidad del agua", version="1.0.0")


# Ruta de inicio: Cuando alguien entra a la API sin especificar nada, verá un mensaje de bienvenida.
@app.get('/', tags=['Home'])
def home():
# Cuando entremos en el navegador a http://127.0.0.1:8000/ veremos un mensaje de bienvenida
    return HTMLResponse('<h1>Bienvenido al informe de mediciones de calidad del agua en Colombia 2017-2023</h1>')


@app.get('/water', tags=['Water_samples'])
def get_water():
    # Si hay mediciones, las enviamos, si no, mostramos un error
    return water_list[:100] or HTTPException(status_code=500, detail="No hay datos de mediciones de calidad de agua disponibles")



# Ruta para obtener una medición específica según su ID
@app.get('/water/{id}', tags=['Water_samples_id'])
def get_water_id(id: str):
    # Buscamos en la lista de mediciones la que tenga el mismo ID
    return next((m for m in water_list if m['id'] == id), {"detalle": "medición no encontrada"})



# Ruta para buscar mediciones por departamento y municipio específico
@app.get ('/water/departamento/', tags=['Water_samples_depart'])
def get_water_departamento(Departamento: str, Municipio:str=None):
    # Filtramos la lista de mediciones según la calificación ingresada
    if Municipio:
        Departamento = quitar_tildes(Departamento)
        Municipio = quitar_tildes(Municipio)
        return [m for m in water_list if Departamento.lower() in m['Departamento'].lower() and Municipio.lower() in m['Municipio'].lower()]
    else:
        Departamento = quitar_tildes(Departamento)
        return [m for m in water_list if Departamento.lower() in m['Departamento'].lower()]




# Ruta del chatbot que responde con las mediciones según palabras clave de la categoría
@app.get('/chatbot', tags=['Chatbot'])
def chatbot(query: str):
    # Dividimos la consulta en palabras clave, para entender mejor la intención del usuario
    query_words = word_tokenize(query.lower())
    
    # Buscamos sinónimos de las palabras clave para ampliar la búsqueda
    synonyms = {word for q in query_words for word in get_synonyms(q)} | set(query_words)

    # Filtramos la lista de películas buscando coincidencias en el año
    results = [m for m in water_list if any (s in m['Periodo'].lower() for s in synonyms)]

     # Si encontramos mediciones, enviamos la lista; si no, mostramos un mensaje de que no se encontraron coincidencias
    return JSONResponse (content={
        "respuesta": "Aquí tienes algunas mediciones relacionadas con el año de consulta." if results else "No encontré mediciones relacionadas con el año de consulta.",
        "mediciones": results
    })









# INTERFAZ GRAFICA


import requests
from delphifmx import *

BASE = "http://127.0.0.1:9000/"


class CalidadAgua(Form):
 
    def __init__(self, owner):
        # Iniciar la ventana
        self.SetProps(Caption = "Sistema de información de calidad del agua en Colombia", OnShow = self.__form_show, OnClose = self.__form_close)
 
        # Crear label con mensaje de bienvenida "Mensaje"
        self.Mensaje = Label(self)
        self.Mensaje.SetProps(Parent = self, Text = "Bienvenido al sistema de información de calidad de agua en Colombia\n\nEn esta aplicación usted podrá consultar mediciones de calidad del agua en diferentes municipios de Colombia entre 2007-2023 y obtener información sobre enfermedades relacionadas con la calidad del agua y sus sintomas.\nAdemás podrá hacer uso de un chatbot interactivo para realizar consultas sobre el tema", 
                              Position = Position(PointF(20, 20)), 
                              Width=300, Height=160, WordWrap=True, TextAlign="Leading")


        # Crear label para filtro con id "VerId"
        self.VerId = Label(self)
        self.VerId.SetProps(Parent = self, Text = "Filtrar por id: ", Position = Position(PointF(370, 75)),  Width=120, Height=15, WordWrap=True, TextAlign="Leading")
 
        # Crear cuadro de texto "EscribirId"
        self.EscribirId = Edit(self)
        self.EscribirId.SetProps(Parent = self, Position = Position(PointF(480, 75)), Height = 15)
 

        # Crear label para filtro con departamento "VerDpto"
        self.VerDpto = Label(self)
        self.VerDpto.SetProps(Parent = self, Text = "Filtrar por departamento: ", Position = Position(PointF(370, 150)),  Width=150, Height=15, WordWrap=True, TextAlign="Leading")
 
        # Crear cuadro de texto "VerDpto"
        self.EscribirDpto = Edit(self)
        self.EscribirDpto.SetProps(Parent = self, Position = Position(PointF(520, 150)), Height = 15)


        # Crear label para filtro con Municipio "VerMun"
        self.VerMun = Label(self)
        self.VerMun.SetProps(Parent = self, Text = "Filtrar por municipio: ", Position = Position(PointF(370, 170)),  Width=150, Height=15, WordWrap=True, TextAlign="Leading")
 
        # Crear cuadro de texto "VerDpto"
        self.EscribirMun = Edit(self)
        self.EscribirMun.SetProps(Parent = self, Position = Position(PointF(520, 170)), Height = 15)


        # Creating a Button named addEmployee that, when clicked, adds the entries in the textboxes to the database. The Button also displays some text specified in the “Text” parameter.
        #self.addEmployee = Button(self)
        #self.addEmployee.SetProps(Parent = self, Text = "Add Employee", Position = Position(PointF(250, 115)), Width = 90, OnClick = self.__button_click_add)
 
        # Creat boton “view” que cuando se da clic muestra la lista de todas las mediciones
        self.view = Button(self)
        self.view.SetProps(Parent = self, Text = "Ver todas las mediciones", Position = Position(PointF(370, 25)), Width = 250, OnClick = self.__button_click_view)
 
         # Crear boton “viewId” que cuando se da clic muestra la medicion del id 
        self.viewId = Button(self)
        self.viewId.SetProps(Parent = self, Text = "Filtrar", Position = Position(PointF(380, 100)), Width = 200, OnClick = self.__button_click_id)
 
         # Creat boton “viewDM” que cuando se da clic muestra las mediciones del departamento y municipio
        self.viewDM = Button(self)
        self.viewDM.SetProps(Parent = self, Text = "Filtrar", Position = Position(PointF(380, 195)), Width = 200, OnClick = self.__button_click_DM)


        # Crear caja de texto “list” que muestra la lista de todas las mediciones
        self.list = ListBox(self)
        self.list.SetProps(Parent = self, Position = Position(PointF(20, 250)), Width = 1025, Height = 200)
 

    def __form_show(self, sender):
        self.SetProps(Width = 1080, Height = 500)
 
    def __form_close(self, sender, action):
        action = "caFree"
 
    #def __button_click_add(self, sender):
 
        # Initializing a JSON with all the employee details from the form.
        #myobj = {"id":int(self.editId.text), "firstName":self.editFName.text,"lastName":self.editLName.text,"gender":self.editGender.text,"role":self.editRole.text}
 
        # Posting the JSON using FASTApi to our Database.
        #x = requests.post(BASE+"users", json = myobj)
 
        # Adding the new Employee to our Database.
        #self.list.items.add(x.text)
        #self.list.items.add("Your Entry was successfully added!")
   
        # Resetting the text boxes as empty.
        #self.editFName.text = self.editLName.text = self.editGender.text = self.editRole.text = self.editId.text = ""
 
    def __button_click_view(self, sender):
        # Obtener los datos
        response = requests.get(BASE + "water")
        response = response.json()
        # Mostrar los datos
        self.list.items.text = ""
        for measure in response:
            self.list.items.add(measure)

    def __button_click_id(self, sender):
        # Obtener los datos del id
        myobj = str(self.EscribirId.text)
        response = requests.get(f"{BASE}/water/{myobj}")
        response = response.json()                                  
        # Mostrar los datos
        self.list.items.text = ""
        self.list.items.add(response)

    def __button_click_DM(self, sender):
        # Obtener los datos del dpto y mun
        dpto = str(self.EscribirDpto.text)
        mun = str(self.EscribirMun.text)
        response = requests.get(f"{BASE}/water/departamento/?Departamento={dpto}&Municipio={mun}")
        response = response.json()                                  
        # Mostrar los datos
        self.list.items.text = ""
        for measure in response:
            self.list.items.add(measure)







def main():
    Application.Initialize()
    Application.Title = "Calidad del agua en Colombia"
    Application.MainForm = CalidadAgua(Application)
    Application.MainForm.Show()
    Application.Run()
    Application.MainForm.Destroy()



if __name__ == '__main__':
    main()




# python -m virtualenv venv
# cd venv\Scripts\
# activate.bat
# aqui ya dentro del venv, se hacen los pip install

# deactivate.bat

# uvicorn main:app --reload --port 9000
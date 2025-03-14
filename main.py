
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

    # Definir respuestas predefinidas
    respuestas = {
        "enfermedades": "Las enfermedades relacionadas con el agua incluyen cólera, hepatitis A y otras.",
        "sintomas": "Los síntomas de enfermedades transmitidas por el agua pueden incluir diarrea, fiebre y vómitos.",
        "inviable": "Que el agua sea inviable significa que no es apta para consumo humano y puede causar brotes epidémicos graves. Las enfermedades asociadas incluyen cólera, hepatitis A, fiebre tifoidea, disentería bacteriana, giardiasis, amebiasis e intoxicaciones químicas como metales pesados y pesticidas. Los riesgos incluyen la muerte, especialmente en niños, adultos mayores e inmunosuprimidos, y la contaminación del suelo y ecosistemas por agentes químicos y biológicos.",
        "alto": "Riesgo alto significa que no es apta para consumo humano y puede causar infecciones graves. Las enfermedades asociadas incluyen diarreas infecciosas (rotavirus, norovirus, E. coli), hepatitis A, parasitosis intestinales (Giardia, Entamoeba histolytica), infecciones respiratorias por aerosoles contaminados y leptospirosis. Los riesgos incluyen enfermedades gastrointestinales, exposición a contaminantes como arsénico o plomo, y efectos negativos en la higiene personal y preparación de alimentos.",
        "medio": "Riesgo medio significa que no es apta para consumo humano, pero puede usarse con precauciones para limpieza e higiene, como hervirla o filtrarla. Las enfermedades asociadas incluyen gastroenteritis bacteriana y viral, infecciones de piel y ojos (Staphylococcus, Pseudomonas), parásitos intestinales (Ascaris, Trichuris), y dermatitis por contacto. Los riesgos incluyen un aumento de enfermedades gastrointestinales en poblaciones vulnerables y la posible presencia de residuos fecales y bacterias patógenas. Si se usa para preparar alimentos, requiere tratamiento previo.",
        "bajo": "Riesgo bajo significa que no es apta para consumo humano, pero se puede tratar para hacerla potable mediante filtración y desinfección. Las enfermedades relacionadas incluyen gastroenteritis leve (E. coli, enterobacterias) y leves infecciones de piel y mucosas. Los riesgos incluyen bacterias coliformes y residuos orgánicos, y requiere hervirla o tratarla con cloro antes de consumirla. Tiene bajo riesgo de contaminación química.",
        "sin": "Sin riesgo significa que es apta para consumo humano, lo que garantiza seguridad sanitaria y reducción de enfermedades. Los beneficios incluyen una mejora en la calidad de vida y productividad, además de una disminución de los costos en salud pública. Los riesgos son mínimos, pero si no se mantiene un control adecuado en la red de distribución, puede haber contaminación. También, el exceso de cloro o tratamientos puede afectar el sabor o la calidad del agua.",
        "ahorra": "Para ahorrar agua en el hogar, cierra la llave mientras te cepillas los dientes y mientras te lavas las manos. Utiliza duchas de bajo flujo y cierra la llave mientras te enjabonas. Además, verifica y repara las fugas en llaves y tuberías, y recuerda cerrar las tuberías después de usar los grifos.",
        "contaminacion": "La contaminación del agua se produce cuando sustancias dañinas, como productos químicos, plásticos o desechos humanos, alteran la calidad del agua. Esto puede afectar la salud humana, los ecosistemas acuáticos y la biodiversidad en general.",
        "prevencion": "Para prevenir: no arrojes plásticos, sobras de comida u otros desechos sólidos al desagüe. Antes de lavar los platos, retira los residuos de comida y deposítalos en la basura. Evita arrojar sustancias químicas a los desagües y utiliza detergentes biodegradables. También puedes participar en la limpieza de playas, arroyos o humedales para proteger nuestros cuerpos de agua.",
        "conciencia": "Genera conciencia: informa a tus familiares y amigos sobre la importancia del ahorro de agua y la prevención de la contaminación. Busca información sobre prácticas sostenibles que puedas aplicar en tu hogar y comunidad. Reduce el consumo de productos que requieren grandes cantidades de agua para su producción y apoya a empresas que implementan prácticas sostenibles para cuidar el medio ambiente.",
        "colera": "Infección intestinal causada por la bacteria *Vibrio cholerae*, que provoca diarrea severa y deshidratación.",
        "hepatitis": "Enfermedad hepática viral causada por el virus de la hepatitis A, se transmite principalmente por agua o alimentos contaminados.",
        "tifoidea": "Infección bacteriana causada por *Salmonella typhi*, que causa fiebre, dolor abdominal y, a veces, diarrea.",
        "bacteriana": "Infección intestinal bacteriana que causa diarrea con sangre, fiebre y dolor abdominal, causada por bacterias como *Shigella*.",
        "giardiasis": "Infección intestinal causada por el parásito *Giardia lamblia*, que provoca diarrea, cólicos abdominales y náuseas.",
        "amebiasis": "Enfermedad intestinal causada por el parásito *Entamoeba histolytica*, que puede causar diarrea, dolor abdominal y en algunos casos, abscesos hepáticos.",
        "irca":" es el Índice de Riesgo de Contaminación Alimentaria, que se utiliza para evaluar el riesgo de contaminación de los alimentos y el impacto que esto puede tener en la salud pública. El IRCA tiene en cuenta factores como la calidad del agua, las condiciones de higiene en la preparación de alimentos, el almacenamiento, y el manejo de estos, para determinar el nivel de riesgo asociado con el consumo de alimentos contaminados."
    }

    
    
    # Buscamos sinónimos de las palabras clave para ampliar la búsqueda
    synonyms = {word for q in query_words for word in get_synonyms(q)} | set(query_words)


    # Verificamos si hay respuestas predefinidas
    respuesta_predefinida = next((respuestas[word] for word in query_words if word in respuestas), None)

    # Si encontramos mediciones, enviamos la lista; si no, mostramos un mensaje de que no se encontraron coincidencias
    return JSONResponse(content={
        "intro": "Aquí tienes la respuesta:",
        "respuesta": respuesta_predefinida
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
        self.Mensaje.SetProps(Parent = self, Text = "Bienvenido al sistema de información de calidad de agua en Colombia\n\nEn esta aplicación usted podrá consultar mediciones de calidad del agua en diferentes municipios de Colombia entre 2007-2023, en donde podrá visualizar el IRCA y el nivel de riesgo de cada zona.\nAdemás podrá hacer uso de un chatbot interactivo para realizar consultas sobre enfermedades relacionadas con la calidad del agua, sus sintomas y otros temas afines", 
                              Position = Position(PointF(20, 20)), 
                              Width=300, Height=180, WordWrap=True, TextAlign="Leading")


        # Crear label para filtro con id "VerId"
        self.VerId = Label(self)
        self.VerId.SetProps(Parent = self, Text = "Filtrar por id: ", Position = Position(PointF(370, 75)),  Width=120, Height=15, WordWrap=True, TextAlign="Leading")
 
        # Crear cuadro de texto "EscribirId"
        self.EscribirId = Edit(self)
        self.EscribirId.SetProps(Parent = self, Position = Position(PointF(480, 75)), Height = 15)
 

        # Crear label para filtro con departamento "VerDpto"
        self.VerDpto = Label(self)
        self.VerDpto.SetProps(Parent = self, Text = "Filtrar por departamento: ", Position = Position(PointF(370, 150)),  Width=150, Height=15, WordWrap=True, TextAlign="Leading")
 
        # Crear cuadro de texto "EscribirDpto"
        self.EscribirDpto = Edit(self)
        self.EscribirDpto.SetProps(Parent = self, Position = Position(PointF(520, 150)), Height = 15)


        # Crear label para filtro con Municipio "VerMun"
        self.VerMun = Label(self)
        self.VerMun.SetProps(Parent = self, Text = "Filtrar por municipio: ", Position = Position(PointF(370, 170)),  Width=150, Height=15, WordWrap=True, TextAlign="Leading")

        # Crear cuadro de texto "EscribirMun"
        self.EscribirMun = Edit(self)
        self.EscribirMun.SetProps(Parent = self, Position = Position(PointF(520, 170)), Height = 15)


        # Crear label para chatbot "Chatbot"
        self.Chatbot = Label(self)
        self.Chatbot.SetProps(Parent = self, Text = "Chatbot", Position = Position(PointF(700, 20)),  Width=150, Height=20, WordWrap=True, TextAlign="Leading")
 
        # Crear cuadro de texto "EscribirChatbot"
        self.EscribirChatbot = Edit(self)
        self.EscribirChatbot.SetProps(Parent = self, Position = Position(PointF(700, 45)), Width=320, Height = 150)
        self.EscribirChatbot.TextSettings.WordWrap = True  
        self.EscribirChatbot.TextSettings.HorzAlign = 'Leading'
        self.EscribirChatbot.TextSettings.VertAlign = 'Top'


        # Creat boton “view” que cuando se da clic muestra la lista de todas las mediciones
        self.view = Button(self)
        self.view.SetProps(Parent = self, Text = "Ver todas las mediciones", Position = Position(PointF(370, 25)), Width = 250, OnClick = self.__button_click_view)
 
         # Crear boton “viewId” que cuando se da clic muestra la medicion del id 
        self.viewId = Button(self)
        self.viewId.SetProps(Parent = self, Text = "Filtrar", Position = Position(PointF(380, 100)), Width = 200, OnClick = self.__button_click_id)
 
         # Creat boton “viewDM” que cuando se da clic muestra las mediciones del departamento y municipio
        self.viewDM = Button(self)
        self.viewDM.SetProps(Parent = self, Text = "Filtrar", Position = Position(PointF(380, 195)), Width = 200, OnClick = self.__button_click_DM)


         # Creat boton “viewchatbot” que cuando se da clic muestra las mediciones del departamento y municipio
        self.viewDM = Button(self)
        self.viewDM.SetProps(Parent = self, Text = "Consultar", Position = Position(PointF(770, 210)), Width = 200, OnClick = self.__button_click_chatbot)


        # Crear caja de texto “list” que muestra la lista de todas las mediciones
        self.ListBox = ListBox(self)
        self.ListBox.SetProps(Parent = self, Position = Position(PointF(20, 250)), Width = 1025, Height = 200)
 

         # Crear boton de Reset
        self.ResetButton = Button(self)
        self.ResetButton.SetProps(Parent=self, Text="Limpiar", Position=Position(PointF(100, 210)), Width=100, OnClick = self.__button_click_reset)
 

    def __form_show(self, sender):
        self.SetProps(Width = 1080, Height = 500)
 
    def __form_close(self, sender, action):
        action = "caFree"
 

    def __button_click_view(self, sender):
        # Obtener los datos
        response = requests.get(BASE + "water")
        response = response.json()
        # Mostrar los datos
        self.ListBox.items.text = ""
        for measure in response:
            self.ListBox.items.add(measure)
            

    def __button_click_id(self, sender):
        # Obtener los datos del id
        myobj = str(self.EscribirId.text)
        response = requests.get(f"{BASE}/water/{myobj}")
        response = response.json()                                  
        # Mostrar los datos
        self.ListBox.items.text = ""
        self.ListBox.items.add(response)


    def __button_click_DM(self, sender):
        # Obtener los datos del dpto y mun
        dpto = str(self.EscribirDpto.text)
        mun = str(self.EscribirMun.text)
        response = requests.get(f"{BASE}/water/departamento/?Departamento={dpto}&Municipio={mun}")
        response = response.json()                                  
        # Mostrar los datos
        self.ListBox.items.text = ""
        for measure in response:
            self.ListBox.items.add(measure)


    def __button_click_chatbot(self, sender):
        # Obtener respuesta
        question = str(self.EscribirChatbot.text)
        question = question.replace(' ', '%20')
        response = requests.get(f"{BASE}/chatbot?query={question}")
        response = response.json()                                  
        # Mostrar los datos
        self.ListBox.items.text = ""

        intro = response.get("intro", "No hay respuesta disponible")
        self.ListBox.items.add(f"{intro}")

        #respuesta = response.get("respuesta", [])
        #self.ListBox.items.add(f"Respuesta: {respuesta}")

        respuesta = response.get("respuesta", "")

        if respuesta is None:
            respuesta = ""

        max_line_length = 180
    
        if len(respuesta) > max_line_length:
            self.ListBox.items.add(f"Respuesta: ")
            for i in range(0, len(respuesta), max_line_length):
                chunk = respuesta[i:i + max_line_length]
                self.ListBox.items.add(f"{chunk}")
        else:
            self.ListBox.items.add(f"Respuesta: {respuesta}")



    def __button_click_reset(self, sender):
        self.EscribirId.Text = ""
        self.EscribirDpto.Text = ""
        self.EscribirMun.Text = ""
        self.EscribirChatbot.Text = ""
        self.ListBox.items.text = ""
        





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
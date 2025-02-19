from fastapi import FastAPI, HTTPException 
from fastapi.responses import HTMLResponse, JSONResponse 
import pandas as pd 
import nltk
from nltk.tokenize import word_tokenize 
from nltk.corpus import wordnet  
import numpy as np

nltk.data.path.append(r'C:\Users\1\AppData\Local\Programs\Python\Python311\Lib\site-packages\nltk')

nltk.download('punkt') 
nltk.download('wordnet') 
nltk.download('punkt_tab')

# Cargar el archivo CSV en un DataFrame de Pandas
file_path = r"C:\Users\1\OneDrive\Desktop\Bootcamp_IA\ProyectoFinalGrupo11\dataset\Calidad_del_Agua_para_Consumo_Humano_en_Colombia_20250215.csv"

# Función para cargar el dataset de mediciones desde un archivo CSV
def load_water():

# Leer el archivo con codificación adecuada para caracteres especiales
    df = pd.read_csv(file_path, encoding="LATIN", sep=";", on_bad_lines="skip", dtype=str)

    # Verificar los tipos de datos de cada columna
    df["IRCA"] = pd.to_numeric(df["IRCA"], errors='coerce') #Convertir la columna 'Salario' a numérica

    df = df.dropna()  # Elimina todas las filas que contienen al menos un valor faltante

    # Llenamos los espacios vacíos con texto vacío y convertimos los datos en una lista de diccionarios 
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
    return HTMLResponse('<h1>Bienvenido al informe de mediciones de calidad del agua en Colombia 2007-2023</h1>')


@app.get('/water', tags=['Water'])
def get_water():
    # Si hay mediciones, las enviamos, si no, mostramos un error
    return water_list or HTTPException(status_code=500, detail="No hay datos de mediciones de calidad de agua disponibles")


# Ruta para obtener una medición específica según su ID
@app.get('/water/{id}', tags=['Water'])
def get_water(id: str):
    # Buscamos en la lista de mediciones la que tenga el mismo ID
    return next((m for m in water_list if m['id'] == id), {"detalle": "medición no encontrada"})



# Ruta del chatbot que responde con las mediciones según palabras clave de la categoría
@app.get('/chatbot', tags=['Chatbot'])
def chatbot(query: str):
    # Dividimos la consulta en palabras clave, para entender mejor la intención del usuario
    query_words = word_tokenize(query.lower())
    
    # Buscamos sinónimos de las palabras clave para ampliar la búsqueda
    synonyms = {word for q in query_words for word in get_synonyms(q)} | set(query_words)

    # Filtramos la lista de películas buscando coincidencias en el año
    results = [m for m in water_list if any ((s in m['Periodo'].lower() for s in synonyms) and (s in m['Municipio'].lower() for s in synonyms))]

     # Si encontramos mediciones, enviamos la lista; si no, mostramos un mensaje de que no se encontraron coincidencias
    return JSONResponse (content={
        "respuesta": "Aquí tienes algunas mediciones relacionadas con el año de consulta." if results else "No encontré mediciones relacionadas con el año de consulta.",
        "mediciones": results
    })



# Ruta para buscar mediciones por departamento específico
@app.get ('/water/by_departamento/', tags=['Water'])
def get_water_by_departamento(Departamento: str):
    # Filtramos la lista de mediciones según la calificación ingresada
    return [m for m in water_list if Departamento.lower() in m['Departamento'].lower()]

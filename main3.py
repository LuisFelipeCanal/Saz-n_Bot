import pandas as pd
import streamlit as st
from datetime import datetime
from copy import deepcopy
#from groq import Groq
#import openai
from openai import OpenAI
import csv
import re
import pytz
import json
import logging
# Configura el logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Inicializar el cliente de Groq con la clave API
#client = Groq(api_key=st.secrets["GROQ_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Configuración inicial de la página
st.set_page_config(page_title="SazónBot", page_icon=":pot_of_food:")
st.title("🍲 SazónBot")

# Mensaje de bienvenida
intro = """¡Bienvenido a Sazón Bot, el lugar donde todos tus antojos de almuerzo se hacen realidad!
Comienza a chatear con Sazón Bot y descubre qué puedes pedir, cuánto cuesta y cómo realizar tu pago. ¡Estamos aquí para ayudarte a disfrutar del mejor almuerzo!"""
st.markdown(intro)


# Cargar el menú desde un archivo CSV
def load(file_path):
    """Cargar el menú desde un archivo CSV con columnas Plato, Descripción y Precio."""
    load = pd.read_csv(file_path)
    return load

# Cargar los distritos de reparto desde un archivo CSV
#def load_distritos(file_path):
 #   """Cargar los distritos de reparto desde un archivo CSV."""
  #  distritos = pd.read_csv(file_path)
   # return distritos

def format_menu(menu):
    if menu.empty:
        return "No hay platos disponibles."

    else:
        # Encabezados de la tabla
        table = "| **Plato** | **Descripción** | **Precio** |\n"
        table += "|-----------|-----------------|-------------|\n"  # Línea de separación
        
        # Filas de la tabla
        for idx, row in menu.iterrows():
            table += f"| {row['Plato']} | {row['Descripción']} | S/{row['Precio']:.2f} |\n"
        
        return table


# Mostrar el menú con descripciones
def display_menu(menu):
    """Mostrar el menú con descripciones."""
    menu_text = "Aquí está nuestra carta:\n"
    for index, row in menu.iterrows():
        menu_text += f"{row['Plato']}: {row['Descripción']} - {row['Precio']} soles\n"
    return menu_text

# Mostrar los distritos de reparto
def display_distritos(distritos):
    """Mostrar los distritos de reparto disponibles."""
    distritos_text = "Los distritos de reparto son:\n"
    for index, row in distritos.iterrows():
        distritos_text += f"**{row['Distrito']}**\n"
    return distritos_text

def display_postre(postre):
    """Mostrar el menú con descripciones."""
    postre_text = "Aquí está lista de postres:\n"
    for index, row in postre.iterrows():
        postre_text += f"{row['Postres']}: {row['Descripción']} - {row['Precio']} soles\n"
    return postre_text

def display_bebida(bebida):
    """Mostrar el menú con descripciones."""
    bebida_text = "Aquí está lista de bebidas:\n"
    for index, row in bebida.iterrows():
        bebida_text += f"{row['bebida']}: {row['descripcion']} - {row['precio']} soles\n"
    return bebida_text
		
# Cargar el menú y distritos
menu = load("carta.csv")
distritos = load("distritos.csv")
bebidas= load("Bebidas.csv")
postres= load("Postres.csv")

def display_confirmed_order(order_details):
    """Genera una tabla en formato Markdown para el pedido confirmado."""
    table = "| **Plato** | **Cantidad** | **Precio Total** |\n"
    table += "|-----------|--------------|------------------|\n"
    for item in order_details:
        table += f"| {item['Plato']} | {item['Cantidad']} | S/{item['Precio Total']:.2f} |\n"
    table += "| **Total** |              | **S/ {:.2f}**      |\n".format(sum(item['Precio Total'] for item in order_details))
    return table

##Pendiente


def get_system_prompt(menu, distritos):
    """Definir el prompt del sistema para el bot de Sazón incluyendo el menú y distritos."""
    lima_tz = pytz.timezone('America/Lima') # Define la zona horaria de Lima
    hora_lima = datetime.now(lima_tz).strftime("%Y-%m-%d %H:%M:%S") # Obtiene la hora actual en Lima
    system_prompt = f"""
    Eres el bot de pedidos de Sazón. Ayudas a los clientes a hacer sus pedidos y siempre 
    eres bien amable. Aquí tienes el menú para que se lo muestres a los clientes:\n{display_menu(menu)}\n
    También repartimos en los siguientes distritos: {display_distritos(distritos)}.\n
    Primero, saluda al cliente y ofrécele el menú,recuerda que el cliente puede darte la cantidad de platos en forma de texto y en forma numérica. Asegurate que la cantidad se encuentre en un rango de 1 al 100. Si se pasa del rango hazle saber que no contamos con esa cantidad. 
    Luego, pregunta si quiere recoger su pedido en el local o si prefiere que lo enviemos a domicilio. 
    Asegúrate de usar solo español peruano en tus respuestas, evitando cualquier término como preferís debe ser prefiere. 
    Si el pedido es para entrega, asegúrate de que el distrito esté disponible y confirma con el cliente el distrito de entrega. 
    Si el pedido es para recoger, invitalo a acercarse a nuestro local ubicado en UPCH123.Verifica que el cliente haya ingresado el método de pedido antes de continuar. Después, resume 
    el pedido en la siguiente tabla:\n
    | **Plato** | **Cantidad** | **Precio Total** |\n
    |-----------|--------------|------------------|\n
    |           |              |                  |\n
    | **Total** |              | **S/ 0.00**      |\n
    El monto total del pedido no acepta descuentos ni rectificaciones del precio.
    
    Pregunta al cliente si desea agregar una bebida o postre a su pedido. Si responde bebida, muéstrale solo la carta de bebidas {display_bebida(bebidas)} y si responde postre muéstrale solo la carta de postres {display_postre(postres)}.
    
    Si el cliente agregó postres o bebidas, agrégalo a la tabla de resumen como si fuera un plato más.Olvídate de los subtotales y vuelve a calcular el monto total de forma precisa.El monto total del pedido no acepta descuentos ni rectificaciones del precio.
    Pregunta al cliente: "¿Estás de acuerdo con el pedido?" y espera su respuesta. 
    Una vez que confirme, pregunta: "¿Cuál es tu método de pago? ¿Deseas pagar con tarjeta de crédito, efectivo o algún otro método?".
    Una vez que el cliente confirme el pedido, registra la hora actual de Perú como el timestamp {hora_lima} de la confirmacion. 
    El pedido confirmado será:\n
    {display_confirmed_order([{'Plato': '', 'Cantidad': 0, 'Precio Total': 0}])}\n
    Recuerda verificar que el pedido sea correcto y el metodo de pago antes de registrarlo.
    """
    return system_prompt.replace("\n", " ")
   
def extract_order_json(response):
    """Extrae el pedido confirmado en formato JSON desde la respuesta del bot solo si todos los campos tienen valores completos."""
    prompt = f"Extrae la información del pedido confirmado de la siguiente respuesta: '{response}'. Si el pedido está confirmado, proporciona una salida en formato JSON con las siguientes claves: 'Platos' (contiene los platos, cada uno con su cantidad y precio_total), 'Total', 'metodo de pago', 'lugar_entrega', y 'timestamp_confirmacion'. Si algún campo como 'metodo de pago' o 'lugar_entrega' no está presente, asígnale el valor 'null'. Si el pedido no está confirmado, devuelve un diccionario vacío."
    #prompt = f"Extrae la información del pedido de la siguiente respuesta: '{response}'. Si el pedido está confirmado proporciona una salida en formato JSON con las claves: Platos(contine los platos con la cantidad y precio_total),Total,metodo de pago,lugar_entrega y timestamp_confirmacion. Si el pedido no está confirmado devuelve una diccionario vacio."

    extraction = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Eres un asistente que solo responde en JSON. Responde únicamente con un JSON o un diccionario vacio."},
            {"role": "user", "content": prompt}
        ],
        model="gpt-3.5-turbo",
        temperature=0,
        max_tokens=300,
        top_p=1,
        stop=None,
        stream=False,
    )
#"gemma2-9b-it"
    response_content = extraction.choices[0].message.content
    
    # Intenta cargar como JSON
    try:
        order_json = json.loads(response_content)
        st.markdown(order_json)
        st.markdown(type(order_json))
        # Verifica si el JSON es un diccionario
        if isinstance(order_json, dict):
            if all(order_json[key] not in (None, '', [], {}) for key in order_json):
                return order_json
            else:
                print("Advertencia: Hay claves con valores nulos o vacíos en el pedido.")
                return {}
            # Verifica que todas las claves en order_json tengan valores no nulos
            #return order_json if order_json else {}
        
        # Si el JSON es una lista, devuelves un diccionario vacío o manejas la lista de otro modo
        elif isinstance(order_json, list):
            print("Advertencia: Se recibió una lista en lugar de un diccionario.")
            return {}
        
        # Si no es ni lista ni diccionario, retorna un diccionario vacío
        else:
            return {}
    
    except json.JSONDecodeError:
        # Manejo de error en caso de que el JSON no sea válido
        return {}

def generate_response(prompt, temperature=0,max_tokens=1000):
    """Enviar el prompt a Groq y devolver la respuesta con un límite de tokens."""
    st.session_state["messages"].append({"role": "user", "content": prompt})

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state["messages"],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )
    response = completion.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": response})
    # Extraer JSON del pedido confirmado
    order_json = extract_order_json(response)
    st.markdown(order_json)
    st.markdown(type(order_json))
    logging.info(json.dumps(order_json, indent=4) if order_json else '{}')
    return response

# Ajustar el tono del bot
def adjust_tone(tone="friendly"):
    """Ajustar el tono del bot según las preferencias del cliente."""
    if tone == "formal":
        st.session_state["tone"] = "formal"
        return "Eres un asistente formal y educado."
    else:
        st.session_state["tone"] = "friendly"
        return "Eres un asistente amigable y relajado."

        
initial_state = [
    {"role": "system", "content": get_system_prompt(menu,distritos)},
    {
        "role": "assistant",
        "content": f"¿Qué te puedo ofrecer?\n\nEste es el menú del día:\n\n{format_menu(menu)}",
    },
]


if "messages" not in st.session_state:
    st.session_state["messages"] = deepcopy(initial_state)

# eliminar conversación
clear_button = st.button("Eliminar conversación", key="clear")
if clear_button:
    st.session_state["messages"] = deepcopy(initial_state)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    elif message["role"] == "assistant":
        with st.chat_message(message["role"], avatar="👨‍🍳"):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"], avatar="👤"):
            st.markdown(message["content"])

if prompt := st.chat_input():
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    output = generate_response(prompt)
    with st.chat_message("assistant", avatar="👨‍🍳"):
        st.markdown(output)
    



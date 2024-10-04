import pandas as pd
import streamlit as st
from datetime import datetime
from copy import deepcopy
from groq import Groq
import csv
import re

# Inicializar el cliente de Groq con la clave API
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Configuración inicial de la página
st.set_page_config(page_title="SazónBot", page_icon=":pot_of_food:")
st.title("🍲 SazónBot")

# Mensaje de bienvenida
intro = """¡Bienvenido a Sazón Bot, el lugar donde todos tus antojos de almuerzo se hacen realidad!
Comienza a chatear con Sazón Bot y descubre qué puedes pedir, cuánto cuesta y cómo realizar tu pago. ¡Estamos aquí para ayudarte a disfrutar del mejor almuerzo!"""
st.markdown(intro)


# Cargar el menú desde un archivo CSV
def load_menu(file_path):
    """Cargar el menú desde un archivo CSV con columnas Plato, Descripción y Precio."""
    menu = pd.read_csv(file_path)
    return menu

# Cargar los distritos de reparto desde un archivo CSV
def load_distritos(file_path):
    """Cargar los distritos de reparto desde un archivo CSV."""
    distritos = pd.read_csv(file_path)
    return distritos

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
        
        st.markdown(table)
    #formatted_menu = []
    #for idx, row in menu.iterrows():
     #   formatted_menu.append(
      #      f"**{row['Plato']}**\n\n{row['Descripción']}\n\n**Precio:** S/{row['Precio']}"
       # )
    #return "\n\n".join(formatted_menu)

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

# Cargar el menú y distritos
menu = load_menu("carta.csv")
distritos = load_distritos("distritos.csv")

def get_system_prompt(menu, distritos):
    """Definir el prompt del sistema para el bot de Sazón incluyendo el menú y distritos."""
    system_prompt = f"""
    Eres el bot de pedidos de Sazón. Ayudas a los clientes a hacer sus pedidos y siempre 
    eres amable. Aquí tienes el menú para mostrarles: {display_menu(menu)}. \
    También repartimos en los siguientes distritos: {display_distritos(distritos)}. \
    Primero saluda al cliente y ofrécele el menú. Después, toma el pedido y verifica 
    si es para recoger o para entrega a domicilio. Si es para entrega, asegúrate de que el distrito \
    esté disponible. Luego, resume el pedido, pregunta si quiere agregar algo más, \
    confirma el monto total y pregunta por el método de pago. Registra todos los pedidos con un \
    timestamp y su monto en soles. Si es necesario, ofrece información sobre los productos o distritos disponibles. \
    Recuerda verificar que el pedido sea correcto antes de registrarlo.
    """
    return system_prompt.replace("\n", " ")


def generate_response(prompt, temperature=0,max_tokens=150):
    """Enviar el prompt a Groq y devolver la respuesta con un límite de tokens."""
    st.session_state["messages"].append({"role": "user", "content": prompt})

    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=st.session_state["messages"],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )
    response = completion.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": response})
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
        "content": f"👨‍🍳¿Qué te puedo ofrecer?\n\nEste es el menú del día:\n\n{format_menu(menu)}",
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


import pandas as pd
import streamlit as st
from datetime import datetime
from copy import deepcopy
from groq import Groq
import csv
import re

# Inicializar el cliente de Groq con la clave API
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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
        distritos_text += f"{row['Distrito']}\n"
    return distritos_text

# Definir el prompt del sistema para el bot de Sazón
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

# Generar la respuesta usando el modelo de Groq con un límite de tokens
def generate_response(prompt, temperature=0, max_tokens=150):
    """Enviar el prompt a Groq y devolver la respuesta con un límite de tokens."""
    st.session_state["messages"].append({"role": "user", "content": prompt})

    response = client.completions.create(
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens  # Limitar el número de tokens en la respuesta
    )
    st.session_state["messages"].append({"role": "assistant", "content": response})
    return response

# Registrar el pedido con timestamp y monto
def register_order(order, total_price):
    """Registrar el pedido con timestamp y monto en un archivo."""
    with open("orders.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, order, total_price])

# Generar resumen del pedido en formato JSON
def generate_order_summary(order):
    """Generar resumen del pedido en formato JSON."""
    return {
        "order": order,
        "total_price": sum([item['price'] for item in order]),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Ajustar el tono del bot
def adjust_tone(tone="friendly"):
    """Ajustar el tono del bot según las preferencias del cliente."""
    if tone == "formal":
        st.session_state["tone"] = "formal"
        return "Eres un asistente formal y educado."
    else:
        st.session_state["tone"] = "friendly"
        return "Eres un asistente amigable y relajado."

# Iniciar el estado inicial del bot
def initialize_state(menu, distritos):
    """Iniciar el estado inicial con el prompt del sistema y el primer mensaje del bot."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": get_system_prompt(menu, distritos)},
            {
                "role": "assistant",
                "content": "👋 ¡Bienvenido a Sazón! ¿Qué te gustaría pedir hoy?",
            },
        ]
# Flujo principal de la aplicación
def main():
    # Cargar el menú y los distritos
    menu = load_menu("menu.csv")
    distritos = load_distritos("distritos.csv")
    
    # Iniciar el estado
    initialize_state(menu, distritos)
    
    # Mostrar el historial de mensajes
    for message in st.session_state["messages"]:
        if message["role"] == "assistant":
            st.markdown(f"**Sazón Bot:** {message['content']}")
        else:
            st.markdown(f"**Tú:** {message['content']}")

    # Recibir el mensaje del usuario
    user_input = st.text_input("Escribe tu pedido aquí:", "")
    
    # Si el usuario envía un mensaje, generar la respuesta
    if user_input:
        response = generate_response(user_input)
        st.markdown(f"**Sazón Bot:** {response}")

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
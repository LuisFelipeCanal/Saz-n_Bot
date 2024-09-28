import pandas as pd
import streamlit as st
from datetime import datetime
from copy import deepcopy
from openai import OpenAI

# Cargar el API key de OpenAI desde Streamlit Secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Configuración inicial de la página
st.set_page_config(page_title="SazónBot", page_icon=":pot_of_food:")
st.title("🍲 SazónBot")

# Mostrar mensaje de bienvenida
intro = """¡Bienvenido a Sazón Bot, el lugar donde todos tus antojos de almuerzo se hacen realidad!

Comienza a chatear con Sazón Bot y descubre qué puedes pedir, cuánto cuesta y cómo realizar tu pago. ¡Estamos aquí para ayudarte a disfrutar del mejor almuerzo!."""
st.markdown(intro)

# Función para cargar el menú desde un archivo CSV
def load_menu(csv_file):
    menu = pd.read_csv(csv_file)
    return menu

# Función para cargar los distritos de reparto desde otro CSV
def load_districts(csv_file):
    districts = pd.read_csv(csv_file)
    return districts['Distrito'].tolist()

# Función para mostrar el menú al usuario
def show_menu(menu):
    st.markdown("### Menú del día")
    for index, row in menu.iterrows():
        st.markdown(f"- **{row['Plato']}**: {row['Descripción']} - Precio: S/{row['Precio']}")

# Cargar menú y distritos (asegúrate de que los archivos CSV existen)
menu = load_menu("carta.csv")  # Archivo 'carta.csv' debe tener columnas: Plato, Descripción, Precio
districts = load_districts("distritos.csv")  # Archivo 'distritos.csv' debe tener una columna: Distrito

# Estado inicial del chatbot
initial_state = [
    {"role": "system", "content": "You are SazónBot. A friendly assistant helping customers with their lunch orders."},
    {
        "role": "assistant",
        "content": "👨‍🍳 ¿Qué te puedo ofrecer?\n\nEste es el menú del día:\n\n" + "\n".join([f"**{row['Plato']}** - S/{row['Precio']}" for index, row in menu.iterrows()])
    },
]

# Función para registrar los pedidos en un archivo
def save_order(order, total_price):
    with open("orders.csv", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp}, {order}, {total_price}\n")

# Función para clasificar el plato
def classify_order(prompt, menu):
    for word in prompt.split():
        if word in menu['Plato'].values:
            return word  # Retorna el nombre del plato encontrado
    return None

# Función para manejar el pedido del usuario
def handle_order(prompt, menu):
    # Clasificar el pedido
    order = classify_order(prompt, menu)

    # Validar si se seleccionó un plato
    if not order:
        return "😊 No has seleccionado ningún plato del menú. Por favor revisa."

    # Responder con el resumen del pedido y mostrar los distritos
    district_list = ", ".join(districts)
    return f"Tu pedido ha sido registrado: {order}. Por favor selecciona un distrito de entrega: {district_list}"

# Función para verificar el distrito
def verify_district(prompt, districts):
    for district in districts:
        if district in prompt:
            return district  # Retorna el distrito encontrado
    return None

# Inicializar la conversación si no existe en la sesión
if "messages" not in st.session_state:
    st.session_state["messages"] = deepcopy(initial_state)

# Botón para limpiar la conversación
clear_button = st.button("Limpiar Conversación", key="clear")
if clear_button:
    st.session_state["messages"] = deepcopy(initial_state)

# Mostrar el historial de la conversación
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    elif message["role"] == "assistant":
        with st.chat_message(message["role"], avatar="🍲"):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"], avatar="👤"):
            st.markdown(message["content"])

# Entrada del usuario para el pedido
if prompt := st.chat_input("¿Qué te gustaría pedir?"):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Procesar el pedido y generar la respuesta
    response = handle_order(prompt, menu)

    with st.chat_message("assistant", avatar="🍲"):
        st.markdown(response)

# Entrada del usuario para el distrito
if prompt := st.chat_input("¿Cuál es tu distrito y dirección?"):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Verificar el distrito y responder
    district = verify_district(prompt, districts)
    
    if district:
        response = f"Gracias por proporcionar tu distrito: {district}. Procederemos a entregar tu pedido allí."
    else:
        response = f"Lo siento, pero no entregamos en ese distrito. Estos son los distritos disponibles: {', '.join(districts)}"

    with st.chat_message("assistant", avatar="🍲"):
        st.markdown(response)






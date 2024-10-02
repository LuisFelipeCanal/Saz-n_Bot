import pandas as pd
import streamlit as st
from datetime import datetime
from copy import deepcopy
from openai import OpenAI
import openai

# Cargar el API key de OpenAI desde Streamlit Secrets
client=OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

# Configuración inicial de la página
st.set_page_config(page_title="SazónBot", page_icon=":pot_of_food:")
st.title("🍲 SazónBot")

# Mostrar mensaje de bienvenida
intro = """¡Bienvenido a Sazón Bot, el lugar donde todos tus antojos de almuerzo se hacen realidad!
Comienza a chatear con Sazón Bot y descubre qué puedes pedir, cuánto cuesta y cómo realizar tu pago. ¡Estamos aquí para ayudarte a disfrutar del mejor almuerzo!"""
st.markdown(intro)

# Función para cargar el menú desde un archivo CSV
def load_menu(csv_file):
    menu = pd.read_csv(csv_file)
    return menu

# Función para cargar los distritos de reparto desde otro CSV
def load_districts(csv_file):
    districts = pd.read_csv(csv_file)
    return districts['Distrito'].tolist()

# Función para mostrar el menú en un formato más amigable
def format_menu(menu):
    if menu.empty:
        return "No hay platos disponibles."
    
    formatted_menu = []
    for idx, row in menu.iterrows():
        formatted_menu.append(
            f"**{row['Plato']}**\n{row['Descripción']}\n**Precio:** S/{row['Precio']}"
        )
    return "\n\n".join(formatted_menu)

# Cargar menú y distritos (asegúrate de que los archivos CSV existen)
menu = load_menu("carta.csv")  # Archivo 'menu.csv' debe tener columnas: Plato, Descripción, Precio
districts = load_districts("distritos.csv")  # Archivo 'distritos.csv' debe tener una columna: Distrito

# Estado inicial del chatbot
initial_state = [
    {"role": "system", "content": "You are SazónBot. A friendly assistant helping customers with their lunch orders."},
    {
        "role": "assistant",
        "content": f"👨‍🍳¿Qué te puedo ofrecer?\n\nEste es el menú del día:\n\n{format_menu(menu)}",
    },
]

# Función para registrar los pedidos en un archivo
def save_order(order, total_price):
    with open("orders.csv", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp}, {order}, {total_price}\n")

# Función para validar si los platos pedidos existen en el menú
def validate_order(prompt, menu):
    order_details = {}
    total_price = 0
    for item in prompt.split(" y "):  # Dividir la entrada por "y" para varios platos
        item_parts = item.strip().split(" ")
        try:
            quantity = int(item_parts[0])
            dish_name = " ".join(item_parts[1:]).strip().lower()
            menu_names = menu['Plato'].str.lower().values
            if dish_name in menu_names:
                price = menu.loc[menu['Plato'].str.lower() == dish_name, 'Precio'].values[0]
                order_details[dish_name] = quantity
                total_price += price * quantity
            else:
                return None, None  # Si el plato no existe, devolver None
        except (ValueError, IndexError):
            return None, None

    return order_details, total_price

# Función para verificar si el distrito es válido
def is_valid_district(district, districts):
    return district.lower() in [d.lower() for d in districts]

# Inicializar la conversación si no existe en la sesión
if "messages" not in st.session_state:
    st.session_state["messages"] = deepcopy(initial_state)
    st.session_state["order"] = None
    st.session_state["total_price"] = 0

# Botón para limpiar la conversación
clear_button = st.button("Limpiar Conversación", key="clear")
if clear_button:
    st.session_state["messages"] = deepcopy(initial_state)
    st.session_state["order"] = None
    st.session_state["total_price"] = 0

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

    # Llamar a GPT-3.5-turbo para analizar el mensaje del usuario
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for a food ordering service."},
            {"role": "user", "content": prompt},
        ]
    )

    parsed_message = response.choices[0].message['content']

    # Validar el pedido del usuario
    order_details, total_price = validate_order(parsed_message, menu)

    if order_details:
        # Guardar el pedido en el estado
        st.session_state["order"] = order_details
        st.session_state["total_price"] = total_price

        # Mostrar resumen del pedido
        order_summary = "\n".join([f"{qty} {dish}" for dish, qty in order_details.items()])
        response_text = f"Tu pedido ha sido registrado:\n\n{order_summary}.\n\n¿Es correcto? (Sí o No)"
    else:
        # Si el plato no existe, mostrar el menú de nuevo
        response_text = f"Uno o más platos no están disponibles. Aquí está el menú otra vez:\n\n{format_menu(menu)}"

    # Mostrar la respuesta del asistente
    with st.chat_message("assistant", avatar="🍲"):
        st.markdown(response_text)

# Si hay un pedido registrado, preguntar por el distrito
if st.session_state["order"]:
    if district_input := st.chat_input("Por favor selecciona un distrito de entrega:"):
        with st.chat_message("user", avatar="👤"):
            st.markdown(district_input)

        # Verificar si el distrito es válido
        if is_valid_district(district_input, districts):
            response_text = f"Gracias por proporcionar tu distrito: {district_input}. Procederemos a entregar tu pedido allí. ¡Que disfrutes de tu almuerzo!"
        else:
            response_text = f"Lo siento, no entregamos en ese distrito. Estos son los distritos disponibles: {', '.join(districts)}"

        # Mostrar la respuesta del asistente
        with st.chat_message("assistant", avatar="🍲"):
            st.markdown(response_text)

        # Si el distrito es válido, guardar el pedido en el archivo
        if is_valid_district(district_input, districts):
            save_order(st.session_state["order"], st.session_state["total_price"])
            st.session_state["order"] = None
            st.session_state["total_price"] = 0









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
menu = load_menu("carta.csv")  # Archivo 'menu.csv' debe tener columnas: Plato, Descripción, Precio
districts = load_districts("distritos.csv")  # Archivo 'distritos.csv' debe tener una columna: Distrito



# Estado inicial del chatbot
menu = load_menu("carta.csv")  # Asegúrate de que el menú esté cargado aquí
initial_state = [
    {"role": "system", "content": "You are SazónBot. A friendly assistant helping customers with their lunch orders."},
    {
        "role": "assistant",
        "content": f"👨‍🍳¿Qué te puedo ofrecer?",
    },
]

show_menu(menu)

# Función para registrar los pedidos en un archivo
def save_order(order, total_price):
    with open("orders.csv", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp}, {order}, {total_price}\n")

# Función para verificar si un pedido es válido
def is_valid_order(order, menu):
    for item in order:
        if item not in menu['Plato'].values:
            return False
    return True

# Función para verificar si el distrito es válido
def is_valid_district(district, districts):
    return district in districts

# Función para manejar el pedido del usuario
def handle_order(prompt, menu, districts):
    # Extraer platos y distritos del mensaje del usuario
    order = [word for word in prompt.split() if word in menu['Plato'].values]
    district = next((word for word in prompt.split() if word in districts), None)

    # Validar si los platos están en el menú
    if not is_valid_order(order, menu):
        return "Algunos de los platos que has seleccionado no están en el menú. Por favor revisa."

    # Validar si el distrito es válido
    if not district:
        return f"Lo siento, pero no entregamos en ese distrito. Estos son los distritos disponibles: {', '.join(districts)}"

    # Calcular el precio total
    total_price = sum(menu[menu['Plato'].isin(order)]['Precio'])

    # Guardar el pedido
    save_order(order, total_price)

    # Responder con el resumen del pedido
    return f"Tu pedido ha sido registrado: {order}. El monto total es S/{total_price}. Gracias por tu compra."

# Función para controlar el tono de la respuesta
def adjust_tone(response, tone="amigable"):
    if tone == "amigable":
        return f"😊 {response}"
    elif tone == "formal":
        return f"Estimado cliente, {response}"
    else:
        return response

# Función para generar la respuesta del chatbot
def generate_response(prompt, temperature=0):
    """Enviar prompt a OpenAI y devolver la respuesta. Añadir el prompt y la respuesta a la conversación."""
    st.session_state["messages"].append({"role": "user", "content": prompt})

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state["messages"],
        temperature=temperature,
    )
    response = completion.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": response})
    return response



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

# Entrada del usuario
if prompt := st.chat_input("¿Qué te gustaría pedir?"):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Procesar el pedido y generar la respuesta
    response = handle_order(prompt, menu, districts)

    # Ajustar el tono de la respuesta
    response = adjust_tone(response, tone="amigable")

    with st.chat_message("assistant", avatar="🍲"):
        st.markdown(response)

    with st.chat_message("assistant", avatar="🍲"):
        st.markdown(output)



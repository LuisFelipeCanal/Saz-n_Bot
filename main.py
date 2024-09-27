import pandas as pd
import streamlit as st
from datetime import datetime

# Cargar el archivo CSV del menú
def load_menu(csv_file):
    try:
        menu = pd.read_csv(csv_file)
        return menu
    except Exception as e:
        st.error(f"Error al cargar el menú: {e}")
        return pd.DataFrame()

# Cargar distritos de reparto desde CSV
def load_districts(csv_file):
    try:
        districts = pd.read_csv(csv_file)
        return districts
    except Exception as e:
        st.error(f"Error al cargar los distritos: {e}")
        return pd.DataFrame()

# Función para mostrar el menú en un formato más amigable
def format_menu(menu):
    return "\n".join([f"{row['Plato']}: {row['Descripción']} - Precio: S/{row['Precio']}" for idx, row in menu.iterrows()])

# Función para generar la respuesta
def generate_response(prompt):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    if any(menu["Plato"].str.contains(prompt, case=False)):
        st.session_state["order"] = prompt
        st.session_state["price"] = menu.loc[menu["Plato"].str.contains(prompt, case=False), "Precio"].values[0]
        response = "Perfecto, ahora elige un distrito de reparto entre los siguientes:\n" + "\n".join(st.session_state["districts"])
    elif any(d in prompt for d in st.session_state["districts"]):
        st.session_state["district"] = prompt
        response = f"Pedido registrado: {st.session_state['order']} para {st.session_state['district']}. El monto es S/{st.session_state['price']}. Gracias por tu pedido."
        save_order(st.session_state["order"], st.session_state["district"], st.session_state["price"])
    else:
        response = "No entendí tu pedido. Por favor, elige un plato del menú."

    st.session_state["messages"].append({"role": "assistant", "content": response})
    return response

# Guardar el pedido en un archivo CSV
def save_order(order, district, price):
    with open("orders.csv", "a") as f:
        f.write(f"{datetime.now()},{order},{district},{price}\n")

# Configuración inicial de la app
st.set_page_config(page_title="SazónBot", page_icon=":pot_of_food:")
st.title("🍲 SazónBot")

# Cargar el menú y los distritos desde CSV
menu = load_menu("carta.csv")
districts = load_districts("distritos.csv")

# Almacenar distritos en el estado de la sesión
if "districts" not in st.session_state:
    if not districts.empty:
        st.session_state["districts"] = districts["Distrito"].tolist()
    else:
        st.session_state["districts"] = []

# Mostrar el mensaje de bienvenida
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "👨‍🍳¿Qué te puedo ofrecer?"}
    ]

# Botón para limpiar la conversación
clear_button = st.button("Limpiar conversación", key="clear")
if clear_button:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "👨‍🍳¿Qué te puedo ofrecer?"}
    ]
    if "order" in st.session_state:
        del st.session_state["order"]
    if "district" in st.session_state:
        del st.session_state["district"]

# Mostrar mensajes del bot y del usuario
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message(message["role"], avatar="🍲"):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"], avatar="👤"):
            st.markdown(message["content"])

# Entrada de chat del usuario
if prompt := st.chat_input("¿Qué te gustaría pedir?"):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    if "order" not in st.session_state:
        # Mostrar el menú al usuario
        menu_formatted = format_menu(menu)
        output = generate_response(f"Este es el menú del día:\n{menu_formatted}\n¿Qué deseas pedir?")
    else:
        output = generate_response(prompt)

    with st.chat_message("assistant", avatar="🍲"):
        st.markdown(output)



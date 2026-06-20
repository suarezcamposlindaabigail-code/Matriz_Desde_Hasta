"""
app.py
======
App de Streamlit para visualizar el cálculo de la matriz Desde-Hasta
(Parte 1 del Caso: Caminos más Cortos).

Ejecutar localmente:
    streamlit run app.py

Desplegar en Streamlit Community Cloud:
    1. Subir este repositorio a GitHub (incluyendo app.py, shortest_paths.py,
       requirements.txt y la carpeta data/ con Red1.nf y Clientes1.txt).
    2. Ir a https://share.streamlit.io , conectar el repositorio de GitHub
       y seleccionar app.py como archivo principal.
"""

import io
import pandas as pd
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

from shortest_paths import (
    leer_red,
    leer_clientes,
    construir_matriz_desde_hasta,
    exportar_csv,
)

st.set_page_config(page_title="Caso Redes - Matriz Desde-Hasta", layout="wide")

st.title("Caso Redes: Camino más Corto y TSP")
st.subheader("Parte 1 - Construcción de la matriz Desde-Hasta")

st.markdown(
    """
Esta aplicación calcula la matriz de distancias **Desde-Hasta** entre el
depósito (nodo 0) y los puntos de entrega, resolviendo el problema de
**camino más corto** sobre la red vial completa (algoritmo de Dijkstra,
equivalente a resolver la formulación LP de flujo de costo mínimo descrita
en `shortest_paths.py`).
"""
)

# ---------------------------------------------------------------------------
# Carga de archivos
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Datos de entrada")
    usar_default = st.checkbox("Usar archivos de ejemplo (data/)", value=True)

    if usar_default:
        path_red = "data/Red1.nf"
        path_clientes = "data/Clientes1.txt"
    else:
        archivo_red = st.file_uploader("Archivo de red (.nf)", type=["nf", "txt"])
        archivo_clientes = st.file_uploader("Archivo de clientes (.txt)", type=["txt"])
        if archivo_red and archivo_clientes:
            path_red = "tmp_red.nf"
            path_clientes = "tmp_clientes.txt"
            with open(path_red, "wb") as f:
                f.write(archivo_red.getbuffer())
            with open(path_clientes, "wb") as f:
                f.write(archivo_clientes.getbuffer())
        else:
            st.warning("Suba ambos archivos para continuar.")
            st.stop()

    deposito = st.number_input("Nodo del depósito", value=0, step=1)
    calcular = st.button("Calcular matriz", type="primary")

# ---------------------------------------------------------------------------
# Cálculo (con caché para no recalcular cada vez)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=True)
def calcular_resultado(path_red, path_clientes, deposito):
    return construir_matriz_desde_hasta(path_red, path_clientes, deposito)


@st.cache_data
def cargar_grafo(path_red):
    return leer_red(path_red)


if "resultado" not in st.session_state:
    st.session_state.resultado = None

if calcular or usar_default:
    with st.spinner("Resolviendo caminos más cortos (Dijkstra) desde cada nodo de interés..."):
        st.session_state.resultado = calcular_resultado(path_red, path_clientes, deposito)

resultado = st.session_state.resultado

if resultado is None:
    st.info("Presione 'Calcular matriz' para iniciar.")
    st.stop()

nodos = resultado.nodos_interes
st.success(f"Matriz calculada: {len(nodos)} nodos de interés (depósito + {len(nodos)-1} clientes).")

# ---------------------------------------------------------------------------
# Tabs de visualización
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Matriz Desde-Hasta", "🛣️ Ruta entre dos nodos", "ℹ️ Formulación"])

with tab1:
    df = pd.DataFrame(
        {j: [resultado.matriz[i][j] for i in nodos] for j in nodos}, index=nodos
    )
    st.dataframe(df, use_container_width=True)

    csv_buffer = io.StringIO()
    exportar_csv(resultado, "tmp_matriz.csv")
    with open("tmp_matriz.csv", "r") as f:
        csv_data = f.read()
    st.download_button(
        "⬇️ Descargar matriz (CSV)",
        data=csv_data,
        file_name="matriz_desde_hasta.csv",
        mime="text/csv",
    )

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        origen = st.selectbox("Nodo origen", nodos, index=0)
    with col2:
        destino = st.selectbox("Nodo destino", nodos, index=1)

    if origen != destino:
        distancia = resultado.distancia(origen, destino)
        ruta = resultado.ruta(origen, destino)
        st.metric("Distancia mínima", f"{distancia}")
        st.write("**Secuencia de nodos en la red (camino más corto):**")
        st.code(" → ".join(str(n) for n in ruta))

        # Visualización del subgrafo de la ruta
        G = nx.DiGraph()
        for k in range(len(ruta) - 1):
            G.add_edge(ruta[k], ruta[k + 1])

        fig, ax = plt.subplots(figsize=(8, 4))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(
            G, pos, with_labels=True, node_color="#FFA500", node_size=600,
            font_size=8, arrowsize=15, ax=ax
        )
        ax.set_title(f"Camino más corto: {origen} → {destino}")
        st.pyplot(fig)
    else:
        st.warning("Seleccione dos nodos distintos.")

with tab3:
    st.markdown(
        r"""
### Formulación del Problema de Camino más Corto

Dado un grafo dirigido $G=(V,A)$, un nodo origen $s$ y costos $d_{ij} \geq 0$
en cada arco $(i,j) \in A$:

**Variables:** $x_{ij} \geq 0$ para cada arco $(i,j) \in A$

**Función objetivo:**
$$\min \sum_{(i,j) \in A} d_{ij}\, x_{ij}$$

**Restricciones (balance de flujo):**
$$\sum_{j:(s,j)\in A} x_{sj} - \sum_{j:(j,s)\in A} x_{js} = |V|-1 \qquad \text{(nodo origen } s \text{)}$$
$$\sum_{j:(k,j)\in A} x_{kj} - \sum_{j:(j,k)\in A} x_{jk} = -1 \qquad \forall k \neq s$$
$$x_{ij} \geq 0$$

Como la matriz de incidencia nodo-arco es totalmente unimodular y los costos
son no negativos, el óptimo de esta LP es siempre entero y coincide con el
resultado del **algoritmo de Dijkstra**, que es el método implementado en
`shortest_paths.py` por eficiencia computacional (se resuelve 90 veces, una
por cada nodo de interés, sobre una red de 1000 nodos / 19,794 arcos).
"""
    )

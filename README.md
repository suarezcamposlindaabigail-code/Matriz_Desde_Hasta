# Caso Redes - Matriz Desde-Hasta (Parte 1: Camino más Corto)

Proyecto para resolver la **Parte 1** del Caso Redes: construir la matriz de
distancias Desde-Hasta entre el depósito y los puntos de entrega, mediante
el cálculo del camino más corto sobre la red vial.

## Estructura del repositorio

```
.
├── app.py                 # App de Streamlit (visualización interactiva)
├── shortest_paths.py       # Lógica: lectura de datos, formulación y Dijkstra
├── requirements.txt        # Dependencias
├── data/
│   ├── Red1.nf              # Archivo de red vial (NodoOrigen NodoDestino Distancia)
│   └── Clientes1.txt        # Archivo de puntos de entrega
└── README.md
```

## Formulación utilizada

El cálculo de cada fila de la matriz Desde-Hasta corresponde a resolver el
problema de **camino más corto** (caso particular del problema de flujo de
costo mínimo) desde un nodo origen $s$ hacia todos los demás nodos de la red:

$$\min \sum_{(i,j)\in A} d_{ij}\,x_{ij}$$
sujeto a balance de flujo en cada nodo (ver detalle y demostración de
equivalencia con Dijkstra en `shortest_paths.py` y en la pestaña
"Formulación" de la app).

Por la estructura de la red (1000 nodos, 19,794 arcos, 90 nodos de interés:
depósito + 89 clientes) se resuelve esta LP mediante el **algoritmo de
Dijkstra**, que es exacto para costos no negativos y mucho más eficiente
que invocar un solver LP genérico 90 veces.

## Ejecutar localmente

```bash
pip install -r requirements.txt

# Opción 1: por línea de comandos (genera CSV y .dat de AMPL)
python shortest_paths.py --red data/Red1.nf --clientes data/Clientes1.txt \
       --out_csv matriz_desde_hasta.csv --out_dat distancias.dat

# Opción 2: interfaz interactiva
streamlit run app.py
```

## Desplegar en GitHub + Streamlit Community Cloud

1. Crear un repositorio en GitHub y subir todos los archivos de esta carpeta
   (incluyendo `data/Red1.nf` y `data/Clientes1.txt`):
   ```bash
   git init
   git add .
   git commit -m "Caso Redes: matriz Desde-Hasta"
   git branch -M main
   git remote add origin https://github.com/<usuario>/<repositorio>.git
   git push -u origin main
   ```
2. Ir a [https://share.streamlit.io](https://share.streamlit.io) e iniciar
   sesión con la cuenta de GitHub.
3. Crear una nueva app, seleccionar el repositorio, la rama `main` y el
   archivo principal `app.py`.
4. Streamlit Cloud instalará automáticamente las dependencias de
   `requirements.txt` y publicará la app con una URL pública.

## Salidas generadas

- `matriz_desde_hasta.csv`: matriz 90×90 con las distancias mínimas entre
  el depósito y cada cliente (y entre clientes), usada como parámetro
  $d_{ij}$ del modelo TSP (Parte 2 y 3 del caso).
- `distancias.dat`: mismo contenido en formato AMPL (`set` y `param`), listo
  para incluir en el modelo `.mod` del TSP.

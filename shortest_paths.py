"""
shortest_paths.py
==================

Resuelve el Problema de Camino más Corto (Parte 1 del Caso) para construir
la matriz de distancias Desde-Hasta entre el depósito y los puntos de entrega.

Formulación matemática (Problema de Flujo de Costo Mínimo / Camino más Corto)
-------------------------------------------------------------------------------
Dado un grafo dirigido G = (V, A), un nodo origen s y costos d_ij >= 0 en
cada arco (i, j) in A, el problema de "árbol de caminos más cortos desde s
hacia todos los demás nodos" se formula como:

    Variables:
        x_ij >= 0                          para cada arco (i, j) in A
        (x_ij representa si se usa el arco (i,j) en el camino hacia el nodo j)

    Función objetivo:
        min  sum_{(i,j) in A} d_ij * x_ij

    Restricciones (balance de flujo / conservación):
        sum_{j:(s,j) in A} x_sj  -  sum_{j:(j,s) in A} x_js  =  |V| - 1     (nodo origen)
        sum_{j:(k,j) in A} x_kj  -  sum_{j:(j,k) in A} x_jk  =  -1   para todo k != s  (resto de nodos)
        x_ij >= 0

Como la matriz de incidencia nodo-arco de una red es totalmente unimodular y
los costos d_ij son no negativos, el óptimo de esta relajación LP es siempre
entero (x_ij in {0,1}), y coincide exactamente con el camino más corto
encontrado por el algoritmo de Dijkstra. Por eficiencia computacional
(la red tiene 1000 nodos y 19,794 arcos, y se debe resolver el problema desde
90 orígenes distintos = depósito + 89 clientes), en este código se resuelve
el LP anterior usando el algoritmo de Dijkstra, que es el método combinatorio
exacto y eficiente para resolver dicho problema de flujo cuando todos los
costos son no negativos (equivale a resolver el dual de la formulación de
flujos por programación dinámica/greedy en lugar de un solver LP genérico).

Este módulo:
    1. Lee el archivo de red  (NodoOrigen NodoDestino Distancia [flag])
    2. Lee el archivo de clientes (un nodo por línea)
    3. Calcula, para cada nodo de interés (depósito 0 + clientes), el árbol
       de caminos más cortos hacia todos los demás nodos de la red (Dijkstra)
    4. Construye la matriz Desde-Hasta (sólo entre depósito + clientes)
    5. Permite reconstruir la ruta (secuencia de nodos intermedios) entre
       dos nodos cualesquiera de interés.
"""

from __future__ import annotations
import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Lectura de datos
# ---------------------------------------------------------------------------
def leer_red(path_red: str) -> Tuple[int, Dict[int, List[Tuple[int, int]]]]:
    """
    Lee el archivo de red vial.

    Formato esperado (igual al usado en el curso):
        Línea 1:  n_nodos  n_arcos
        Líneas siguientes: NodoOrigen  NodoDestino  Distancia  [flag opcional]

    Retorna:
        n_nodos: cantidad total de nodos en la red
        grafo:   diccionario {nodo: [(nodo_destino, distancia), ...]}
    """
    with open(path_red, "r", encoding="utf-8") as f:
        lineas = [l.strip() for l in f if l.strip()]

    n_nodos, n_arcos = map(int, lineas[0].split())
    grafo: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(n_nodos)}

    for linea in lineas[1:]:
        partes = linea.split()
        origen, destino, dist = int(partes[0]), int(partes[1]), int(partes[2])
        grafo[origen].append((destino, dist))

    return n_nodos, grafo


def leer_clientes(path_clientes: str) -> List[int]:
    """Lee el archivo de puntos de entrega (un nodo por línea)."""
    with open(path_clientes, "r", encoding="utf-8") as f:
        return [int(l.strip()) for l in f if l.strip()]


# ---------------------------------------------------------------------------
# Algoritmo de Dijkstra (resuelve la LP de camino más corto descrita arriba)
# ---------------------------------------------------------------------------
def dijkstra(origen: int, grafo: Dict[int, List[Tuple[int, int]]], n_nodos: int
             ) -> Tuple[List[float], List[int]]:
    """
    Calcula el árbol de caminos más cortos desde 'origen' hacia todos los
    nodos de la red.

    Retorna:
        dist: lista de distancias mínimas (dist[i] = distancia de origen a i)
        pred: lista de predecesores en el camino más corto (para reconstruir
              la ruta), pred[i] = nodo anterior a i en el camino óptimo.
    """
    dist = [float("inf")] * n_nodos
    pred = [-1] * n_nodos
    dist[origen] = 0
    visitado = [False] * n_nodos
    cola = [(0, origen)]

    while cola:
        d_actual, u = heapq.heappop(cola)
        if visitado[u]:
            continue
        visitado[u] = True
        for v, peso in grafo[u]:
            nd = d_actual + peso
            if nd < dist[v]:
                dist[v] = nd
                pred[v] = u
                heapq.heappush(cola, (nd, v))

    return dist, pred


def reconstruir_ruta(pred: List[int], origen: int, destino: int) -> List[int]:
    """Reconstruye la secuencia de nodos del camino más corto origen -> destino."""
    if destino == origen:
        return [origen]
    ruta = [destino]
    actual = destino
    while actual != origen:
        actual = pred[actual]
        if actual == -1:
            return []  # no hay camino
        ruta.append(actual)
    ruta.reverse()
    return ruta


# ---------------------------------------------------------------------------
# Construcción de la matriz Desde-Hasta
# ---------------------------------------------------------------------------
@dataclass
class ResultadoCaminosMasCortos:
    nodos_interes: List[int]                       # depósito + clientes
    matriz: Dict[int, Dict[int, float]] = field(default_factory=dict)
    predecesores: Dict[int, List[int]] = field(default_factory=dict)  # pred[origen] -> lista pred por nodo de red

    def distancia(self, i: int, j: int) -> float:
        return self.matriz[i][j]

    def ruta(self, i: int, j: int) -> List[int]:
        return reconstruir_ruta(self.predecesores[i], i, j)


def construir_matriz_desde_hasta(
    path_red: str,
    path_clientes: str,
    deposito: int = 0,
) -> ResultadoCaminosMasCortos:
    """
    Calcula la matriz Desde-Hasta (camino más corto) entre el depósito y
    todos los puntos de entrega, recorriendo la red vial completa.
    """
    n_nodos, grafo = leer_red(path_red)
    clientes = leer_clientes(path_clientes)
    nodos_interes = [deposito] + [c for c in clientes if c != deposito]

    resultado = ResultadoCaminosMasCortos(nodos_interes=nodos_interes)

    for origen in nodos_interes:
        dist, pred = dijkstra(origen, grafo, n_nodos)
        resultado.matriz[origen] = {j: dist[j] for j in nodos_interes}
        resultado.predecesores[origen] = pred

    return resultado


def exportar_csv(resultado: ResultadoCaminosMasCortos, path_salida: str) -> None:
    """Exporta la matriz Desde-Hasta a un archivo CSV."""
    nodos = resultado.nodos_interes
    with open(path_salida, "w", encoding="utf-8") as f:
        f.write("Desde\\Hasta," + ",".join(str(j) for j in nodos) + "\n")
        for i in nodos:
            fila = ",".join(str(resultado.matriz[i][j]) for j in nodos)
            f.write(f"{i},{fila}\n")


def exportar_ampl_dat(resultado: ResultadoCaminosMasCortos, path_salida: str) -> None:
    """
    Exporta la matriz Desde-Hasta en formato .dat de AMPL, lista para
    usarse como parámetro 'd' en el modelo TSP (Parte 2 y 3 del caso).
    """
    nodos = resultado.nodos_interes
    with open(path_salida, "w", encoding="utf-8") as f:
        f.write(f"set NODOS := {' '.join(str(n) for n in nodos)};\n\n")
        f.write("param d :\n")
        f.write("        " + " ".join(str(j) for j in nodos) + " :=\n")
        for i in nodos:
            fila = " ".join(str(resultado.matriz[i][j]) for j in nodos)
            f.write(f"  {i}  {fila}\n")
        f.write(";\n")


# ---------------------------------------------------------------------------
# Ejecución directa (modo script)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Construye la matriz Desde-Hasta a partir de la red vial y los clientes."
    )
    parser.add_argument("--red", default="data/Red1.nf", help="Ruta al archivo de red")
    parser.add_argument("--clientes", default="data/Clientes1.txt", help="Ruta al archivo de clientes")
    parser.add_argument("--deposito", type=int, default=0, help="Nodo del depósito")
    parser.add_argument("--out_csv", default="matriz_desde_hasta.csv", help="Archivo CSV de salida")
    parser.add_argument("--out_dat", default="distancias.dat", help="Archivo .dat de AMPL de salida")
    args = parser.parse_args()

    print("Leyendo red y clientes...")
    resultado = construir_matriz_desde_hasta(args.red, args.clientes, args.deposito)
    print(f"Nodos de interés (depósito + clientes): {len(resultado.nodos_interes)}")

    exportar_csv(resultado, args.out_csv)
    print(f"Matriz CSV exportada a: {args.out_csv}")

    exportar_ampl_dat(resultado, args.out_dat)
    print(f"Archivo .dat (AMPL) exportado a: {args.out_dat}")

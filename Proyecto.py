import math
import time
import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN

class Taxi:
    # Inicializa un objeto Taxi con atributos básicos
    def __init__(self, id, ubicacion, punto_partida):
        self.id = id
        self.ubicacion = ubicacion
        self.destino = None
        self.ocupado = False
        self.ruta = []
        self.posicion_actual = None
        self.paso_actual = 0
        self.velocidad = 1  # Pixeles por paso de actualización
        self.en_movimiento = False # Atributo para controlar si el taxi está en movimiento
        self.pasajero = None
        self.punto_partida = punto_partida
        self.ultimo_movimiento = time.time()  # Timestamp del último movimiento

    # Asigna un destino al taxi y actualiza su estado de movimiento
    def asignar_destino(self, destino, recoger_pasajero=False):
        self.destino = destino
        self.en_movimiento = True if self.destino else False  # Reinicia el movimiento cuando se asigna un nuevo destino
        self.ocupado = recoger_pasajero

    # Calcula la ruta más corta hasta el destino usando el algoritmo de Dijkstra
    def calcular_ruta(self, grafo):
        if self.destino:
            self.ruta, _ = grafo.dijkstra(self.ubicacion, self.destino)
            self.posicion_actual = 0
            self.paso_actual = 0

    # Mueve el taxi a lo largo de la ruta calculada
    def mover(self, ubicaciones, grafo):
        if self.ruta and self.posicion_actual is not None and self.en_movimiento:
            nodo_actual = self.ruta[self.posicion_actual]
            x1, y1 = ubicaciones[nodo_actual]

            if self.posicion_actual + 1 < len(self.ruta):
                nodo_siguiente = self.ruta[self.posicion_actual + 1]
                x2, y2 = ubicaciones[nodo_siguiente]

                dx = x2 - x1
                dy = y2 - y1
                distancia = math.sqrt(dx**2 + dy**2)

                if distancia > 0:
                    paso_x = self.velocidad * (dx / distancia)
                    paso_y = self.velocidad * (dy / distancia)

                    self.paso_actual += self.velocidad

                    if self.paso_actual >= distancia:
                        self.ubicacion = nodo_siguiente
                        self.posicion_actual += 1
                        self.paso_actual = 0
                        if self.ubicacion == self.destino:
                            self.en_movimiento = False  # Detiene el movimiento al llegar al nodo
                            if self.ocupado:  # Recogiendo pasajero
                                self.asignar_destino(self.pasajero.ubicacion_destino)
                                self.calcular_ruta(grafo)
                                self.ocupado = False
                                time.sleep(1)  # Pausa de 1 segundo al recoger pasajero
                            else: # Dejando pasajero
                                self.pasajero = None
                                self.asignar_destino(self.punto_partida)
                                self.calcular_ruta(grafo)
                                time.sleep(1)  # Pausa de 1 segundo al dejar pasajero
                        return (x2, y2), (x2, y2)
                    else:
                        pos_x = x1 + paso_x * self.paso_actual
                        pos_y = y1 + paso_y * self.paso_actual
                        return (x1, y1), (pos_x, pos_y)
            else:
                self.ubicacion = self.destino
                self.ruta = []
                self.posicion_actual = None
                self.destino = None
                self.en_movimiento = False  # Detiene el movimiento al llegar al destino
                return (x1, y1), (x1, y1)
        return None, None

# Calcula la distancia euclidiana entre dos ubicaciones
def distancia_euclidea(ubicacion1, ubicacion2):
    return math.sqrt((ubicacion1[0] - ubicacion2[0]) ** 2 + (ubicacion1[1] - ubicacion2[1]) ** 2)


class Pasajero:
    # Inicializa un objeto Pasajero con sus ubicaciones inicial y destino
    def __init__(self, id, ubicacion_inicial, ubicacion_destino):
        self.id = id
        self.ubicacion_inicial = ubicacion_inicial
        self.ubicacion_destino = ubicacion_destino
        self.recogido = False


class Grafo:
    # Inicializa un objeto Grafo con nodos y aristas
    def __init__(self):
        self.aristas = {}
        self.nodos = set()

    # Agrega un nodo al grafo
    def agregar_nodo(self, nodo):
        self.nodos.add(nodo)

    # Agrega una arista con peso entre dos nodos
    def agregar_arista(self, desde, hasta, peso):
        self.aristas.setdefault(desde, []).append((hasta, peso))
        self.aristas.setdefault(hasta, []).append((desde, peso))
        self.nodos.update([desde, hasta])

    # Implementa el algoritmo de Dijkstra para encontrar el camino más corto
    def dijkstra(self, inicio, fin):
        import heapq
        cola = [(0, inicio)]
        distancias = {nodo: float('inf') for nodo in self.nodos}
        distancias[inicio] = 0
        camino_mas_corto = {nodo: None for nodo in self.nodos}

        while cola:
            distancia_actual, nodo_actual = heapq.heappop(cola)

            if nodo_actual == fin:
                camino = []
                while nodo_actual:
                    camino.append(nodo_actual)
                    nodo_actual = camino_mas_corto[nodo_actual]
                return camino[::-1], distancias[fin]

            if distancia_actual > distancias[nodo_actual]:
                continue

            for vecino, peso in self.aristas[nodo_actual]:
                distancia = distancia_actual + peso
                if distancia < distancias[vecino]:
                    distancias[vecino] = distancia
                    camino_mas_corto[vecino] = nodo_actual
                    heapq.heappush(cola, (distancia, vecino))

        return [], float('inf')

class Simulacion:
    # Simulación con un grafo y listas de taxis y pasajeros
    def __init__(self, grafo):
        self.grafo = grafo
        self.taxis = []
        self.pasajeros = []

    # Agrega un taxi
    def agregar_taxi(self, taxi):
        self.taxis.append(taxi)

    # Agrega un pasajero
    def agregar_pasajero(self, pasajero):
        self.pasajeros.append(pasajero)

pygame.init()
ventana = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Simulación de Taxis")
fondo_ciudad = pygame.transform.scale(pygame.image.load('city_background.jpg'), (800, 600))
imagen_taxi = pygame.image.load('taxi.png')
imagen_pasajero = pygame.image.load('passenger.png')
fuente = pygame.font.SysFont(None, 24)

# Dibuja el grafo en la ventana
def dibujar_grafo(grafo, ubicaciones):
    ventana.blit(fondo_ciudad, (0, 0))
    for nodo in grafo.nodos:
        if nodo != 'F':  # Omitir el nodo 'F'
            x, y = ubicaciones[nodo]
            pygame.draw.circle(ventana, (0, 0, 0), (x, y), 12)
            ventana.blit(fuente.render(nodo, True, (255, 255, 255)), (x - 10, y - 10))

# Dibuja los taxis y pasajeros que se veran en la ventana
def dibujar_entidades(taxis, pasajeros, ubicaciones, grafo):
    for taxi in taxis:
        pos_actual, pos_siguiente = taxi.mover(ubicaciones, grafo)
        if pos_actual and pos_siguiente:
            ventana.blit(imagen_taxi, (pos_siguiente[0] - 10, pos_siguiente[1] - 10))
        else:
            if taxi.ubicacion in ubicaciones:
                x, y = ubicaciones[taxi.ubicacion]
                ventana.blit(imagen_taxi, (x - 10, y - 10))
    for pasajero in pasajeros:
        if not pasajero.recogido and pasajero.ubicacion_inicial in ubicaciones:
            x, y = ubicaciones[pasajero.ubicacion_inicial]
            ventana.blit(imagen_pasajero, (x - 10, y - 10))

# Encuentra el taxi más cercano a un pasajero
def encontrar_taxi_mas_cercano(taxis, pasajero, ubicaciones):
    taxi_mas_cercano = None
    menor_distancia = float('inf')
    for taxi in taxis:
        if not taxi.ocupado:
            distancia = distancia_euclidea(ubicaciones[taxi.ubicacion], ubicaciones[pasajero.ubicacion_inicial])
            if distancia < menor_distancia:
                menor_distancia = distancia
                taxi_mas_cercano = taxi
    return taxi_mas_cercano

# Se dibuja los botones en la ventana
def dibujar_botones(botones):
    for boton in botones:
        pygame.draw.rect(ventana, boton['color'], boton['rect'])
        ventana.blit(fuente.render(boton['text'], True, (255, 255, 255)), boton['rect'].topleft)

# Esta es la funcion principl para que nos muestre en ventana
def main():
    grafo = Grafo()
    ubicaciones = {'Parque': (200, 170), 'Escuela': (555, 465), 'Cruce': (130, 460), 'Calle': (200, 40), 'Estacion': (740, 160), 'F': (265, 465), 'Casa': (415, 165)}
    for nodo in ubicaciones:
        grafo.agregar_nodo(nodo)
    for arista in [('Parque', 'F', 2), ('Calle', 'Parque', 2), ('F', 'Cruce', 3), ('F', 'Escuela', 4), ('Estacion', 'Casa', 1), ('Casa', 'Parque', 6)]:
        grafo.agregar_arista(*arista)

    simulacion = Simulacion(grafo)
    taxi1, taxi2 = Taxi(1, 'Calle', 'Calle'), Taxi(2, 'Estacion', 'Estacion')
    simulacion.agregar_taxi(taxi1)
    simulacion.agregar_taxi(taxi2)

    botones = [
        {'text': 'Recoger en Casa', 'rect': pygame.Rect(10, 10, 150, 25), 'color': (0, 128, 0), 'accion': lambda: 'Casa'},
        {'text': 'Recoger en Escuela', 'rect': pygame.Rect(10, 40, 150, 25), 'color': (0, 128, 0), 'accion': lambda: 'Escuela'},
        {'text': 'Recoger en Cruce', 'rect': pygame.Rect(10, 70, 150, 25), 'color': (0, 128, 0), 'accion': lambda: 'Cruce'},
        {'text': 'Recoger en Parque', 'rect': pygame.Rect(10, 100, 150, 25), 'color': (0, 128, 0), 'accion': lambda: 'Parque'},
        {'text': 'llevar a Escuela', 'rect': pygame.Rect(10, 140, 140, 25), 'color': (128, 0, 0), 'accion': lambda: 'Escuela'},
        {'text': 'llevar a Casa', 'rect': pygame.Rect(10, 170, 140, 25), 'color': (128, 0, 0), 'accion': lambda: 'Casa'},
        {'text': 'llevar a Cruce', 'rect': pygame.Rect(10, 200, 140, 25), 'color': (128, 0, 0), 'accion': lambda: 'Cruce'},
        {'text': 'llevar a Parque', 'rect': pygame.Rect(10, 230, 140, 25), 'color': (128, 0, 0), 'accion': lambda: 'Parque'},
    ]

    punto_recogida = None
    punto_destino = None

    clock = pygame.time.Clock()  # Objeto Clock para controlar la velocidad de actualización


    while True:
        for evento in pygame.event.get():
            if evento.type == QUIT:
                pygame.quit()
                return
            elif evento.type == MOUSEBUTTONDOWN:
                for boton in botones:
                    if boton['rect'].collidepoint(evento.pos):
                        if boton['text'].startswith('Recoger'):
                            punto_recogida = boton['accion']()
                        elif boton['text'].startswith('llevar'):
                            punto_destino = boton['accion']()

                        if punto_recogida and punto_destino:
                            pasajero = Pasajero(1, punto_recogida, punto_destino)
                            simulacion.agregar_pasajero(pasajero)
                            punto_recogida = None
                            punto_destino = None

        for pasajero in simulacion.pasajeros:
            if not pasajero.recogido:
                taxi_mas_cercano = encontrar_taxi_mas_cercano(simulacion.taxis, pasajero, ubicaciones)
                if taxi_mas_cercano:
                    taxi_mas_cercano.asignar_destino(pasajero.ubicacion_inicial, recoger_pasajero=True)
                    taxi_mas_cercano.calcular_ruta(grafo)
                    pasajero.recogido = True
                    taxi_mas_cercano.pasajero = pasajero
                    break

        ventana.fill((255, 255, 255))
        dibujar_grafo(grafo, ubicaciones)
        dibujar_entidades(simulacion.taxis, simulacion.pasajeros, ubicaciones, grafo)
        dibujar_botones(botones)
        pygame.display.update()
        clock.tick(50)  # Limitar la velocidad de actualización a 10 FPS

if __name__ == "__main__":
    main()

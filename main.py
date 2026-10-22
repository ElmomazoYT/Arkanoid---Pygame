import sys
import math
import json
import pygame

if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

ANCHO, ALTO, ESCALA = 224, 256, 1      
RUTA = "one/Arcade - Arkanoid - "      
ORIGEN_X, ORIGEN_Y = 8, 40             


def recorte(hoja, x, y, w, h):
    return hoja.subsurface(pygame.Rect(x, y, w, h))


class Bloque:
    def __init__(self, sprite, x, y, golpes):
        self.sprite = sprite
        self.rect = pygame.Rect(x, y, 16, 8)
        self.golpes = golpes

    def golpear(self):
        self.golpes -= 1
        return self.golpes <= 0


class Vaus:
    def __init__(self, hoja):
        self.frames = [recorte(hoja, 32, y, 32, 8) for y in (40, 0, 8, 16, 24, 32)]
        self.ancho, self.alto = self.frames[0].get_size()
        self.x0 = 98.0
        self.x = self.x0
        self.y = 227
        self.rapidez = 150
        self.tiempo = 0.0

    def actualizar(self, dt, teclas):
        self.tiempo = (self.tiempo + dt) % (len(self.frames) * 0.1)

        izq = teclas[pygame.K_LEFT] or teclas[pygame.K_a]
        der = teclas[pygame.K_RIGHT] or teclas[pygame.K_d]
        self.x += (der - izq) * self.rapidez * dt

        self.x = max(9, min(self.x, 215 - self.ancho))

    def dibujar(self, destino):
        frame = self.frames[int(self.tiempo / 0.1)]
        destino.blit(frame, (round(self.x), self.y))


class Pelota:
    def __init__(self, hoja):
        self.sprite = recorte(hoja, 0, 40, 5, 4)
        self.sombra = recorte(hoja, 0, 40, 9, 8)
        self.ancho, self.alto = self.sprite.get_size()
        self.rapidez = 180
        self.dx = self.dy = 0.0      
        self.x = self.y = 0.0
        self.x_ant = self.y_ant = 0.0
        self.pegada = True           
        self.perdida = False

    def set_angulo(self, grados):
        rad = math.radians(grados)    
        self.dx = math.cos(rad)
        self.dy = -math.sin(rad)

    def pegar(self, vaus):
        self.x = vaus.x + (vaus.ancho - self.ancho) / 2
        self.y = vaus.y - self.alto
        self.x_ant, self.y_ant = self.x, self.y

    def resetear(self, vaus):
        self.pegada = True
        self.perdida = False
        self.pegar(vaus)

    def lanzar(self):
        if self.pegada:
            self.pegada = False
            self.set_angulo(60)

    def actualizar(self, dt, vaus):
        if self.pegada:
            self.pegar(vaus)
            return

        self.x_ant, self.y_ant = self.x, self.y
        self.x += self.dx * self.rapidez * dt
        self.y += self.dy * self.rapidez * dt

        if self.x <= 8:
            self.x = 8
            self.dx = abs(self.dx)
        if self.x >= 215 - self.ancho:
            self.x = 215 - self.ancho
            self.dx = -abs(self.dx)
        if self.y <= 24:
            self.y = 24
            self.dy = abs(self.dy)

        if self.y >= ALTO - 1:
            self.perdida = True

    def rebotar_vaus(self, vaus):
        if self.pegada or self.dy <= 0:   
            return

        toca_x = self.x + self.ancho > vaus.x and self.x < vaus.x + vaus.ancho
        toca_y = vaus.y <= self.y + self.alto <= vaus.y + vaus.alto
        if toca_x and toca_y:
            self.y = vaus.y - self.alto

            centro_pelota = self.x + self.ancho / 2
            offset = (centro_pelota - (vaus.x + vaus.ancho / 2)) / (vaus.ancho / 2)
            offset = max(-1.0, min(1.0, offset))

            self.set_angulo(90 - offset * 60)

    def rebotar_bloques(self, bloques):
        if self.pegada:
            return

        caja = pygame.Rect(round(self.x), round(self.y), self.ancho, self.alto)
        for b in bloques:
            if not caja.colliderect(b.rect):
                continue

            if self.x_ant + self.ancho <= b.rect.left or self.x_ant >= b.rect.right:
                self.dx = -self.dx
            else:
                self.dy = -self.dy

            if b.golpear():
                bloques.remove(b)
            return 

    def dibujar(self, destino):
        pos = (round(self.x), round(self.y))
        destino.blit(self.sprite, pos)


def crear_tipos(hoja):
    return {
        "V": (recorte(hoja, 48, 0, 16, 8), 1),   # verde
        "P": (recorte(hoja, 32, 8, 16, 8), 1),   # rosado
        "A": (recorte(hoja, 16, 8, 16, 8), 1),   # azul
        "Y": (recorte(hoja, 48, 8, 16, 8), 1),   # amarillo
        "R": (recorte(hoja, 0, 8, 16, 8), 1),    # rojo
        "S": (recorte(hoja, 0, 16, 16, 8), 2),   # plateado
    }


def cargar_nivel(numero, tipos):
    with open(f"niveles/nivel_{numero}.json") as archivo:
        datos = json.load(archivo)

    bloques = []
    for col, fila, tipo, *_ in datos:
        sprite, golpes = tipos[tipo]
        bloques.append(Bloque(sprite, ORIGEN_X + col * 16, ORIGEN_Y + fila * 8, golpes))
    return bloques


def main():
    pygame.init()
    ventana = pygame.display.set_mode((ANCHO * ESCALA, ALTO * ESCALA))
    pygame.display.set_caption("Arkanoid")
    reloj = pygame.time.Clock()

    lienzo = pygame.Surface((ANCHO, ALTO)).convert()

    def cargar(nombre):
        return pygame.image.load(f"{RUTA}{nombre}.png").convert_alpha()

    fondos = cargar("Backgrounds - Fields")
    hoja_vaus = cargar("Playable Characters - Vaus")
    hoja_bloques = cargar("Miscellaneous - Blocks & Backgrounds")

    fondo = recorte(fondos, 0, 0, 224, 240)
    icono_vida = recorte(fondos, 8, 240, 16, 8)

    tipos = crear_tipos(hoja_bloques)
    bloques = cargar_nivel(1, tipos)
    vaus = Vaus(hoja_vaus)
    pelota = Pelota(hoja_vaus)
    pelota.resetear(vaus)
    vidas = 3

    corriendo = True
    while corriendo:
        dt = min(reloj.tick(60) / 1000, 1 / 30)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                pelota.lanzar()

        vaus.actualizar(dt, pygame.key.get_pressed())
        pelota.actualizar(dt, vaus)
        pelota.rebotar_vaus(vaus)
        pelota.rebotar_bloques(bloques)

        if pelota.perdida:
            vidas -= 1
            vaus.x = vaus.x0
            pelota.resetear(vaus)
            if vidas <= 0:
                print("Game Over")
                vidas = 3
                bloques = cargar_nivel(1, tipos)

        if not bloques:           
            bloques = cargar_nivel(1, tipos)
            vaus.x = vaus.x0
            pelota.resetear(vaus)

        # --- Dibujo ---
        lienzo.fill((0, 0, 0))
        lienzo.blit(fondo, (0, 16))
        for i in range(vidas):
            lienzo.blit(icono_vida, (9 + 16 * i, 248))

        lienzo.blit(pelota.sombra, (round(pelota.x), round(pelota.y)))
        for b in bloques:
            lienzo.blit(b.sprite, b.rect.topleft)
        vaus.dibujar(lienzo)
        pelota.dibujar(lienzo)

        pygame.transform.scale(lienzo, ventana.get_size(), ventana)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
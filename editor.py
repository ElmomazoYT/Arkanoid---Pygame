import json
import os
import pygame

NIVEL = 1                                  # cambia el numero para editar otro nivel
ARCHIVO = f"niveles/nivel_{NIVEL}.json"

ANCHO, ALTO, ESCALA = 224, 256, 2
ORIGEN_X, ORIGEN_Y = 8, 40                 
COLUMNAS, FILAS = 13, 20
PANEL = 150                      

TIPOS = {
    "V": (48, 0, 16, 8),    # verde
    "P": (32, 8, 16, 8),    # rosado
    "A": (16, 8, 16, 8),    # azul
    "Y": (48, 8, 16, 8),    # amarillo
    "R": (0, 8, 16, 8),     # rojo
    "S": (0, 15, 16, 9),    # plateado
}


def recorte(hoja, x, y, w, h):
    return pygame.transform.scale(hoja.subsurface((x, y, w, h)), (w * ESCALA, h * ESCALA))


def guardar(bloques):
    os.makedirs("niveles", exist_ok=True)
    datos = [[c, f, t, p] for (c, f), (t, p) in sorted(bloques.items(), key=lambda b: (b[0][1], b[0][0]))]
    with open(ARCHIVO, "w") as archivo:
        json.dump(datos, archivo)


def cargar():
    if not os.path.exists(ARCHIVO):
        return {}
    with open(ARCHIVO) as archivo:
        return {(c, f): (t, p) for c, f, t, p in json.load(archivo)}


def main():
    pygame.init()
    ancho_campo = ANCHO * ESCALA
    pantalla = pygame.display.set_mode((ancho_campo + PANEL, ALTO * ESCALA))
    pygame.display.set_caption(f"Editor de niveles - Nivel {NIVEL}")
    fuente = pygame.font.SysFont(None, 20)
    reloj = pygame.time.Clock()

    hoja_fondo = pygame.image.load("one/Arcade - Arkanoid - Backgrounds - Fields.png").convert_alpha()
    hoja_bloques = pygame.image.load("one/Arcade - Arkanoid - Miscellaneous - Blocks & Backgrounds.png").convert_alpha()
    fondo = recorte(hoja_fondo, 0, 0, 224, 240)
    sprites = {letra: recorte(hoja_bloques, *coords) for letra, coords in TIPOS.items()}

    botones = {letra: pygame.Rect(ancho_campo + 20, 40 + i * 40, 16 * ESCALA + 12, 9 * ESCALA + 12)
               for i, letra in enumerate(TIPOS)}

    bloques = cargar()         
    seleccionado = "V"
    mensaje = "Nivel cargado" if bloques else "Nivel nuevo"
    corriendo = True

    while corriendo:
        reloj.tick(60)
        mx, my = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_s:
                    guardar(bloques)
                    mensaje = f"Guardado: {ARCHIVO}"
                elif evento.key == pygame.K_l:
                    bloques = cargar()
                    mensaje = "Nivel cargado"
                elif evento.key == pygame.K_c:
                    bloques = {}
                    mensaje = "Nivel limpiado"
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for letra, rect in botones.items():      
                    if rect.collidepoint(evento.pos):
                        seleccionado = letra

        col = (mx // ESCALA - ORIGEN_X) // 16
        fila = (my // ESCALA - ORIGEN_Y) // 8
        dentro = mx < ancho_campo and 0 <= col < COLUMNAS and 0 <= fila < FILAS

        if dentro:
            botones_mouse = pygame.mouse.get_pressed()
            if botones_mouse[0]:
                bloques[(col, fila)] = (seleccionado, None)
            elif botones_mouse[2]:
                bloques.pop((col, fila), None)

        pantalla.fill((20, 20, 20))
        pantalla.blit(fondo, (0, 16 * ESCALA))

        for c in range(COLUMNAS):                        
            for f in range(FILAS):
                celda = pygame.Rect((ORIGEN_X + c * 16) * ESCALA, (ORIGEN_Y + f * 8) * ESCALA,
                                    16 * ESCALA, 8 * ESCALA)
                pygame.draw.rect(pantalla, (50, 50, 80), celda, 1)

        for (c, f), (tipo, _) in bloques.items():
            pantalla.blit(sprites[tipo], ((ORIGEN_X + c * 16) * ESCALA, (ORIGEN_Y + f * 8) * ESCALA))

        if dentro:                                        
            pygame.draw.rect(pantalla, (255, 255, 255),
                             ((ORIGEN_X + col * 16) * ESCALA, (ORIGEN_Y + fila * 8) * ESCALA,
                              16 * ESCALA, 8 * ESCALA), 2)

        
        for letra, rect in botones.items():
            pantalla.blit(sprites[letra], (rect.x + 6, rect.y + 6))
            if letra == seleccionado:
                pygame.draw.rect(pantalla, (255, 255, 0), rect, 2)

        ayuda = ["Clic izq: poner", "Clic der: borrar", "S: guardar", "L: cargar", "C: limpiar", "", mensaje]
        for i, linea in enumerate(ayuda):
            pantalla.blit(fuente.render(linea, True, (220, 220, 220)), (ancho_campo + 10, 330 + i * 20))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
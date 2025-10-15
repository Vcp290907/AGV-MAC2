import os
import cv2 as cv
import numpy as np

# Gera um tabuleiro ChArUco 5x7 para impressão em A4 (300 DPI aprox.)
# Especificações físicas: quadrado=40 mm (0.04 m), marcador=20 mm (0.02 m) — tamanhos reais na impressão

# A4 (retrato) em pixels para ~300 DPI
DPI = 300
A4_W_MM, A4_H_MM = 210.0, 297.0
A4_W_PX, A4_H_PX = int(A4_W_MM / 25.4 * DPI), int(A4_H_MM / 25.4 * DPI)

# Tamanho do tabuleiro (colunas x linhas) — 5x7 para caber 40 mm em A4 retrato
COLS, ROWS = 5, 7

# Tamanhos físicos
SQUARE_MM = 40.0  # 40 mm
MARKER_MM = 20.0  # 20 mm
SQUARE_M = SQUARE_MM / 1000.0
MARKER_M = MARKER_MM / 1000.0

def place_on_a4_no_scale(img_gray: np.ndarray) -> np.ndarray:
	"""Centraliza no A4 SEM redimensionar (mantém 40 mm exatos por quadrado)."""
	h, w = img_gray.shape[:2]
	if w > A4_W_PX or h > A4_H_PX:
		raise RuntimeError("Tabuleiro não cabe em A4 retrato com 40 mm por quadrado. Use paisagem ou reduza o tamanho.")
	canvas = np.full((A4_H_PX, A4_W_PX), 255, dtype=np.uint8)
	x0 = (A4_W_PX - w) // 2
	y0 = (A4_H_PX - h) // 2
	canvas[y0:y0 + h, x0:x0 + w] = img_gray
	return canvas

def main():
	# Dicionário ArUco
	aruco = cv.aruco
	dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)

	# Tentar criar o tabuleiro ChArUco de forma compatível com diferentes versões do OpenCV
	board = None
	if hasattr(aruco, 'CharucoBoard_create'):
		# API clássica
		board = aruco.CharucoBoard_create(COLS, ROWS, SQUARE_M, MARKER_M, dictionary)
	elif hasattr(aruco, 'CharucoBoard'):
		# Algumas builds expõem a classe com construtor
		try:
			board = aruco.CharucoBoard((COLS, ROWS), SQUARE_M, MARKER_M, dictionary)
		except Exception:
			board = None

	if board is None:
		raise RuntimeError("Sua instalação do OpenCV não expõe ChArUco nesta API. Atualize para uma versão com suporte ao Charuco.")

	# Calcular resolução exata para 40 mm por quadrado
	square_px = int(round(SQUARE_MM / 25.4 * DPI))  # ~472 px a 300 DPI
	board_w_px = COLS * square_px
	board_h_px = ROWS * square_px
	# Gerar já no tamanho final, sem redimensionar depois
	board_img = board.generateImage((board_w_px, board_h_px), marginSize=0, borderBits=1)

	a4_img = place_on_a4_no_scale(board_img)
	out_path = os.path.join(os.path.dirname(__file__), "charuco_board.png")
	cv.imwrite(out_path, a4_img)
	print(f"Tabuleiro ChArUco 7x5 gerado em A4 e salvo como '{out_path}'")

if __name__ == "__main__":
	main()

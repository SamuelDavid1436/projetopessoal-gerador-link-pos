# -*- coding: utf-8 -*-
"""
gerar_identidade_visual.py
Gera assets/icone.ico (multi-resolução) e assets/logo.png a partir de
formas vetoriais desenhadas com PIL — paleta azul marinho + dourado,
tema do app "Captura de Mensalidade - Pós-Graduação".
Rodar uma vez (ou sempre que quiser regenerar a identidade visual).
"""

import os
from PIL import Image, ImageDraw, ImageFont

AZUL_MARINHO = (18, 41, 75, 255)
AZUL_MARINHO_ESCURO = (11, 28, 54, 255)
AZUL_MARINHO_CLARO = (39, 67, 114, 255)
DOURADO = (199, 154, 62, 255)
DOURADO_CLARO = (224, 184, 108, 255)
BRANCO = (255, 255, 255, 255)
CINZA_CLARO = (223, 229, 238, 255)

PASTA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(PASTA_ASSETS, exist_ok=True)


def _rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def desenhar_icone_base(tamanho=1024):
    """Desenha o ícone em alta resolução: fundo azul-marinho arredondado,
    documento branco com linhas (extrato) e um selo dourado com 'R$'
    representando a captura do link de pagamento."""
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    raio_fundo = int(tamanho * 0.22)
    fundo = Image.new("RGBA", (tamanho, tamanho), AZUL_MARINHO)
    mask_fundo = _rounded_mask(tamanho, raio_fundo)
    img.paste(fundo, (0, 0), mask_fundo)

    # leve gradiente/sombra interna decorativa (círculo mais claro ao fundo)
    overlay = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse(
        [tamanho * 0.55, -tamanho * 0.15, tamanho * 1.25, tamanho * 0.55],
        fill=(*AZUL_MARINHO_CLARO[:3], 90),
    )
    overlay.putalpha(Image.composite(overlay.split()[3], Image.new("L", (tamanho, tamanho), 0), mask_fundo))
    img.alpha_composite(overlay)

    # ---- Documento (extrato) ----
    doc_w = int(tamanho * 0.44)
    doc_h = int(tamanho * 0.56)
    doc_x = int(tamanho * 0.20)
    doc_y = int(tamanho * 0.22)
    dobra = int(doc_w * 0.28)

    pontos_doc = [
        (doc_x, doc_y),
        (doc_x + doc_w - dobra, doc_y),
        (doc_x + doc_w, doc_y + dobra),
        (doc_x + doc_w, doc_y + doc_h),
        (doc_x, doc_y + doc_h),
    ]
    draw.polygon(pontos_doc, fill=BRANCO)
    # dobra do canto (triângulo em azul marinho claro)
    draw.polygon(
        [(doc_x + doc_w - dobra, doc_y), (doc_x + doc_w, doc_y + dobra), (doc_x + doc_w - dobra, doc_y + dobra)],
        fill=CINZA_CLARO,
    )

    # linhas do "extrato" dentro do documento
    linha_x0 = doc_x + int(doc_w * 0.16)
    linha_x1 = doc_x + doc_w - int(doc_w * 0.16)
    espacamento = int(doc_h * 0.13)
    largura_linha = max(4, int(tamanho * 0.012))
    for i in range(4):
        y = doc_y + int(doc_h * 0.30) + i * espacamento
        cor = AZUL_MARINHO_CLARO if i != 3 else DOURADO
        largura_final = linha_x1 if i < 3 else doc_x + int(doc_w * 0.55)
        draw.line([(linha_x0, y), (largura_final, y)], fill=cor, width=largura_linha)

    # ---- Selo dourado (link de pagamento) ----
    selo_raio = int(tamanho * 0.235)
    selo_cx = int(tamanho * 0.70)
    selo_cy = int(tamanho * 0.72)
    draw.ellipse(
        [selo_cx - selo_raio, selo_cy - selo_raio, selo_cx + selo_raio, selo_cy + selo_raio],
        fill=DOURADO, outline=AZUL_MARINHO_ESCURO, width=max(3, int(tamanho * 0.006)),
    )

    texto = "R$"
    fonte = None
    for nome in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"):
        try:
            fonte = ImageFont.truetype(nome, int(selo_raio * 1.05))
            break
        except OSError:
            continue
    if fonte is None:
        fonte = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), texto, font=fonte)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((selo_cx - tw / 2 - bbox[0], selo_cy - th / 2 - bbox[1]), texto, font=fonte, fill=BRANCO)

    return img


def gerar_ico():
    base = desenhar_icone_base(1024)
    caminho = os.path.join(PASTA_ASSETS, "icone.ico")
    tamanhos = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    base.save(caminho, format="ICO", sizes=tamanhos)
    print(f"Ícone gerado: {caminho}")


def gerar_png_icone(tamanho=512):
    base = desenhar_icone_base(tamanho * 2).resize((tamanho, tamanho), Image.LANCZOS)
    caminho = os.path.join(PASTA_ASSETS, "icone.png")
    base.save(caminho)
    print(f"PNG do ícone gerado: {caminho}")
    return base


def gerar_logo_horizontal(icone_png):
    largura, altura = 1200, 300
    logo = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))

    tam_icone = 220
    icone = icone_png.resize((tam_icone, tam_icone), Image.LANCZOS)
    pos_y_icone = (altura - tam_icone) // 2
    logo.paste(icone, (40, pos_y_icone), icone)

    draw = ImageDraw.Draw(logo)
    fonte_titulo = fonte_sub = None
    for nome in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"):
        try:
            fonte_titulo = ImageFont.truetype(nome, 62)
            break
        except OSError:
            continue
    for nome in ("DejaVuSans.ttf", "Arial.ttf", "arial.ttf"):
        try:
            fonte_sub = ImageFont.truetype(nome, 36)
            break
        except OSError:
            continue
    if fonte_titulo is None:
        fonte_titulo = ImageFont.load_default()
    if fonte_sub is None:
        fonte_sub = ImageFont.load_default()

    x_texto = 40 + tam_icone + 36
    draw.text((x_texto, 78), "Captura de Mensalidade", font=fonte_titulo, fill=AZUL_MARINHO)
    draw.text((x_texto, 78 + 74), "Pós-Graduação", font=fonte_sub, fill=DOURADO)

    caminho = os.path.join(PASTA_ASSETS, "logo.png")
    logo.save(caminho)
    print(f"Logo horizontal gerada: {caminho}")


if __name__ == "__main__":
    gerar_ico()
    icone_png = gerar_png_icone()
    gerar_logo_horizontal(icone_png)

from datetime import datetime
import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import models


def _get_sala_nome(item: models.PatrimonioDB) -> str:
    if item.sala and item.sala.nome:
        return item.sala.nome
    return "Sem sala"


def _find_logo_path(filename: str) -> str | None:
    backend_dir = Path(__file__).resolve().parent
    candidates = [
        backend_dir / filename,
        backend_dir.parent / "frontend" / "public" / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def _formatar_valor_br(valor: float) -> str:
    # 21900.0 -> 21.900,00
    valor_formatado = f"{valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {valor_formatado}"


def gerar_pdf_patrimonio(items: list[models.PatrimonioDB]) -> io.BytesIO:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=1.5 * cm,
    )
    elements = []

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "TituloCustom",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1a5490"),
        spaceAfter=8,
        alignment=1,
        fontName="Helvetica-Bold",
    )

    subtitulo_style = ParagraphStyle(
        "SubTituloCustom",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        alignment=1,
        spaceAfter=18,
    )

    sala_style = ParagraphStyle(
        "SalaCustom",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1a5490"),
        spaceAfter=10,
        spaceBefore=10,
        fontName="Helvetica-Bold",
        borderColor=colors.HexColor("#1a5490"),
        borderWidth=1,
        borderPadding=6,
    )

    desc_style = ParagraphStyle(
        "DescCell",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#222222"),
    )

    comp_nome_style = ParagraphStyle(
        "CompNome",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#374151"),
        leftIndent=10,
    )

    comp_obs_style = ParagraphStyle(
        "CompObs",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#6b7280"),
        leftIndent=10,
    )

    titulo = "Relatório de Patrimônio<br/><b>LAMIC - Laboratório de Análises Micotoxicológicas</b>"
    logo_lamic_path = _find_logo_path("logo_lamic.png")
    logo_ufsm_path = _find_logo_path("ufsm_png.png")

    if logo_lamic_path and logo_ufsm_path:
        logo_lamic = Image(logo_lamic_path, width=2 * cm, height=1.5 * cm)
        logo_ufsm = Image(logo_ufsm_path, width=2 * cm, height=1.5 * cm)
        header_data = [[logo_lamic, Paragraph(titulo, titulo_style), logo_ufsm]]
        header_widths = [2.5 * cm, 12 * cm, 2.5 * cm]
    else:
        header_data = [[Paragraph(titulo, titulo_style)]]
        header_widths = [17 * cm]

    header_table = Table(header_data, colWidths=header_widths)
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elements.append(header_table)
    elements.append(
        Paragraph(
            f"<font size=9 color='#666666'>Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</font>",
            subtitulo_style,
        )
    )
    elements.append(Spacer(1, 0.25 * cm))

    separator = Table([[""]], colWidths=[17 * cm])
    separator.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#1a5490")),
            ]
        )
    )
    elements.append(separator)
    elements.append(Spacer(1, 0.4 * cm))

    itens_por_sala: dict[str, list[models.PatrimonioDB]] = {}
    for item in items:
        sala_nome = _get_sala_nome(item)
        itens_por_sala.setdefault(sala_nome, []).append(item)

    for sala_nome in sorted(itens_por_sala.keys()):
        elements.append(Paragraph(f"<b>{sala_nome}</b>", sala_style))

        data = [["Patr. LAMIC", "Patr. UFSM / Nº Série", "Descrição / Componente", "Qtd", "Valor (R$)"]]
        comp_rows = []  # índices das linhas de componente (1-based dentro de data)

        total_valor = 0.0
        for item in itens_por_sala[sala_nome]:
            valor_item = float(item.valor_total or 0)
            desc_para = Paragraph(item.nome or "", desc_style)
            data.append(
                [
                    item.numero_patrimonio_lamic or "-",
                    item.numero_patrimonio_ufsm or "-",
                    desc_para,
                    str(item.quantidade or 0),
                    _formatar_valor_br(valor_item),
                ]
            )
            total_valor += valor_item

            componentes = getattr(item, "componentes", []) or []
            for comp in componentes:
                valor_comp = float(comp.valor or 0)
                partes = [Paragraph(f"└ {comp.nome}", comp_nome_style)]
                if comp.observacao:
                    partes.append(Paragraph(comp.observacao, comp_obs_style))
                comp_cell = partes[0] if len(partes) == 1 else partes
                data.append(
                    [
                        "",
                        comp.numero_serie or "—",
                        comp_cell,
                        str(comp.quantidade or 1),
                        _formatar_valor_br(valor_comp) if valor_comp else "—",
                    ]
                )
                comp_rows.append(len(data) - 1)

        data.append(["", "", "TOTAL SALA:", "", _formatar_valor_br(total_valor)])

        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5490")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 1), (1, -2), "CENTER"),
            ("ALIGN", (2, 1), (2, -2), "LEFT"),
            ("ALIGN", (3, 1), (3, -2), "CENTER"),
            ("ALIGN", (4, 1), (4, -2), "RIGHT"),
            ("VALIGN", (0, 1), (-1, -2), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -2), 0.3, colors.HexColor("#d1d5db")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f3f4f6")]),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0f7")),
            ("ALIGN", (2, -1), (2, -1), "RIGHT"),
            ("ALIGN", (4, -1), (4, -1), "RIGHT"),
        ]

        # Estilo diferenciado para linhas de componente
        for ri in comp_rows:
            style_cmds += [
                ("BACKGROUND", (0, ri), (-1, ri), colors.HexColor("#eef2f7")),
                ("FONTSIZE", (0, ri), (-1, ri), 8),
                ("TOPPADDING", (0, ri), (-1, ri), 3),
                ("BOTTOMPADDING", (0, ri), (-1, ri), 3),
                ("TEXTCOLOR", (0, ri), (1, ri), colors.HexColor("#6b7280")),
                ("LINEABOVE", (0, ri), (-1, ri), 0.3, colors.HexColor("#cbd5e1")),
            ]

        table = Table(
            data,
            colWidths=[2.8 * cm, 3.2 * cm, 9.0 * cm, 1.2 * cm, 2.5 * cm],
            repeatRows=1,
        )
        table.setStyle(TableStyle(style_cmds))

        elements.append(table)
        elements.append(Spacer(1, 0.35 * cm))

    elements.append(Spacer(1, 0.45 * cm))
    footer_separator = Table([[""]], colWidths=[17 * cm])
    footer_separator.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#1a5490")),
            ]
        )
    )
    elements.append(footer_separator)

    total_geral = sum(float(item.valor_total or 0) for item in items)
    footer_text = (
        f"<font size=9 color='#666666'><b>Total Geral de Patrimônio:</b> {_formatar_valor_br(total_geral)} "
        f"| <b>Total de Itens:</b> {len(items)}</font>"
    )
    elements.append(Paragraph(footer_text, subtitulo_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
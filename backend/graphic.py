import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import io
from database import engine


def _formatar_moeda_br(valor, _pos=None):
    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_grafico_valor_por_sala():
    query = """
        SELECT s.nome AS sala, p.valor_total, p.quantidade
        FROM patrimonios p
        JOIN salas s ON p.sala_id = s.id
    """

    dados = pd.read_sql(query, engine)
    if dados.empty:
        return None

    dados["valor_total"] = dados["valor_total"].fillna(0)
    dados["quantidade"] = dados["quantidade"].fillna(0)

    dados["valor_real"] = dados["valor_total"] * dados["quantidade"]
    valor_por_sala = dados.groupby("sala", as_index=False)["valor_real"].sum()
    valor_por_sala = valor_por_sala.sort_values(by="valor_real", ascending=False)

    total_salas = len(valor_por_sala)
    # Layout em paisagem: usa melhor largura da tela.
    largura_figura = max(13, min(22, 0.42 * total_salas + 7))
    altura_figura = 7.4

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(largura_figura, altura_figura), facecolor="#f8fafc")
    ax.set_facecolor("#f8fafc")

    x_posicoes = list(range(total_salas))
    denominador = max(total_salas - 1, 1)
    cores = [plt.cm.Oranges(0.35 + 0.55 * (indice / denominador)) for indice in range(total_salas)]
    barras = ax.bar(
        x_posicoes,
        valor_por_sala["valor_real"],
        color=cores,
        edgecolor="#ffffff",
        linewidth=1,
        width=0.72,
    )

    maior_valor = float(valor_por_sala["valor_real"].max()) if total_salas else 0.0
    deslocamento_rotulo = maior_valor * 0.018 if maior_valor else 1

    # Rotulos em poucas barras para manter legibilidade.
    barras_para_rotular = min(8, total_salas)
    for indice, (barra, valor) in enumerate(zip(barras, valor_por_sala["valor_real"])):
        if indice >= barras_para_rotular:
            continue
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + deslocamento_rotulo,
            _formatar_moeda_br(valor),
            va="bottom",
            ha="center",
            fontsize=9,
            rotation=90,
            color="#374151",
        )

    if maior_valor > 0:
        ax.set_ylim(0, maior_valor * 1.26)

    ax.set_title("Valor Total de Patrimônio por Sala", fontsize=17, weight="bold", color="#111827", pad=14)
    ax.set_xlabel("Salas", fontsize=12, color="#374151")
    ax.set_ylabel("Valor acumulado (R$)", fontsize=12, color="#374151")
    ax.set_xticks(x_posicoes)
    ax.set_xticklabels(valor_por_sala["sala"], rotation=40, ha="right", fontsize=9)
    ax.tick_params(axis="y", labelsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(_formatar_moeda_br))
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.grid(axis="x", visible=False)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.text(
        0.012,
        0.01,
        f"Total geral: {_formatar_moeda_br(valor_por_sala['valor_real'].sum())} | Salas: {total_salas}",
        fontsize=10,
        color="#4b5563",
    )
    plt.tight_layout(rect=[0, 0.05, 1, 1])

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    buffer.seek(0)
    plt.close(fig)

    return buffer


def grafico_valor_sala():
    # Compatibilidade com código legado que usa o nome antigo.
    return gerar_grafico_valor_por_sala()

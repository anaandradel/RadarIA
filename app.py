import streamlit as st
import pandas as pd
import unicodedata
import re
import os
import time
from google import genai
from google.genai import types
def analisar_com_gemini(prompt, transcricao=None, audio=None):
    inicio_total = time.perf_counter()

    try:
        # ==============================
        # PREPARAÇÃO
        # ==============================
        inicio_preparacao = time.perf_counter()

        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )

        partes = [prompt]

        if transcricao:
            partes.append(
                "\n\nTRANSCRIÇÃO DA LIGAÇÃO:\n" + transcricao
            )

        tamanho_audio_mb = 0

        if audio is not None:
            audio_bytes = audio.getvalue()
            tamanho_audio_mb = len(audio_bytes) / (1024 * 1024)

            partes.append(
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/mpeg"
                )
            )

        tempo_preparacao = time.perf_counter() - inicio_preparacao

        print("")
        print("======================================")
        print("📡 RADAR - MEDIÇÃO DE DESEMPENHO")
        print("======================================")
        print(f"⏱️ Preparação: {tempo_preparacao:.2f}s")
        print(f"🎙️ Áudio: {tamanho_audio_mb:.2f} MB")
        print(f"📝 Transcrição: {len(transcricao or '')} caracteres")

        # ==============================
        # GEMINI
        # ==============================
        inicio_gemini = time.perf_counter()

        resposta = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=partes
        )

        tempo_gemini = time.perf_counter() - inicio_gemini
        tempo_total = time.perf_counter() - inicio_total

        print(f"🧠 Gemini: {tempo_gemini:.2f}s")
        print(f"⚡ TOTAL: {tempo_total:.2f}s")
        print("======================================")
        print("")

        return resposta.text

    except Exception as e:
        tempo_total = time.perf_counter() - inicio_total

        print("")
        print("======================================")
        print("❌ ERRO NA ANÁLISE")
        print(f"⏱️ Tempo até o erro: {tempo_total:.2f}s")
        print(f"Erro: {str(e)}")
        print("======================================")
        print("")

        return f"ERRO NA ANÁLISE COM IA: {str(e)}"

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
page_title="RADAR IA",
page_icon="📡",
layout="wide"
)


# ============================================================
# FUNÇÕES
# ============================================================

def normalizar(valor):
    """Normaliza textos para facilitar comparações."""

    if pd.isna(valor):
        return ""

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return texto


def encontrar_coluna(df, nomes):
    """Localiza uma coluna pelo nome, ignorando acentos."""

    nomes_normalizados = [
        normalizar(nome)
        for nome in nomes
    ]

    for coluna in df.columns:

        if normalizar(coluna) in nomes_normalizados:
            return coluna

    return None


def contem_detrator(texto):
    """Verifica se os resultados contêm CSAT Detrator."""

    texto = normalizar(texto)

    return "detrator" in texto


def contem_rpc_nao(texto):
    """Verifica se os resultados contêm RPC NÃO."""

    texto = normalizar(texto)

    padroes = [
        r"rpc\s*[-:]\s*nao",
        r"rpc\s+nao",
        r"rpc_nao",
        r"rpc.*nao"
    ]

    return any(
        re.search(
            padrao,
            texto
        )
        for padrao in padroes
    )


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown("""
<style>
    .radar-header {
        background: linear-gradient(135deg, #0086FF 0%, #0066CC 100%);
        padding: 28px 35px;
        border-radius: 0 0 18px 18px;
        margin-bottom: 28px;
        box-shadow: 0 4px 15px rgba(0, 102, 204, 0.18);
    }

    .radar-logo {
        color: white;
        font-size: 38px;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 0;
    }

    .radar-subtitle {
        color: rgba(255,255,255,0.92);
        font-size: 16px;
        margin-top: 5px;
    }

    .radar-version {
        color: rgba(255,255,255,0.75);
        font-size: 12px;
        margin-top: 12px;
    }
</style>

<div class="radar-header">
    <div class="radar-logo">📡 RADAR</div>
    <div class="radar-subtitle">
        Inteligência para Auditoria de Atendimento
    </div>
    <div class="radar-version">
        Plataforma de apoio à auditoria de qualidade
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    """
    **Bem-vindo ao RADAR!**

    Analise as ligações do relatório da Genesys e identifique
    rapidamente os atendimentos que precisam de atenção.
    """
)

st.divider()


# ============================================================
# ETAPA 1 — UPLOAD
# ============================================================

st.header("📄 1. Relatório da Genesys")

arquivo = st.file_uploader(
    "Anexe o relatório CSV do colaborador",
    type=["csv"]
)


if arquivo is None:

    st.info(
        "📎 Anexe o relatório da Genesys para começar."
    )

    st.stop()


# ============================================================
# LEITURA DO CSV
# ============================================================

df = None


# UTF-8 + vírgula
try:

    arquivo.seek(0)

    df = pd.read_csv(
        arquivo,
        sep=",",
        encoding="utf-8-sig"
    )

except Exception:
    pass


# Latin-1 + vírgula
if df is None:

    try:

        arquivo.seek(0)

        df = pd.read_csv(
            arquivo,
            sep=",",
            encoding="latin1"
        )

    except Exception:
        pass


# UTF-8 + ponto e vírgula
if df is None:

    try:

        arquivo.seek(0)

        df = pd.read_csv(
            arquivo,
            sep=";",
            encoding="utf-8-sig"
        )

    except Exception:
        pass


if df is None:

    st.error(
        "❌ Não foi possível ler o relatório CSV."
    )

    st.stop()


# ============================================================
# LIMPEZA
# ============================================================

df.columns = [
    str(coluna).strip()
    for coluna in df.columns
]


st.success(
    f"✅ Relatório carregado: {len(df)} ligações."
)


# ============================================================
# IDENTIFICAÇÃO DAS COLUNAS
# ============================================================

col_usuario = encontrar_coluna(
    df,
    [
        "Usuários",
        "Usuarios",
        "Usuário",
        "Usuario"
    ]
)


col_data = encontrar_coluna(
    df,
    [
        "Data"
    ]
)


col_duracao = encontrar_coluna(
    df,
    [
        "Duração",
        "Duracao"
    ]
)


col_finalizacao = encontrar_coluna(
    df,
    [
        "Finalização",
        "Finalizacao"
    ]
)


col_resultados = encontrar_coluna(
    df,
    [
        "Resultados com êxito",
        "Resultados com exito"
    ]
)


col_transferidas = encontrar_coluna(
    df,
    [
        "Transferidas",
        "Transferida"
    ]
)


col_desconexao = encontrar_coluna(
    df,
    [
        "Tipo de desconexão",
        "Tipo de desconexao"
    ]
)


# ============================================================
# ESTRUTURA
# ============================================================

st.divider()

st.header("🔎 Estrutura identificada")


c1, c2, c3 = st.columns(3)


with c1:

    if col_transferidas:

        st.success(
            f"Transferidas: **{col_transferidas}**"
        )

    else:

        st.error(
            "Transferidas não encontrada."
        )


with c2:

    if col_desconexao:

        st.success(
            f"Desconexão: **{col_desconexao}**"
        )

    else:

        st.error(
            "Tipo de desconexão não encontrada."
        )


with c3:

    if col_resultados:

        st.success(
            f"Resultados: **{col_resultados}**"
        )

    else:

        st.error(
            "Resultados com êxito não encontrada."
        )


# ============================================================
# VALIDAÇÃO
# ============================================================

colunas_obrigatorias = {
    "Transferidas": col_transferidas,
    "Tipo de desconexão": col_desconexao,
    "Resultados com êxito": col_resultados
}


faltantes = [
    nome
    for nome, coluna in colunas_obrigatorias.items()
    if coluna is None
]


if faltantes:

    st.error(
        "❌ Não consegui localizar: "
        + ", ".join(faltantes)
    )

    st.write(
        "### Colunas encontradas no CSV:"
    )

    st.dataframe(
        pd.DataFrame(
            {
                "Colunas": list(df.columns)
            }
        ),
        use_container_width=True,
        hide_index=True
    )

    st.stop()


# ============================================================
# TRIAGEM
# ============================================================

def classificar_ligacao(linha):

    transferidas = normalizar(
        linha[col_transferidas]
    )

    desconexao = normalizar(
        linha[col_desconexao]
    )

    resultados = normalizar(
        linha[col_resultados]
    )


    # ========================================================
    # 🔴 CENÁRIO B
    #
    # TRANSFERIDAS = SIM
    # +
    # CSAT = DETRATOR
    # +
    # RPC = NÃO
    # ========================================================

    if transferidas == "sim":

        tem_detrator = contem_detrator(
            resultados
        )

        tem_rpc_nao = contem_rpc_nao(
            resultados
        )

        if (
            tem_detrator
            and tem_rpc_nao
        ):

            return {
                "status": "🔴 INVESTIGAÇÃO DE ATENDIMENTO",

                "motivo": (
                    "Transferidas = SIM + "
                    "CSAT DETRATOR + RPC NÃO"
                ),

                "tipo": "atendimento"
            }


    # ========================================================
    # 🟡 CENÁRIO A
    #
    # TRANSFERIDAS = NÃO
    # +
    # TIPO DE DESCONEXÃO = SISTEMA
    #
    # ESTE É O ÚNICO CASO DE DESCONEXÃO
    # CONSIDERADO INVESTIGAÇÃO.
    # ========================================================

    if (
        transferidas == "nao"
        and desconexao == "sistema"
    ):

        return {
            "status": "🟡 INVESTIGAÇÃO DE DESCONEXÃO",

            "motivo": (
                "Transferidas = NÃO + "
                "Tipo de desconexão = SISTEMA"
            ),

            "tipo": "desconexao"
        }


    # ========================================================
    # 🔵 REVISÃO — NÃO TRANSFERIDA
    #
    # TRANSFERIDAS = NÃO
    #
    # Não significa problema.
    # Apenas disponibilizamos para revisão.
    # ========================================================

    if transferidas == "nao":

        return {
            "status": "🔵 REVISÃO — NÃO TRANSFERIDA",

            "motivo": (
                "Transferidas = NÃO. "
                "Revisar a ligação se necessário."
            ),

            "tipo": "revisao"
        }


    # ========================================================
    # 🟢 SEM ALERTA
    # ========================================================

    return {
        "status": "🟢 SEM ALERTA",

        "motivo": "",

        "tipo": ""
    }


# ============================================================
# APLICA TRIAGEM
# ============================================================

classificacoes = df.apply(
    classificar_ligacao,
    axis=1
)


df["RADAR_STATUS"] = [
    resultado["status"]
    for resultado in classificacoes
]


df["RADAR_MOTIVO"] = [
    resultado["motivo"]
    for resultado in classificacoes
]


df["RADAR_TIPO"] = [
    resultado["tipo"]
    for resultado in classificacoes
]


# ============================================================
# FILA DO RADAR
# ============================================================

df_alertas = df[
    df["RADAR_TIPO"] != ""
].copy()


# ============================================================
# PAINEL DE INDICADORES
# ============================================================

st.divider()

st.header("📊 Visão geral da auditoria")

total_ligacoes = len(df)

total_atendimento = len(
    df[df["RADAR_TIPO"] == "atendimento"]
)

total_desconexao = len(
    df[df["RADAR_TIPO"] == "desconexao"]
)

total_revisao = len(
    df[df["RADAR_TIPO"] == "revisao"]
)

total_sem_alerta = len(
    df[df["RADAR_TIPO"] == ""]
)

st.markdown("""
<style>
.radar-card {
    padding: 22px;
    border-radius: 14px;
    background: white;
    border: 1px solid #E5E7EB;
    min-height: 145px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.06);
}

.radar-card-title {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 10px;
}

.radar-card-number {
    font-size: 36px;
    font-weight: 800;
    margin-bottom: 4px;
}

.radar-card-description {
    font-size: 13px;
    color: #6B7280;
}

.radar-red {
    border-top: 5px solid #E53935;
}

.radar-yellow {
    border-top: 5px solid #F4B400;
}

.radar-blue {
    border-top: 5px solid #4285F4;
}

.radar-green {
    border-top: 5px solid #34A853;
}
</style>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="radar-card radar-red">
            <div class="radar-card-title">
                🔴 Investigação de atendimento
            </div>
            <div class="radar-card-number">
                {total_atendimento}
            </div>
            <div class="radar-card-description">
                Ligações para investigar
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"""
        <div class="radar-card radar-yellow">
            <div class="radar-card-title">
                🟡 Investigação de desconexão
            </div>
            <div class="radar-card-number">
                {total_desconexao}
            </div>
            <div class="radar-card-description">
                Possíveis desconexões
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div class="radar-card radar-blue">
            <div class="radar-card-title">
                🔵 Revisão
            </div>
            <div class="radar-card-number">
                {total_revisao}
            </div>
            <div class="radar-card-description">
                Ligações disponíveis para revisão
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"""
        <div class="radar-card radar-green">
            <div class="radar-card-title">
                🟢 Sem alerta
            </div>
            <div class="radar-card-number">
                {total_sem_alerta}
            </div>
            <div class="radar-card-description">
                Nenhum critério de alerta identificado
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    f"""
    <div style="
        margin-top: 18px;
        padding: 12px 18px;
        background: #F3F6FA;
        border-radius: 10px;
        color: #374151;
        font-size: 14px;
    ">
        📞 <strong>{total_ligacoes}</strong> ligações analisadas no relatório
    </div>
    """,
    unsafe_allow_html=True
)
# ============================================================
# FILTROS
# ============================================================

st.divider()

filtro = st.selectbox(
    "🔎 O que você quer revisar?",
    [
        "Todas",
        "🔴 INVESTIGAÇÃO DE ATENDIMENTO",
        "🟡 INVESTIGAÇÃO DE DESCONEXÃO",
        "🔵 REVISÃO — NÃO TRANSFERIDA"
    ]
)


if filtro == "Todas":

    exibicao = df_alertas.copy()

else:

    exibicao = df_alertas[
        df_alertas["RADAR_STATUS"]
        == filtro
    ].copy()


# ============================================================
# TABELA
# ============================================================

if len(exibicao) > 0:

    st.subheader(
        f"📋 {len(exibicao)} ligações"
    )


    colunas_tabela = []


    if col_usuario:

        colunas_tabela.append(
            col_usuario
        )


    if col_data:

        colunas_tabela.append(
            col_data
        )


    if col_duracao:

        colunas_tabela.append(
            col_duracao
        )


    colunas_tabela.append(
        col_transferidas
    )


    colunas_tabela.append(
        col_desconexao
    )


    if col_finalizacao:

        colunas_tabela.append(
            col_finalizacao
        )


    colunas_tabela.append(
        col_resultados
    )


    colunas_tabela.extend(
        [
            "RADAR_STATUS",
            "RADAR_MOTIVO"
        ]
    )


    colunas_tabela = list(
        dict.fromkeys(
            colunas_tabela
        )
    )


    st.dataframe(
        exibicao[
            colunas_tabela
        ],
        use_container_width=True,
        hide_index=True
    )


else:

    st.success(
        "🎉 Nenhuma ligação encontrada neste filtro."
    )


# ============================================================
# SELEÇÃO
# ============================================================

if len(exibicao) == 0:

    st.stop()


st.divider()

st.header(
    "🔎 3. Selecione uma ligação"
)


indices = list(
    exibicao.index
)


def nome_ligacao(indice):

    linha = df.loc[
        indice
    ]


    partes = []


    if col_usuario:

        partes.append(
            str(
                linha[col_usuario]
            )
        )


    if col_data:

        partes.append(
            str(
                linha[col_data]
            )
        )


    if col_duracao:

        partes.append(
            str(
                linha[col_duracao]
            )
        )


    partes.append(
        str(
            linha["RADAR_STATUS"]
        )
    )


    return " | ".join(
        partes
    )


selecionada = st.selectbox(
    "Escolha a ligação que deseja revisar:",
    indices,
    format_func=nome_ligacao
)


ligacao = df.loc[
    selecionada
]


# ============================================================
# DADOS DA LIGAÇÃO
# ============================================================

st.subheader(
    "📋 Dados da ligação"
)


c1, c2 = st.columns(2)


with c1:

    if col_usuario:

        st.write(
            f"**Colaborador:** "
            f"{ligacao[col_usuario]}"
        )


    if col_data:

        st.write(
            f"**Data:** "
            f"{ligacao[col_data]}"
        )


    if col_duracao:

        st.write(
            f"**Duração:** "
            f"{ligacao[col_duracao]}"
        )


with c2:

    st.write(
        f"**Transferidas:** "
        f"{ligacao[col_transferidas]}"
    )


    st.write(
        f"**Tipo de desconexão:** "
        f"{ligacao[col_desconexao]}"
    )


    if col_finalizacao:

        st.write(
            f"**Finalização:** "
            f"{ligacao[col_finalizacao]}"
        )


st.write(
    f"**Resultados com êxito:** "
    f"{ligacao[col_resultados]}"
)


st.warning(
    f"🔎 **Motivo da revisão:** "
    f"{ligacao['RADAR_MOTIVO']}"
)


# ============================================================
# ANÁLISE DA LIGAÇÃO
# ============================================================

st.divider()

st.header(
    "🎧 4. Conteúdo da ligação"
)


tipo = ligacao[
    "RADAR_TIPO"
]


if tipo == "desconexao":

    st.info(
        "🟡 **Investigação de desconexão**\n\n"
        "A IA deverá investigar o contexto do encerramento "
        "da ligação e procurar evidências de possível "
        "interrupção/desconexão."
    )


elif tipo == "atendimento":

    st.info(
        "🔴 **Investigação de atendimento**\n\n"
        "A IA deverá investigar por que o cliente avaliou "
        "o atendimento negativamente."
    )


elif tipo == "revisao":

    st.info(
        "🔵 **Revisão de ligação não transferida**\n\n"
        "A não transferência não significa que houve erro. "
        "A ligação está disponível para revisão."
    )


# ============================================================
# ÁUDIO
# ============================================================

audio = st.file_uploader(
    "🎧 Anexar gravação",
    type=[
        "mp3",
        "wav",
        "m4a"
    ],
    key=f"audio_{selecionada}"
)


# ============================================================
# TRANSCRIÇÃO
# ============================================================

transcricao = st.text_area(
    "📝 Colar transcrição",
    height=300,
    placeholder=(
        "Cole aqui a transcrição da ligação..."
    ),
    key=f"transcricao_{selecionada}"
)


# ============================================================
# BOTÃO IA
# ============================================================

if audio or transcricao.strip():

    st.success(
        "✅ Conteúdo da ligação carregado."
    )


    if st.button(
        "🧠 ANALISAR COM IA",
        type="primary",
        use_container_width=True
    ):

        prompt = """
        Você é o RADAR IA, responsável por auxiliar na auditoria de qualidade
        de ligações de atendimento.

        Analise cuidadosamente o conteúdo da ligação fornecido abaixo.

        IMPORTANTE:
        - Não invente informações.
        - Não presuma que algo aconteceu se não houver evidência.
        - Diferencie claramente fato observado de interpretação.
        - Quando não houver informação suficiente, diga "Não foi possível identificar".
        - Use trechos e acontecimentos da conversa como evidência.
        - Não faça julgamento baseado apenas no resultado final da ligação.

        OBJETIVOS DA ANÁLISE:

        1. IDENTIFICAÇÃO DO CONTEXTO
        - Qual era o motivo do contato?
        - O que o cliente queria?
        - Qual foi a demanda apresentada?

        2. CONDUTA DO AGENTE
        - Demonstrou cordialidade?
        - Demonstrou empatia?
        - Demonstrou irritação, impaciência ou grosseria?
        - Interrompeu o cliente de maneira inadequada?
        - Deixou de responder alguma questão importante?
        - A comunicação foi clara?

        3. EXPERIÊNCIA DO CLIENTE
        - O cliente demonstrou insatisfação?
        - Houve frustração?
        - Houve conflito ou discussão?
        - O cliente discordou da orientação recebida?
        - O cliente ameaçou escalar a situação para Luiza Helena,
        diretoria, Procon, Reclame Aqui, esfera cível ou consumidor.gov?

        4. ORIENTAÇÃO
        - O agente explicou alguma orientação ou procedimento?
        - A orientação foi compreensível?
        - Houve alguma promessa ou tratativa adicional?
        Exemplos:
        - cupom;
        - resgate;
        - qualquer outra tratativa especial.

        5. ENCERRAMENTO
        - A ligação terminou normalmente?
        - Terminou abruptamente?
        - Havia uma orientação em andamento quando a conversa terminou?
        - O agente pediu para o cliente aguardar?
        - Quem estava falando por último?
        - Houve despedida ou encerramento normal?
        - Há evidência de possível desconexão?

        AO FINAL, ORGANIZE A RESPOSTA EM:

        ### 🔎 Resumo da ligação

        ### 🗣️ Conduta do agente

        ### 😡 Experiência do cliente

        ### 📚 Orientação realizada

        ### 🎁 Promessa ou tratativa adicional

        ### 📞 Encerramento da ligação

        ### ⚠️ Pontos de atenção

        ### 🧠 Conclusão da análise

        Na conclusão, indique somente o que pode ser sustentado
        pelas evidências encontradas na ligação.
        """

            

            


        resultado_ia = analisar_com_gemini(
            prompt=prompt,
            transcricao=transcricao,
            audio=audio
        )

        st.divider()

        st.subheader("🧠 Resultado da análise por IA")

        st.markdown(resultado_ia)
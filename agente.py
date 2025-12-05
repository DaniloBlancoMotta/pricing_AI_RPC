#!/usr/bin/env python3
"""
Validador Ontológico de Precificação (Academias)
Implementa um agente LangGraph para validar a estratégia de precificação.
"""

import argparse
import json
import logging
import operator
import os
import sys
from typing import Dict, List, Annotated, TypedDict, Any, Optional, Literal
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ValidadorPricing")

class RegraValidacao(BaseModel):
    """Define uma regra de validação de negócio com descrição e limite."""
    nome: str
    descricao: str
    limite: float = 0.0

class Ontologia(BaseModel):
    """Estrutura principal da ontologia para validação de pricing."""
    versao: str
    regras: Dict[str, RegraValidacao]
    
def carregar_ontologia() -> Ontologia:
    """Carrega a ontologia do arquivo JSON ou usa fallback hardcoded."""
    arquivo_regras = "regras.json"
    
    if os.path.exists(arquivo_regras):
        try:
            logger.info(f"📂 Carregando regras de '{arquivo_regras}'...")
            with open(arquivo_regras, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return Ontologia(**dados)
        except Exception as e:
            logger.error(f"❌ Erro ao ler {arquivo_regras}: {e}. Usando fallback.")
    
    logger.warning("⚠️ Usando Ontologia Hardcoded (Fallback).")
    return Ontologia(
        versao="1.1.0-Fallback",
        regras={
            "regra_custo_minimo": RegraValidacao(
                nome="Regra 1: Custo Mínimo (Passo 1)",
                descricao="O preço mais baixo ofertado deve ser maior ou igual ao Custo de Aquisição (CAC).",
                limite=1.0
            ),
            "regra_acessibilidade_rpc": RegraValidacao(
                nome="Regra 4: Acessibilidade RPC (Passo 4)",
                descricao="O Preço Mensal não deve exceder 5% da Renda Per Capita Mínima da área.",
                limite=0.05
            ),
        }
    )

class Estado(TypedDict):
    """
    Estado compartilhado.
    Usa Annotated[List, operator.add] para permitir que nós paralelos
    escrevam nas listas sem sobrescrever uns aos outros (append).
    """
    ontologia: Ontologia
    
    # Inputs
    custo_unitario_cac: float
    preco_segmento_minimo: float
    renda_per_capita_min: float
    
    # Resultados (Reducers para paralelismo)
    violacoes: Annotated[List[str], operator.add]
    alertas: Annotated[List[str], operator.add]
    
    relatorio: str
    feedback_llm: str

def carregar_dados_node(state: Estado) -> Estado:
    """Nó inicial: Carrega ontologia e prepara o terreno."""
    logger.info("🔄 [Nó] Carregando Ontologia...")
    
    # Apenas carrega a ontologia, os dados numéricos já vieram do input inicial (main)
    ontologia = carregar_ontologia()
    
    logger.info(f"✅ Dados em Análise: Preço R${state['preco_segmento_minimo']:.2f}, "
                f"CAC R${state['custo_unitario_cac']:.2f}, "
                f"RPC R${state['renda_per_capita_min']:.2f}")
    
    return {"ontologia": ontologia}

def validar_regra_1_node(state: Estado) -> Estado:
    """Valida se Preço >= CAC."""
    logger.info("🔄 [Nó] Validando Regra 1 (Custo)...")
    
    regra = state["ontologia"].regras.get("regra_custo_minimo")
    if not regra:
        return {}

    violacoes = []
    if state["preco_segmento_minimo"] < state["custo_unitario_cac"] * regra.limite:
        msg = (f"[R1 FALHA] Preço R${state['preco_segmento_minimo']:.2f} < "
               f"CAC R${state['custo_unitario_cac']:.2f}.")
        violacoes.append(msg)
        logger.error(f"  ❌ {msg}")
    else:
        logger.info("  ✅ Regra 1 OK.")
        
    return {"violacoes": violacoes}

def validar_regra_4_node(state: Estado) -> Estado:
    """Valida se Preço <= 5% da RPC."""
    logger.info("🔄 [Nó] Validando Regra 4 (Acessibilidade)...")
    
    regra = state["ontologia"].regras.get("regra_acessibilidade_rpc")
    if not regra:
        return {}

    alertas = []
    preco_max = state["renda_per_capita_min"] * regra.limite
    
    if state["preco_segmento_minimo"] > preco_max:
        msg = (f"[R4 ALERTA] Preço R${state['preco_segmento_minimo']:.2f} excede "
               f"limite de acessibilidade (R${preco_max:.2f}).")
        alertas.append(msg)
        logger.warning(f"  ⚠️ {msg}")
    else:
        logger.info("  ✅ Regra 4 OK.")
        
    return {"alertas": alertas}

def verificar_bloqueios_node(state: Estado) -> Estado:
    """Nó de sincronização (Join) para decidir o próximo passo."""
    return {}

def validar_taticas_node(state: Estado) -> Estado:
    """Valida táticas de desconto (só roda se não houver violações críticas)."""
    logger.info("🔄 [Nó] Validando Táticas (Marca Premium)...")
    
    alertas = []
    # Exemplo: Preço muito próximo do custo pode ser ruim para marca premium
    if state["preco_segmento_minimo"] < state["custo_unitario_cac"] * 1.2:
        msg = "[TÁTICA] Margem baixa pode diluir percepção de valor Premium."
        alertas.append(msg)
        logger.warning(f"  ⚠️ {msg}")
    else:
        logger.info("  ✅ Táticas OK.")
        
    return {"alertas": alertas}

def gerar_relatorio_node(state: Estado) -> Estado:
    """Gera o relatório final."""
    logger.info("🔄 [Nó] Gerando Relatório Final...")
    
    lines = []
    lines.append("=" * 60)
    lines.append(f"RELATÓRIO DE PRECIFICAÇÃO - {state['ontologia'].versao}")
    lines.append("=" * 60)
    
    if state["violacoes"]:
        lines.append("❌ VIOLAÇÕES CRÍTICAS (IMPEDEM O LANÇAMENTO):")
        for v in state["violacoes"]:
            lines.append(f" - {v}")
    else:
        lines.append("✅ Nenhuma violação crítica detectada.")
        
    lines.append("-" * 60)
    
    if state["alertas"]:
        lines.append("⚠️ PONTOS DE ATENÇÃO:")
        for a in state["alertas"]:
            lines.append(f" - {a}")
    else:
        lines.append("ℹ️ Nenhum alerta tático.")
        
    lines.append("=" * 60)
    
    relatorio_texto = "\n".join(lines)
    return {"relatorio": relatorio_texto}

def gerar_feedback_llm_node(state: Estado) -> Estado:
    """Usa a API Groq para gerar um feedback humanizado."""
    logger.info("🤖 [Nó] Gerando Feedback com IA (Groq)...")
    
    # Configuração da API Key via variável de ambiente
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        logger.error("❌ ERRO: Variável de ambiente GROQ_API_KEY não encontrada.")
        return {"feedback_llm": "Erro de configuração: API Key não encontrada."}

    try:
        llm = ChatGroq(
            temperature=0.7, 
            model_name="llama-3.3-70b-versatile", 
            api_key=api_key
        )
        
        prompt_sistema = """
        Você é um consultor sênior de estratégia de precificação para academias.
        Sua tarefa é analisar o relatório técnico abaixo e escrever uma carta 
        profissional e direta para o dono da academia.
        
        Se houver violações críticas, seja firme mas educado sobre a inviabilidade.
        Se houver apenas alertas, sugira melhorias.
        Se estiver tudo certo, parabenize pela estratégia sólida.
        
        Use formatação Markdown. Seja conciso.
        """
        
        prompt_usuario = f"""
        Aqui está o relatório técnico da validação:
        
        {state['relatorio']}
        
        Dados de Contexto:
        - CAC: R${state['custo_unitario_cac']:.2f}
        - Preço Proposto: R${state['preco_segmento_minimo']:.2f}
        - RPC da Região: R${state['renda_per_capita_min']:.2f}
        """
        
        mensagens = [
            SystemMessage(content=prompt_sistema),
            HumanMessage(content=prompt_usuario)
        ]
        
        resposta = llm.invoke(mensagens)
        return {"feedback_llm": resposta.content}
        
    except Exception as e:
        logger.error(f"❌ Erro na chamada da LLM: {e}")
        return {"feedback_llm": "Não foi possível gerar o feedback da IA no momento."}

def roteador_critico(state: Estado) -> Literal["validar_taticas", "gerar_relatorio"]:
    """
    Decide se avança para validação de táticas ou aborta para o relatório.
    Se houver violações nas regras fundamentais (1 ou 4), pula as táticas.
    """
    if state["violacoes"]:
        logger.warning("⛔ Violações críticas detectadas. Pulando análise tática.")
        return "gerar_relatorio"
    return "validar_taticas"

def criar_grafo():
    builder = StateGraph(Estado)
    
    # Adicionar Nós
    builder.add_node("coletar_dados", carregar_dados_node)
    builder.add_node("validar_regra_1", validar_regra_1_node)
    builder.add_node("validar_regra_4", validar_regra_4_node)
    builder.add_node("verificar_bloqueios", verificar_bloqueios_node)
    builder.add_node("validar_taticas", validar_taticas_node)
    builder.add_node("gerar_relatorio", gerar_relatorio_node)
    builder.add_node("gerar_feedback_llm", gerar_feedback_llm_node)
    
    # Arestas
    builder.add_edge(START, "coletar_dados")
    
    # Paralelismo (Fan-out)
    builder.add_edge("coletar_dados", "validar_regra_1")
    builder.add_edge("coletar_dados", "validar_regra_4")
    
    # Sincronização (Fan-in)
    builder.add_edge("validar_regra_1", "verificar_bloqueios")
    builder.add_edge("validar_regra_4", "verificar_bloqueios")
    
    # Roteamento Condicional
    builder.add_conditional_edges(
        "verificar_bloqueios",
        roteador_critico
    )
    
    builder.add_edge("validar_taticas", "gerar_relatorio")
    builder.add_edge("gerar_relatorio", "gerar_feedback_llm")
    builder.add_edge("gerar_feedback_llm", END)
    
    return builder.compile()

def main():
    parser = argparse.ArgumentParser(description="Validador de Precificação (LangGraph)")
    parser.add_argument("--cac", type=float, default=100.0, help="Custo de Aquisição (CAC)")
    parser.add_argument("--preco", type=float, default=99.0, help="Preço Mínimo do Segmento")
    parser.add_argument("--rpc", type=float, default=3800.0, help="Renda Per Capita Mínima")
    
    args = parser.parse_args()
    
    print("\n🚀 Iniciando Agente de Precificação...")
    
    grafo = criar_grafo()
    
    # Estado Inicial
    inputs = {
        "custo_unitario_cac": args.cac,
        "preco_segmento_minimo": args.preco,
        "renda_per_capita_min": args.rpc,
        "violacoes": [],
        "alertas": [],
        "relatorio": "",
        "feedback_llm": ""
    }
    
    thread = {"configurable": {"thread_id": "1"}}
    
    # Execução
    final_state = grafo.invoke(inputs, config=thread)
    
    print("\n" + final_state["relatorio"])
    print("\n📝 FEEDBACK DO CONSULTOR IA (GROQ):")
    print("-" * 60)
    print(final_state["feedback_llm"])
    print("-" * 60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# run.py
"""
Runner genérico para múltiplos portais.

Lê clientes de um CSV e executa o script correto de cada portal.

Uso:
    python run.py                         # Roda todos do CSV
    python run.py --csv meu_arquivo.csv   # Usa outro CSV
    python run.py --portal equatorial_go  # Filtra por portal
    python run.py --id cliente_001        # Roda cliente específico
    python run.py --proxy                 # Usa proxies gratuitos
    python run.py --headless              # Sem janela do browser

Estrutura esperada do CSV:
    - Coluna 'portal': nome do portal (ex: equatorial_go, cemig, enel)
    - Coluna 'id': identificador único do cliente (opcional)
    - Demais colunas: dados de acesso conforme mapeamento em portais.json
"""

import csv
import json
import sys
import time
import random
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Importa do módulo local (mesma pasta)
try:
    from runner import HumanRunner
    from logger import HumanBrowserLogger
except ImportError:
    try:
        from human_browser.runner import HumanRunner
        from human_browser.logger import HumanBrowserLogger
    except ImportError:
        from .runner import HumanRunner
        from .logger import HumanBrowserLogger


# =============================================================================
# CONFIGURAÇÕES PADRÃO
# =============================================================================

CSV_FILE = "clientes.csv"
PORTAIS_FILE = "portais.json"
DOWNLOAD_DIR = "./faturas"


# =============================================================================
# FUNÇÕES
# =============================================================================

def carregar_portais(filepath: str = PORTAIS_FILE) -> Dict:
    """Carrega configuração dos portais."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"❌ Arquivo de portais não encontrado: {filepath}")
        sys.exit(1)
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def carregar_csv(filepath: str, encoding: str = 'utf-8') -> List[Dict]:
    """
    Carrega clientes do CSV.
    
    Tenta diferentes encodings se o padrão falhar.
    Remove espaços extras dos nomes das colunas e valores.
    """
    path = Path(filepath)
    
    if not path.exists():
        print(f"❌ Arquivo CSV não encontrado: {filepath}")
        sys.exit(1)
    
    # Tenta diferentes encodings comuns em CSVs brasileiros
    encodings = [encoding, 'utf-8-sig', 'latin-1', 'cp1252']
    
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                # Detecta o delimitador
                sample = f.read(1024)
                f.seek(0)
                
                if ';' in sample and ',' not in sample:
                    delimiter = ';'
                elif '\t' in sample:
                    delimiter = '\t'
                else:
                    delimiter = ','
                
                reader = csv.DictReader(f, delimiter=delimiter)
                clientes_raw = list(reader)
                
                # Limpa os dados: remove espaços extras e colunas vazias
                clientes = []
                for cliente in clientes_raw:
                    cliente_limpo = {}
                    for key, value in cliente.items():
                        # Remove espaços do nome da coluna
                        key_limpo = key.strip() if key else ""
                        
                        # Ignora colunas sem nome
                        if not key_limpo:
                            continue
                        
                        # Remove espaços do valor
                        value_limpo = value.strip() if value else ""
                        
                        cliente_limpo[key_limpo] = value_limpo
                    
                    clientes.append(cliente_limpo)
                
                print(f"✓ {len(clientes)} clientes carregados de {filepath}")
                print(f"  Encoding: {enc}, Delimitador: '{delimiter}'")
                
                # Mostra colunas detectadas
                if clientes:
                    colunas = list(clientes[0].keys())
                    print(f"  Colunas: {', '.join(colunas)}")
                
                return clientes
                
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"⚠ Erro com encoding {enc}: {e}")
            continue
    
    print(f"❌ Não foi possível ler o CSV com nenhum encoding")
    sys.exit(1)


def mapear_cliente(cliente: Dict, portal_config: Dict) -> Dict:
    """
    Mapeia colunas do CSV para variáveis do script.
    
    DETECÇÃO AUTOMÁTICA: Se um campo está preenchido no CSV,
    ele é considerado necessário e será passado para o script.
    
    O mapeamento em portais.json serve para:
    1. Renomear colunas (CSV tem "uc" mas script espera "unidade_consumidora")
    2. Definir valores padrão
    
    Exemplo:
        CSV: {"Email": "teste@x.com", "Senha": "123", "cpf": ""}
        → Resultado: {"email": "teste@x.com", "senha": "123"}
        (cpf ignorado pois está vazio)
    """
    mapeamento = portal_config.get("campos", {})
    padrao = portal_config.get("campos_padrao", {})
    
    resultado = {}
    
    # 1. Aplica mapeamento definido em portais.json
    for var_script, coluna_csv in mapeamento.items():
        valor = None
        
        # Busca pelo nome da coluna (case-insensitive)
        for key in cliente.keys():
            if key.lower() == coluna_csv.lower():
                valor = cliente[key]
                break
        
        # Se não encontrou pelo mapeamento, busca pelo nome da variável
        if valor is None:
            for key in cliente.keys():
                if key.lower() == var_script.lower():
                    valor = cliente[key]
                    break
        
        # Se ainda não encontrou, usa valor padrão
        if valor is None and var_script in padrao:
            valor = padrao[var_script]
        
        # Só adiciona se tiver valor (não vazio)
        if valor is not None and str(valor).strip():
            resultado[var_script] = valor
    
    # 2. Adiciona campos extras do CSV que não estão no mapeamento
    #    (desde que estejam preenchidos e não sejam 'portal' ou 'id')
    campos_ignorar = {'portal', 'id', 'ID'}
    
    for key, value in cliente.items():
        # Ignora campos de controle
        if key.lower() in [c.lower() for c in campos_ignorar]:
            continue
        
        # Ignora se já foi mapeado
        ja_mapeado = False
        for var_script, coluna_csv in mapeamento.items():
            if key.lower() == coluna_csv.lower() or key.lower() == var_script.lower():
                ja_mapeado = True
                break
        
        if ja_mapeado:
            continue
        
        # Adiciona se estiver preenchido
        if value is not None and str(value).strip():
            # Converte nome da coluna para snake_case
            var_name = key.lower().replace(' ', '_')
            resultado[var_name] = value
    
    # Mantém id para referência
    cliente_id = cliente.get('id') or cliente.get('ID')
    if cliente_id:
        resultado['_cliente_id'] = cliente_id
    
    return resultado


def detectar_campos_preenchidos(cliente: Dict) -> List[str]:
    """
    Detecta quais campos estão preenchidos para este cliente.
    Útil para debug e logging.
    """
    campos = []
    for key, value in cliente.items():
        if key.lower() in ['id', 'portal']:
            continue
        if value is not None and str(value).strip():
            campos.append(key)
    return campos


def agrupar_por_portal(clientes: List[Dict]) -> Dict[str, List[Dict]]:
    """Agrupa clientes por portal."""
    grupos = defaultdict(list)
    
    for cliente in clientes:
        # Busca coluna portal (case-insensitive)
        portal = None
        for key in cliente.keys():
            if key.lower() == 'portal':
                portal = cliente[key].lower()  # Normaliza para minúsculo
                break
        
        if not portal:
            portal = 'default'
        
        grupos[portal].append(cliente)
    
    return dict(grupos)


def executar_portal(
    runner: HumanRunner,
    portal_id: str,
    portal_config: Dict,
    clientes: List[Dict]
) -> List[Dict]:
    """
    Executa scripts para todos os clientes de um portal.
    
    Suporta múltiplos scripts por portal. Para cada cliente:
    1. Tenta o primeiro script
    2. Se falhar, tenta o segundo
    3. Se falhar, tenta o terceiro
    4. Só depois passa para o próximo cliente
    """
    
    # Suporta tanto "script" (string) quanto "scripts" (array)
    scripts = portal_config.get("scripts", [])
    if not scripts:
        # Fallback para formato antigo
        script_unico = portal_config.get("script")
        if script_unico:
            scripts = [script_unico]
    
    warmup = portal_config.get("warmup_url")
    nome = portal_config.get("nome", portal_id)
    
    # Verifica quais scripts existem
    scripts_existentes = []
    for s in scripts:
        if Path(s).exists():
            scripts_existentes.append(s)
        else:
            print(f"⚠️  Script não encontrado, ignorando: {s}")
    
    if not scripts_existentes:
        print(f"❌ Nenhum script válido encontrado para {nome}")
        return [{"success": False, "error": "Nenhum script válido"}] * len(clientes)
    
    # Mapeia clientes
    clientes_mapeados = [mapear_cliente(c, portal_config) for c in clientes]
    
    print(f"\n{'='*60}")
    print(f"🏢 Portal: {nome}")
    print(f"📄 Scripts disponíveis: {len(scripts_existentes)}")
    for i, s in enumerate(scripts_existentes, 1):
        print(f"   {i}. {Path(s).name}")
    print(f"👥 Clientes: {len(clientes_mapeados)}")
    print(f"{'='*60}")
    
    # Executa com fallback de scripts
    return runner.run_for_multiple(
        scripts=scripts_existentes,
        variables_list=clientes_mapeados,
        warmup_url=warmup,
        delay_between=3.0
    )


def main():
    parser = argparse.ArgumentParser(
        description="Runner genérico para múltiplos portais de energia"
    )
    parser.add_argument(
        "--csv", "-f",
        type=str,
        default=CSV_FILE,
        help=f"Arquivo CSV com clientes (padrão: {CSV_FILE})"
    )
    parser.add_argument(
        "--portais", "-P",
        type=str,
        default=PORTAIS_FILE,
        help=f"Arquivo JSON com configuração dos portais (padrão: {PORTAIS_FILE})"
    )
    parser.add_argument(
        "--portal", "-p",
        type=str,
        default=None,
        help="Filtrar por portal específico (ex: equatorial_go)"
    )
    parser.add_argument(
        "--id", "-i",
        type=str,
        default=None,
        help="Executar cliente específico por ID"
    )
    parser.add_argument(
        "--proxy",
        action="store_true",
        help="Usar proxies gratuitos"
    )
    parser.add_argument(
        "--headless", "-H",
        action="store_true",
        help="Rodar sem abrir janela do browser"
    )
    parser.add_argument(
        "--download-dir", "-d",
        type=str,
        default=DOWNLOAD_DIR,
        help=f"Diretório para downloads (padrão: {DOWNLOAD_DIR})"
    )
    parser.add_argument(
        "--listar-portais",
        action="store_true",
        help="Lista portais configurados e sai"
    )
    parser.add_argument(
        "--listar-clientes",
        action="store_true",
        help="Lista clientes do CSV e sai"
    )
    
    args = parser.parse_args()
    
    # Carrega configurações
    portais = carregar_portais(args.portais)
    
    # Listar portais
    if args.listar_portais:
        print("\n📋 Portais configurados:")
        for pid, pconfig in portais.items():
            nome = pconfig.get("nome", pid)
            scripts = pconfig.get("scripts", [pconfig.get("script", "?")])
            print(f"  • {pid}: {nome}")
            for s in scripts:
                existe = "✓" if Path(s).exists() else "❌"
                print(f"      {existe} {s}")
        return
    
    # Carrega clientes
    clientes = carregar_csv(args.csv)
    
    # Listar clientes
    if args.listar_clientes:
        print("\n📋 Clientes no CSV:")
        for i, c in enumerate(clientes):
            cid = c.get('id') or c.get('ID') or f'linha_{i}'
            portal = None
            for k in c.keys():
                if k.lower() == 'portal':
                    portal = c[k]
                    break
            print(f"  [{i+1}] {cid} - Portal: {portal or '?'}")
        return
    
    # Filtra por portal (se especificado)
    if args.portal:
        portal_filtro = args.portal.lower()
        clientes = [c for c in clientes if any(
            k.lower() == 'portal' and c[k].lower() == portal_filtro 
            for k in c.keys()
        )]
        if not clientes:
            print(f"❌ Nenhum cliente encontrado para portal: {args.portal}")
            return
        print(f"→ Filtrado para portal: {args.portal} ({len(clientes)} clientes)")
    
    # Filtra por ID (se especificado)
    if args.id:
        clientes = [c for c in clientes if c.get('id') == args.id or c.get('ID') == args.id]
        if not clientes:
            print(f"❌ Cliente não encontrado: {args.id}")
            return
        print(f"→ Executando apenas: {args.id}")
    
    # Configura runner
    runner = HumanRunner()
    runner.config.download_dir = args.download_dir
    runner.config.headless = args.headless
    runner.config.use_tls_warmup = True
    runner.config.max_retries = 2
    
    # Cria diretório de download
    Path(args.download_dir).mkdir(parents=True, exist_ok=True)
    
    # Inicializa logger
    logger = HumanBrowserLogger(log_dir="./logs")
    logger.start_execution()
    logger.set_total_clientes(len(clientes))
    
    # Configura proxy
    if args.proxy:
        logger.info("Buscando proxies gratuitos...")
        runner.setup_free_proxies(count=5, test_limit=50)
    
    # Conta portais para estatísticas
    contagem_portais = defaultdict(int)
    for c in clientes:
        for k in c.keys():
            if k.lower() == 'portal':
                contagem_portais[c[k].lower()] += 1
                break
    
    logger.info(f"Resumo: {len(clientes)} clientes em {len(contagem_portais)} portal(is)")
    for portal_id, count in contagem_portais.items():
        nome = portais.get(portal_id, {}).get("nome", portal_id)
        logger.info(f"Portal {nome}: {count} clientes")
    
    print(f"\n⚡ Modo: Processamento SEQUENCIAL (ordem do CSV)")
    print(f"   Isso distribui requisições entre portais diferentes")
    
    # =========================================================================
    # EXECUÇÃO LINHA POR LINHA (na ordem do CSV)
    # =========================================================================
    
    todos_resultados = []
    total = len(clientes)
    
    logger.info(f"Iniciando processamento de {total} clientes")
    print(f"\n{'='*60}")
    print(f"🚀 INICIANDO PROCESSAMENTO")
    print(f"{'='*60}")
    
    for i, cliente in enumerate(clientes, 1):
        # Identifica o portal desta linha
        portal_id = None
        for k in cliente.keys():
            if k.lower() == 'portal':
                portal_id = cliente[k].lower()
                break
        
        # Identifica o cliente
        cliente_id = cliente.get('id') or cliente.get('ID') or f'linha_{i}'
        
        # Detecta campos preenchidos
        campos_preenchidos = detectar_campos_preenchidos(cliente)
        
        print(f"\n{'#'*60}")
        print(f"👤 [{i}/{total}] Cliente: {cliente_id}")
        print(f"🏢 Portal: {portal_id or 'NÃO IDENTIFICADO'}")
        print(f"📝 Campos preenchidos: {', '.join(campos_preenchidos)}")
        print(f"{'#'*60}")
        
        logger.log_cliente_inicio(cliente_id, portal_id or "?", dict.fromkeys(campos_preenchidos))
        
        # Verifica se portal está configurado
        if not portal_id or portal_id not in portais:
            error_msg = f"Portal não configurado: {portal_id}"
            logger.log_cliente_erro(cliente_id, portal_id or "?", error_msg)
            print(f"❌ {error_msg}")
            print(f"  Adicione em {args.portais}")
            todos_resultados.append({
                "success": False,
                "error": error_msg,
                "portal": portal_id,
                "cliente_id": cliente_id
            })
            continue
        
        portal_config = portais[portal_id]
        
        # Obtém scripts do portal
        scripts = portal_config.get("scripts", [])
        if not scripts:
            script_unico = portal_config.get("script")
            if script_unico:
                scripts = [script_unico]
        
        # Filtra scripts que existem
        scripts_existentes = [s for s in scripts if Path(s).exists()]
        
        if not scripts_existentes:
            error_msg = f"Nenhum script válido encontrado"
            logger.log_cliente_erro(cliente_id, portal_id, error_msg)
            print(f"❌ {error_msg} para {portal_id}")
            todos_resultados.append({
                "success": False,
                "error": error_msg,
                "portal": portal_id,
                "cliente_id": cliente_id
            })
            continue
        
        # Mapeia variáveis do cliente (detecta automaticamente campos preenchidos)
        variaveis = mapear_cliente(cliente, portal_config)
        warmup_url = portal_config.get("warmup_url")
        
        # Remove _cliente_id das variáveis injetadas (é só referência)
        variaveis_para_script = {k: v for k, v in variaveis.items() if not k.startswith('_')}
        
        # Log dos campos que serão usados
        print(f"📋 Variáveis para o script:")
        for k, v in variaveis_para_script.items():
            if 'senha' in k.lower() or 'password' in k.lower():
                print(f"   • {k}: ****")
            else:
                print(f"   • {k}: {v}")
        
        # Executa com fallback de scripts
        resultado = runner.run_with_script_fallback(
            scripts=scripts_existentes,
            variables=variaveis_para_script,
            warmup_url=warmup_url
        )
        
        resultado["portal"] = portal_id
        resultado["cliente_id"] = cliente_id
        resultado["campos_usados"] = list(variaveis_para_script.keys())
        todos_resultados.append(resultado)
        
        # Log do resultado
        if resultado["success"]:
            script_usado = resultado.get("script_used", "?")
            duration = resultado.get("duration", 0)
            logger.log_cliente_sucesso(cliente_id, portal_id, script_usado, duration)
            print(f"\n✅ SUCESSO - {cliente_id} ({portal_id}) - Script: {script_usado}")
        else:
            error_msg = resultado.get("error", "Erro desconhecido")
            script_tried = resultado.get("script_tried", "?")
            logger.log_cliente_erro(cliente_id, portal_id, error_msg, script=script_tried)
            print(f"\n❌ FALHOU - {cliente_id} ({portal_id})")
        
        # Delay aleatório entre clientes (parece mais humano)
        if i < total:
            delay = random.uniform(2.0, 6.0)  # Entre 2 e 6 segundos
            print(f"\n⏳ Aguardando {delay:.1f}s antes do próximo cliente...")
            time
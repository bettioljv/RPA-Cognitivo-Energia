# human_browser/logger.py
"""
Sistema de logging para o HumanBrowser.

Gera logs em dois formatos:
1. JSON - para análise programática
2. Texto - para leitura humana

Estrutura de logs:
    logs/
    ├── 2025-01-20/
    │   ├── execucao_14-30-00.json      # Log completo em JSON
    │   ├── execucao_14-30-00.log       # Log legível
    │   ├── erros_14-30-00.log          # Apenas erros
    │   └── resumo_14-30-00.json        # Resumo da execução
    └── 2025-01-21/
        └── ...
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


@dataclass
class LogEntry:
    """Entrada de log individual."""
    timestamp: str
    level: str
    message: str
    cliente_id: Optional[str] = None
    portal: Optional[str] = None
    script: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_text(self) -> str:
        """Formata para log de texto legível."""
        parts = [f"[{self.timestamp}]", f"[{self.level}]"]
        
        if self.cliente_id:
            parts.append(f"[{self.cliente_id}]")
        if self.portal:
            parts.append(f"[{self.portal}]")
        
        parts.append(self.message)
        
        if self.error:
            parts.append(f"\n    ERRO: {self.error}")
        
        if self.duration:
            parts.append(f"({self.duration:.2f}s)")
        
        return " ".join(parts)


@dataclass
class ExecutionSummary:
    """Resumo de uma execução."""
    inicio: str
    fim: str = ""
    duracao_total: float = 0
    total_clientes: int = 0
    sucessos: int = 0
    falhas: int = 0
    erros_por_portal: Dict[str, int] = field(default_factory=dict)
    erros_por_tipo: Dict[str, int] = field(default_factory=dict)
    clientes_com_erro: List[Dict] = field(default_factory=list)
    scripts_mais_usados: Dict[str, int] = field(default_factory=dict)


class HumanBrowserLogger:
    """
    Logger centralizado para o HumanBrowser.
    
    Uso:
        logger = HumanBrowserLogger()
        logger.start_execution()
        
        logger.info("Iniciando processamento", cliente_id="001", portal="celesc")
        logger.success("Download concluído", cliente_id="001", duration=5.2)
        logger.error("Falha no login", cliente_id="002", error="Timeout")
        
        logger.end_execution()
    """
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.entries: List[LogEntry] = []
        self.summary: Optional[ExecutionSummary] = None
        self.execution_id: Optional[str] = None
        self.current_date_dir: Optional[Path] = None
        
        # Configurações
        self.console_output = True
        self.file_output = True
        
    def start_execution(self) -> str:
        """Inicia uma nova execução e cria estrutura de logs."""
        now = datetime.now()
        
        # Cria diretório por data
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        self.execution_id = f"execucao_{time_str}"
        
        self.current_date_dir = self.log_dir / date_str
        self.current_date_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializa resumo
        self.summary = ExecutionSummary(inicio=now.isoformat())
        self.entries = []
        
        self.info(f"Execução iniciada: {self.execution_id}")
        
        return self.execution_id
    
    def end_execution(self) -> Dict:
        """Finaliza execução e salva logs."""
        now = datetime.now()
        
        if self.summary:
            self.summary.fim = now.isoformat()
            inicio = datetime.fromisoformat(self.summary.inicio)
            self.summary.duracao_total = (now - inicio).total_seconds()
        
        self.info(f"Execução finalizada. Duração: {self.summary.duracao_total:.2f}s")
        
        # Salva arquivos
        if self.file_output and self.current_date_dir:
            self._save_json_log()
            self._save_text_log()
            self._save_error_log()
            self._save_summary()
        
        return self.get_summary()
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        cliente_id: Optional[str] = None,
        portal: Optional[str] = None,
        script: Optional[str] = None,
        duration: Optional[float] = None,
        error: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Registra uma entrada de log."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            message=message,
            cliente_id=cliente_id,
            portal=portal,
            script=script,
            duration=duration,
            error=error,
            details=details
        )
        
        self.entries.append(entry)
        
        # Atualiza estatísticas
        if self.summary:
            if level == LogLevel.ERROR:
                if portal:
                    self.summary.erros_por_portal[portal] = \
                        self.summary.erros_por_portal.get(portal, 0) + 1
                if error:
                    # Categoriza erro
                    error_type = self._categorize_error(error)
                    self.summary.erros_por_tipo[error_type] = \
                        self.summary.erros_por_tipo.get(error_type, 0) + 1
                if cliente_id:
                    self.summary.clientes_com_erro.append({
                        "cliente_id": cliente_id,
                        "portal": portal,
                        "error": error,
                        "timestamp": entry.timestamp
                    })
            
            if level == LogLevel.SUCCESS and script:
                self.summary.scripts_mais_usados[script] = \
                    self.summary.scripts_mais_usados.get(script, 0) + 1
        
        # Output no console
        if self.console_output:
            self._print_entry(entry)
    
    def _categorize_error(self, error: str) -> str:
        """Categoriza erro para estatísticas."""
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return "Timeout"
        elif "element" in error_lower and "not found" in error_lower:
            return "Elemento não encontrado"
        elif "login" in error_lower or "senha" in error_lower or "password" in error_lower:
            return "Falha de autenticação"
        elif "proxy" in error_lower:
            return "Erro de proxy"
        elif "connection" in error_lower or "network" in error_lower:
            return "Erro de conexão"
        elif "captcha" in error_lower:
            return "Captcha detectado"
        else:
            return "Outro"
    
    def _print_entry(self, entry: LogEntry):
        """Imprime entrada no console com cores."""
        colors = {
            "DEBUG": "\033[90m",     # Cinza
            "INFO": "\033[94m",      # Azul
            "WARNING": "\033[93m",   # Amarelo
            "ERROR": "\033[91m",     # Vermelho
            "SUCCESS": "\033[92m",   # Verde
        }
        reset = "\033[0m"
        
        color = colors.get(entry.level, "")
        print(f"{color}{entry.to_text()}{reset}")
    
    # Métodos de conveniência
    def debug(self, message: str, **kwargs):
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def success(self, message: str, **kwargs):
        self._log(LogLevel.SUCCESS, message, **kwargs)
    
    def log_cliente_inicio(self, cliente_id: str, portal: str, campos: Dict):
        """Log de início de processamento de cliente."""
        campos_str = ", ".join(campos.keys())
        self.info(
            f"Iniciando processamento",
            cliente_id=cliente_id,
            portal=portal,
            details={"campos": list(campos.keys())}
        )
    
    def log_cliente_sucesso(self, cliente_id: str, portal: str, script: str, duration: float):
        """Log de sucesso de cliente."""
        if self.summary:
            self.summary.sucessos += 1
        
        self.success(
            f"Download concluído",
            cliente_id=cliente_id,
            portal=portal,
            script=script,
            duration=duration
        )
    
    def log_cliente_erro(self, cliente_id: str, portal: str, error: str, script: Optional[str] = None):
        """Log de erro de cliente."""
        if self.summary:
            self.summary.falhas += 1
        
        self.error(
            f"Falha no processamento",
            cliente_id=cliente_id,
            portal=portal,
            script=script,
            error=error
        )
    
    def log_script_tentativa(self, cliente_id: str, portal: str, script: str, tentativa: int, total: int):
        """Log de tentativa de script."""
        self.info(
            f"Tentando script {tentativa}/{total}: {script}",
            cliente_id=cliente_id,
            portal=portal,
            script=script
        )
    
    def set_total_clientes(self, total: int):
        """Define total de clientes para estatísticas."""
        if self.summary:
            self.summary.total_clientes = total
    
    # Salvamento de arquivos
    def _save_json_log(self):
        """Salva log completo em JSON."""
        filepath = self.current_date_dir / f"{self.execution_id}.json"
        
        data = {
            "execution_id": self.execution_id,
            "summary": asdict(self.summary) if self.summary else {},
            "entries": [e.to_dict() for e in self.entries]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Log JSON salvo: {filepath}")
    
    def _save_text_log(self):
        """Salva log em formato texto legível."""
        filepath = self.current_date_dir / f"{self.execution_id}.log"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"=" * 70 + "\n")
            f.write(f"EXECUÇÃO: {self.execution_id}\n")
            f.write(f"INÍCIO: {self.summary.inicio if self.summary else 'N/A'}\n")
            f.write(f"=" * 70 + "\n\n")
            
            for entry in self.entries:
                f.write(entry.to_text() + "\n")
            
            f.write(f"\n" + "=" * 70 + "\n")
            f.write(f"FIM DA EXECUÇÃO\n")
            f.write(f"=" * 70 + "\n")
        
        print(f"📄 Log texto salvo: {filepath}")
    
    def _save_error_log(self):
        """Salva apenas erros em arquivo separado."""
        error_entries = [e for e in self.entries if e.level == "ERROR"]
        
        if not error_entries:
            return
        
        filepath = self.current_date_dir / f"erros_{self.execution_id.replace('execucao_', '')}.log"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"ERROS DA EXECUÇÃO: {self.execution_id}\n")
            f.write(f"Total de erros: {len(error_entries)}\n")
            f.write("=" * 70 + "\n\n")
            
            for entry in error_entries:
                f.write(f"Cliente: {entry.cliente_id or 'N/A'}\n")
                f.write(f"Portal: {entry.portal or 'N/A'}\n")
                f.write(f"Script: {entry.script or 'N/A'}\n")
                f.write(f"Timestamp: {entry.timestamp}\n")
                f.write(f"Mensagem: {entry.message}\n")
                f.write(f"Erro: {entry.error or 'N/A'}\n")
                f.write("-" * 40 + "\n\n")
        
        print(f"📄 Log de erros salvo: {filepath}")
    
    def _save_summary(self):
        """Salva resumo da execução."""
        if not self.summary:
            return
        
        filepath = self.current_date_dir / f"resumo_{self.execution_id.replace('execucao_', '')}.json"
        
        summary_data = asdict(self.summary)
        summary_data["taxa_sucesso"] = f"{100 * self.summary.sucessos / max(1, self.summary.total_clientes):.1f}%"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Resumo salvo: {filepath}")
    
    def get_summary(self) -> Dict:
        """Retorna resumo da execução."""
        if not self.summary:
            return {}
        
        return {
            **asdict(self.summary),
            "taxa_sucesso": f"{100 * self.summary.sucessos / max(1, self.summary.total_clientes):.1f}%"
        }
    
    def print_summary(self):
        """Imprime resumo no console."""
        if not self.summary:
            return
        
        s = self.summary
        
        print(f"\n{'='*60}")
        print("📊 RESUMO DA EXECUÇÃO")
        print(f"{'='*60}")
        print(f"⏱  Duração total: {s.duracao_total:.2f}s")
        print(f"👥 Total clientes: {s.total_clientes}")
        print(f"✅ Sucessos: {s.sucessos}")
        print(f"❌ Falhas: {s.falhas}")
        print(f"📈 Taxa de sucesso: {100 * s.sucessos / max(1, s.total_clientes):.1f}%")
        
        if s.erros_por_portal:
            print(f"\n❌ Erros por portal:")
            for portal, count in sorted(s.erros_por_portal.items(), key=lambda x: -x[1]):
                print(f"   • {portal}: {count}")
        
        if s.erros_por_tipo:
            print(f"\n❌ Erros por tipo:")
            for tipo, count in sorted(s.erros_por_tipo.items(), key=lambda x: -x[1]):
                print(f"   • {tipo}: {count}")
        
        if s.scripts_mais_usados:
            print(f"\n📄 Scripts que funcionaram:")
            for script, count in sorted(s.scripts_mais_usados.items(), key=lambda x: -x[1]):
                print(f"   • {script}: {count} vezes")
        
        print(f"{'='*60}")


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def listar_logs(log_dir: str = "./logs", dias: int = 7) -> List[Dict]:
    """Lista logs dos últimos N dias."""
    log_path = Path(log_dir)
    logs = []
    
    if not log_path.exists():
        return logs
    
    for date_dir in sorted(log_path.iterdir(), reverse=True)[:dias]:
        if date_dir.is_dir():
            for log_file in date_dir.glob("resumo_*.json"):
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data["arquivo"] = str(log_file)
                    data["data"] = date_dir.name
                    logs.append(data)
    
    return logs


def buscar_erros_cliente(cliente_id: str, log_dir: str = "./logs") -> List[Dict]:
    """Busca todos os erros de um cliente específico."""
    log_path = Path(log_dir)
    erros = []
    
    if not log_path.exists():
        return erros
    
    for date_dir in log_path.iterdir():
        if date_dir.is_dir():
            for log_file in date_dir.glob("*.json"):
                if "resumo" in log_file.name:
                    continue
                
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data.get("entries", []):
                        if entry.get("cliente_id") == cliente_id and entry.get("level") == "ERROR":
                            entry["arquivo"] = str(log_file)
                            erros.append(entry)
    
    return erros


# Logger global
_logger: Optional[HumanBrowserLogger] = None

def get_logger() -> HumanBrowserLogger:
    """Retorna logger global."""
    global _logger
    if _logger is None:
        _logger = HumanBrowserLogger()
    return _logger

def set_logger(logger: HumanBrowserLogger):
    """Define logger global."""
    global _logger
    _logger = logger
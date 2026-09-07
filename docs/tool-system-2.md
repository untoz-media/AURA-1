# Tool System 2.0 — implementação local

## M007.1 — System Info

Deteção da RAM no Windows através de GlobalMemoryStatusEx, registo no
assistente e encaminhamento de perguntas sobre RAM, CPU e sistema operativo.
O campo ram_gb é mantido por compatibilidade; ram_total_gb e
ram_disponivel_gb usam unidades de 1024³ bytes.

## M007.2 — File Tool

A ferramenta `files` disponibiliza `list` e `exists`, com `path` relativo
à raiz do projeto (fixada pela localização do código, não pela pasta atual).
Não lê conteúdos nem altera ficheiros. Exemplos na conversa:

- Que ficheiros tenho nesta pasta?
- Lista os ficheiros da pasta docs
- Existe o ficheiro README.md?

Caminhos absolutos, caminhos superiores, componentes ocultos, streams NTFS,
wildcards, symlinks e junctions são bloqueados. As listagens examinam no máximo
101 entradas, devolvem até 100 e indicam `truncated` quando há mais entradas.
As entradas devolvidas são ordenadas por nome; não há pesquisa recursiva.
Ficheiros ausentes devolvem `exists: false`; erros de consulta são normalizados.

Os limites são uma validação ao nível da aplicação, não um isolamento do
sistema operativo contra processos locais que alterem diretórios em simultâneo.

## Validação

Executar `python -m pytest -q tests`. Os testes de integração substituem
o Qwen por um runtime simulado. A qualidade das respostas do modelo real
continua a necessitar de validação separada.

## M007.3 — Segurança

O registo explícito de ferramentas funciona como lista de permissões: pedidos
não podem registar nem executar ferramentas desconhecidas. Nomes de registo
são validados; duplicados são rejeitados. Calculadora e data/hora rejeitam
argumentos adicionais e tipos inválidos. Erros inesperados não expõem detalhes
internos. O router ignora entradas inválidas ou superiores a 4096 caracteres.
A ferramenta de ficheiros rejeita também nomes reservados do Windows e
caracteres de controlo. Não existe ferramenta de execução de shell.

Comandos manuais disponíveis: `/tool system_info`, `/tool files list docs`
e `/tool files exists README.md`, além de calculadora e data/hora.

## M007.4 — Testes transversais

Em 2026-09-07: 64 testes aprovados, 1 ignorado por falta de privilégios
para criar symlinks no Windows. Incluem ferramentas desconhecidas, argumentos
inválidos, limites da calculadora, erros, caminhos bloqueados, router,
comandos manuais e integração com a memória.

## M007.5 — Validação local

Validação em 2026-09-07 com Qwen/Qwen3-4B-Instruct-2507 local, 4-bit,
temperatura 0 e limite de 120 tokens. O modelo confirmou a existência de
README.md e respondeu corretamente que 2 mais 3 é 5. A saída foi repetida
em UTF-8 após um erro de impressão de emoji com cp1252; o CLI agora configura
UTF-8 ao iniciar.

O modelo confundiu RAM total e disponível numa das respostas. As perguntas
sobre RAM passam por isso a receber valores formatados diretamente da
ferramenta, sem reformulação pelo modelo. Verificação real após a correção:
15.89 GB totais e 8.32 GB disponíveis naquele instante. Testes após a correção:
64 aprovados e 1 ignorado. Este é um smoke test local, não uma avaliação
exaustiva da qualidade do modelo nem uma auditoria externa de segurança.

O bloco M007 está implementado e validado dentro deste âmbito, com a ressalva
do teste de symlink impedido pelo ambiente. Segue-se a avaliação de conversação,
latência e preparação da versão utilizável; a numeração do roadmap original
de treino/publicação é distinta da sequência de integração usada neste documento.

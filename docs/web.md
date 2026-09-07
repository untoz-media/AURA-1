# AURA-1 Web

## Arranque rápido no Windows

1. Instala Python e as dependências: `python -m pip install -r requirements-runtime.txt`.
2. Faz duplo clique em `iniciar_aura_web.bat` ou executa `python aura_web.py`.
3. Aguarda até o indicador no navegador mostrar **Pronta**.
4. Mantém o terminal aberto. Usa Ctrl+C no terminal para terminar.

O endereço predefinido é `http://127.0.0.1:8765`. Se essa porta estiver
ocupada, executa `python aura_web.py --port 9000`.

No pacote Windows, executa primeiro `instalar_aura_windows.bat`. O instalador
cria um ambiente isolado na pasta `.venv`; depois usa `iniciar_aura_web.bat`.
O arquivo não inclui os pesos do modelo, que são descarregados no primeiro uso.

## Funcionalidades desta versão

- Conversa com Qwen3-4B-Instruct-2507 local.
- Histórico durante a sessão e memória persistente já suportada pelo AURA.
- Nova conversa sem reiniciar o modelo.
- Cálculo, data/hora, informação do sistema e consulta segura de ficheiros.
- Interface adaptada a computador e telemóvel na rede local do dispositivo.
- Estado de carregamento e erros apresentados sem expor detalhes internos.

## Limites conhecidos

- Existe uma conversa por processo. Recarregar a página conserva o contexto
  no servidor, mas a página ainda não volta a desenhar as mensagens antigas.
- A resposta chega completa; ainda não existe apresentação palavra a palavra.
- O servidor aceita apenas o próprio computador. Acesso por outros dispositivos
  exigirá uma arquitetura de autenticação e segurança própria.
- O modelo pode errar. Memória RAM é formatada diretamente pela ferramenta para
  distinguir corretamente o total do disponível.
- O primeiro carregamento observado neste computador demorou cerca de 22 segundos.

## Verificação

`python -m pytest -q tests` valida a aplicação e as ferramentas sem carregar o
modelo. A validação real confirmou estado do modelo, quatro ferramentas e uma
resposta de cálculo através do servidor HTTP.

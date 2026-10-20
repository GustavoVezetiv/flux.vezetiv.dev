# IMOBI Automation — MVP 0.1.1

Aplicação local para reduzir o trabalho mecânico no ImobiBrasil sem usar a API paga.

## Objetivo do MVP

Fluxo inicial:

1. ChatGPT analisa o material usando as regras do Notion.
2. ChatGPT gera um pacote `.json` com as alterações propostas.
3. Você importa o pacote no painel local.
4. Revisa e aprova imóvel por imóvel.
5. O Playwright abre o navegador visível.
6. **MVP 0.1:** você navega manualmente até a Ref. correta e clica `Continuar`.
7. O robô preenche os campos já mapeados, salva e faz auditoria leve.
8. Se não encontrar um campo, o robô pausa; você assume o navegador, corrige manualmente e continua.

A busca automática por Ref., exportação XLS final e auditoria pelo relatório entram nas próximas versões.

## Por que começar assim

A parte mais frágil é mapear a navegação real do ImobiBrasil. Separando navegação e preenchimento conseguimos testar valor real imediatamente sem construir um robô gigante antes de conhecer os seletores da interface.

## Instalação no Windows

1. Instale Python 3.11 ou superior.
2. Extraia esta pasta.
3. Execute `instalar.bat` uma vez.
4. Depois execute `iniciar.bat`.
5. O painel abre no navegador.

## Teste seguro

Use primeiro `packages/exemplo_vanguard.json` com **Modo simulação** ligado.
Nenhum clique no CRM ocorre em simulação.

## Estrutura

- `app.py` — painel Streamlit.
- `worker.py` — processo de execução.
- `automation/adapter.py` — conhecimento da interface do ImobiBrasil.
- `automation/runner.py` — fluxo de execução + pausa manual + auditoria.
- `config/selectors.json` — mapeamento dos campos.
- `data/imobi_automation.db` — histórico local (criado automaticamente).
- `packages/` — pacotes gerados pelo ChatGPT.

## Próximos marcos

### 0.2 — Mapear a tela real
- busca automática por Ref.;
- abrir edição sozinho;
- mapear abas/seções;
- mapear tipos especiais: checkbox, select, autocomplete, editor de texto.

### 0.3 — Auditoria forte
- reler o cadastro após salvar;
- baixar XLS do relatório;
- filtrar apenas Refs alteradas;
- comparar esperado x encontrado.

### 0.4 — Cadastro novo
- 12 seções;
- pausa para escolha da Ref.;
- upload de fotos;
- duplicação assistida.

## Segurança operacional

- Modo simulação deve ficar ligado até validarmos os seletores.
- O robô nunca deve decidir excluir/desativar sozinho.
- A aprovação é por item.
- Em divergência, parar e pedir intervenção humana.


## Correção 0.1.1
- Corrigido o instalador no Windows para não depender do `py` launcher quando ele aponta para uma versão inexistente do Python.
- O instalador agora prioriza Python 3.13/3.12/3.11 instalado em `%LocalAppData%` e usa o executável real para criar o `.venv`.

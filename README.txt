UFC FIGHT ANALYTICS - DASHBOARD STREAMLIT
=========================================

Resumo
------
Dashboard interativo em Streamlit que apresenta análises de lutas do UFC
com gráficos Plotly e painéis por lutador.

Arquivos principais
------------------
- `app.py` — aplicativo Streamlit
- `dashboard_capa.png` — imagem da capa
- `requirements.txt` — dependências

OBS: o ambiente virtual (`.venv`) não deve ser comitado. Adicione `.venv/` no `.gitignore`.

Como o app carrega os dados
--------------------------
O app baixa os dados automaticamente do Kaggle. Para isso você precisa fornecer
um token de API do Kaggle ou as variáveis de ambiente `KAGGLE_USERNAME` e
`KAGGLE_KEY`.

Opções para fornecer credenciais Kaggle:
- Criar o arquivo de token (Windows):
  - Crie a pasta `%USERPROFILE%\.kaggle` se não existir.
  - Salve o arquivo `access_token` com o conteúdo do JSON do seu token do Kaggle em
    `C:\Users\<seu-usuario>\.kaggle\access_token`.
  - Proteja o arquivo: ajuste permissões para que apenas seu usuário leia.
- Ou exporte variáveis de ambiente (temporário):
  ```powershell
  $env:KAGGLE_USERNAME = 'seu_usuario'
  $env:KAGGLE_KEY = 'sua_chave'
  ```

Instalação e execução
---------------------
1. Instale as dependências:
```powershell
pip install -r requirements.txt
```

2. Execute o app:
```powershell
streamlit run app.py
```

Se o navegador não abrir automaticamente, acesse o endereço exibido pelo Streamlit
(normalmente http://localhost:8501).

Cuidados antes de publicar
--------------------------
- Nunca comite o token do Kaggle ou arquivos que contenham credenciais.
- Se algum token foi commitado por engano, remova-o do histórico Git antes de
  publicar e gere um novo token.
- Não inclua a pasta do ambiente virtual no repositório (`.venv/`).

Repository
----------
URL: (preencher após push) 

Detalhes do dataset (aproximados)
---------------------------------
Registros: 8887
Lutadores distintos aproximados: 2757
Período: 1994 a 2026

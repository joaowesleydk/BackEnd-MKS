# MKS Store Backend

Backend em Python para e-commerce de moda e beleza usando FastAPI.

## Configuração

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Configurar banco de dados:**
- Instale PostgreSQL
- Crie um banco chamado `mks_store`
- Copie `.env.example` para `.env` e configure suas variáveis

3. **Executar aplicação:**
```bash
uvicorn app.main:app --reload
```

## Endpoints Principais

### Autenticação
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Dados do usuário logado

### Usuários
- `POST /api/users/register` - Cadastro

### Produtos
- `GET /api/products/` - Listar produtos
- `GET /api/products/{id}` - Produto específico
- `POST /api/products/` - Criar produto
- `GET /api/products/categories/` - Listar categorias
- `POST /api/products/categories/` - Criar categoria

### Pedidos
- `POST /api/orders/` - Criar pedido
- `GET /api/orders/` - Pedidos do usuário

## Documentação
Acesse `http://localhost:8000/docs` para ver a documentação interativa da API.

## Estrutura do Banco
- **users** - Usuários do sistema
- **categories** - Categorias de produtos
- **products** - Produtos (moda/beleza)
- **orders** - Pedidos
- **order_items** - Itens dos pedidos
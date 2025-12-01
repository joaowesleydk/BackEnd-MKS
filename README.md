# MKS Store Backend

Backend em Python para e-commerce de moda e beleza usando FastAPI.

## 🚀 Configuração Rápida

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente
Copie `.env.example` para `.env` e configure:
```bash
cp .env.example .env
```

### 3. Executar aplicação
```bash
uvicorn app.main:app --reload
```

## 📋 Endpoints Principais

### Frontend (formato específico)
- `GET /api/products/frontend` - Lista produtos
- `GET /api/products/categoria/{nome}` - Produtos por categoria  
- `GET /api/products/search?q=termo` - Busca produtos
- `POST /api/products/frontend-create` - Cadastra produto (admin)

### Autenticação
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Cadastro
- `POST /api/auth/google-login` - Login com Google
- `GET /api/auth/me` - Dados do usuário

### Administração
- `POST /api/auth/create-admin` - Criar admin (máx 2)
- `POST /api/products/categories/` - Criar categoria
- `POST /api/upload/image` - Upload de imagem

## 🔧 Configuração

### Banco de dados
```bash
# PostgreSQL local
DATABASE_URL=postgresql://user:password@localhost/mks_store

# Ou usar o setup automático
POST /api/auth/setup-database
```

### Cloudinary (upload de imagens)
```bash
CLOUDINARY_CLOUD_NAME=seu_cloud_name
CLOUDINARY_API_KEY=sua_api_key
CLOUDINARY_API_SECRET=seu_api_secret
```

### Google OAuth
```bash
GOOGLE_CLIENT_ID=seu_client_id
GOOGLE_REDIRECT_URI=https://seu-frontend.com
```

## 📖 Documentação

Acesse `http://localhost:8000/docs` para documentação interativa.

## 🏗️ Estrutura

```
app/
├── api/routes/     # Endpoints da API
├── core/          # Configurações e segurança  
├── crud/          # Operações do banco
├── models/        # Modelos SQLAlchemy
└── schemas/       # Schemas Pydantic
```

## 🔐 Sistema de Roles

- **user**: Pode fazer pedidos e ver produtos
- **admin**: Pode cadastrar produtos e categorias (máximo 2 admins)

## 🌐 Deploy

Configurado para deploy automático no Render via `render.yaml`.

URL da API: https://backend-mks.onrender.com
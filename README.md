# Moda Karina Store - Backend

Backend completo para e-commerce de moda desenvolvido com FastAPI, PostgreSQL e integração com Mercado Pago.

## 🚀 Funcionalidades

- **Autenticação**: Login tradicional e Google OAuth com JWT
- **Produtos**: CRUD completo com categorias e promoções
- **Carrinho**: Sistema de carrinho por usuário
- **Pedidos**: Checkout com Mercado Pago (PIX, cartão, boleto)
- **Frete**: Integração ViaCEP e cálculo automático
- **Provador Virtual**: Upload e processamento de imagens
- **Webhooks**: Confirmação automática de pagamentos

## 🛠️ Stack Técnica

- **Python 3.8+**
- **FastAPI** - Framework web moderno
- **PostgreSQL** - Banco de dados
- **SQLAlchemy** - ORM
- **Alembic** - Migrações
- **JWT** - Autenticação
- **Mercado Pago SDK** - Pagamentos
- **Google OAuth** - Login social

## 📦 Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd BackEnd-MKS
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. Execute as migrações:
```bash
alembic upgrade head
```

5. Inicie o servidor:
```bash
uvicorn app.main:app --reload
```

## 🔧 Configuração

### Variáveis de Ambiente

```env
DATABASE_URL=postgresql://user:password@localhost/moda_karina_store
JWT_SECRET_KEY=your-secret-key-here
MERCADOPAGO_ACCESS_TOKEN=your-mercadopago-token
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FRONTEND_URL=https://karinamodastore.com.br
```

### Banco de Dados

1. Crie um banco PostgreSQL
2. Configure a DATABASE_URL no .env
3. Execute: `alembic upgrade head`

## 📚 API Endpoints

### Autenticação
- `POST /auth/register` - Registro de usuário
- `POST /auth/login` - Login tradicional
- `POST /auth/google` - Login com Google
- `GET /auth/me` - Perfil do usuário
- `PUT /auth/profile` - Atualizar perfil

### Produtos
- `GET /products/` - Listar produtos (com filtros)
- `GET /products/{id}` - Detalhes do produto
- `POST /products/` - Criar produto (admin)
- `PUT /products/{id}` - Atualizar produto (admin)
- `DELETE /products/{id}` - Deletar produto (admin)

### Carrinho
- `GET /cart/` - Ver carrinho
- `POST /cart/add` - Adicionar ao carrinho
- `PUT /cart/{item_id}` - Atualizar quantidade
- `DELETE /cart/{item_id}` - Remover item

### Pedidos
- `GET /orders/` - Histórico de pedidos
- `POST /orders/` - Criar pedido
- `POST /orders/calculate-shipping` - Calcular frete

### Outros
- `GET /address/cep/{cep}` - Consultar CEP
- `POST /virtual-tryon/upload` - Upload para provador
- `POST /webhooks/mercadopago` - Webhook pagamentos

## 🚀 Deploy

### Render

1. Conecte seu repositório no Render
2. Configure as variáveis de ambiente
3. Use o comando de build: `pip install -r requirements.txt`
4. Use o comando de start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 📄 Documentação

Acesse `/docs` para ver a documentação interativa do Swagger.

## 🔒 Segurança

- Senhas hasheadas com bcrypt
- JWT tokens com expiração
- CORS configurado
- Validação de dados com Pydantic
- Middleware de autenticação

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request
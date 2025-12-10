# Moda Karina Store - Backend Node.js

Backend completo para e-commerce de moda desenvolvido com Node.js, Express, PostgreSQL e integração com Mercado Pago.

## 🚀 Funcionalidades

- **Autenticação**: Login tradicional e Google OAuth com JWT
- **Produtos**: CRUD completo com categorias e promoções
- **Carrinho**: Sistema de carrinho por usuário
- **Pedidos**: Checkout com Mercado Pago (PIX, cartão, boleto)
- **Frete**: Integração ViaCEP e cálculo automático
- **Webhooks**: Confirmação automática de pagamentos

## 🛠️ Stack Técnica

- **Node.js 18+**
- **Express** - Framework web
- **PostgreSQL** - Banco de dados
- **Prisma** - ORM moderno
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
npm install
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. Execute as migrações:
```bash
npx prisma migrate deploy
npx prisma generate
```

5. Inicie o servidor:
```bash
npm start
```

## 🔧 Configuração

### Variáveis de Ambiente

```env
DATABASE_URL=postgresql://user:password@localhost/moda_karina_store
JWT_SECRET_KEY=your-secret-key-here
MERCADOPAGO_ACCESS_TOKEN=your-mercadopago-token
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## 📚 API Endpoints

### Autenticação
- `POST /auth/register` - Registro de usuário
- `POST /auth/login` - Login tradicional
- `POST /auth/google` - Login com Google
- `GET /auth/me` - Perfil do usuário

### Produtos
- `GET /produtos/` - Listar produtos (com filtros)
- `GET /produtos/{id}` - Detalhes do produto
- `POST /produtos/` - Criar produto (admin)
- `PUT /produtos/{id}` - Atualizar produto (admin)
- `DELETE /produtos/{id}` - Deletar produto (admin)

### Carrinho
- `GET /carrinho/` - Ver carrinho
- `POST /carrinho/adicionar` - Adicionar ao carrinho
- `PUT /carrinho/item/{id}` - Atualizar quantidade
- `DELETE /carrinho/item/{id}` - Remover item
- `DELETE /carrinho/limpar` - Limpar carrinho

### Outros
- `GET /usuario/perfil` - Perfil do usuário
- `PUT /usuario/perfil` - Atualizar perfil
- `POST /usuario/upload-foto` - Upload de foto
- `POST /pagamento/mercadopago` - Criar pagamento
- `GET /cep/{cep}` - Consultar CEP
- `POST /frete/calcular` - Calcular frete
- `POST /webhook/mercadopago` - Webhook pagamentos

## 🚀 Deploy no Render

1. **Build Command:** `npm install && npx prisma generate`
2. **Start Command:** `npm start`

## 📄 Documentação

Todas as respostas seguem o padrão:
```json
{
  "success": true/false,
  "data": {...},
  "message": "string"
}
```
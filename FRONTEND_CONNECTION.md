# Conexão Frontend - Backend

## URL da API
```
https://seu-app-name.onrender.com
```

## Endpoints Principais

### Autenticação
```javascript
// Login
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded
Body: username=email&password=senha

// Dados do usuário logado
GET /api/auth/me
Authorization: Bearer {token}
```

### Usuários
```javascript
// Cadastro
POST /api/users/register
Content-Type: application/json
Body: {
  "name": "Nome",
  "email": "email@exemplo.com",
  "password": "senha123"
}
```

### Produtos
```javascript
// Listar produtos
GET /api/products/

// Produto específico
GET /api/products/{id}

// Categorias
GET /api/products/categories/
```

### Pedidos
```javascript
// Criar pedido
POST /api/orders/
Authorization: Bearer {token}
Content-Type: application/json
Body: {
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ]
}

// Listar pedidos do usuário
GET /api/orders/
Authorization: Bearer {token}
```

## Exemplo de uso com JavaScript

```javascript
const API_URL = 'https://seu-app-name.onrender.com';

// Login
async function login(email, password) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `username=${email}&password=${password}`
  });
  
  const data = await response.json();
  if (data.access_token) {
    localStorage.setItem('token', data.access_token);
  }
  return data;
}

// Buscar produtos
async function getProducts() {
  const response = await fetch(`${API_URL}/api/products/`);
  return await response.json();
}

// Fazer pedido
async function createOrder(items) {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_URL}/api/orders/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ items })
  });
  return await response.json();
}
```

## CORS
O CORS já está configurado para aceitar requisições de qualquer origem.

## Documentação Interativa
Acesse: `https://seu-app-name.onrender.com/docs`
# Exemplos de Uso dos Endpoints de Email

## 1. Email de Contato

```bash
POST https://backend-mks-1.onrender.com/api/email/contact
Content-Type: application/json

{
  "name": "João Silva",
  "email": "joao@email.com",
  "phone": "(11) 99999-9999",
  "subject": "Dúvida sobre produto",
  "message": "Gostaria de saber mais informações sobre o produto X."
}
```

## 2. Confirmação de Pedido (para o cliente)

```bash
POST https://backend-mks-1.onrender.com/api/email/order-confirmation
Content-Type: application/json

{
  "customerName": "Maria Santos",
  "customerEmail": "maria@email.com",
  "orderId": "12345",
  "items": [
    {
      "name": "Vestido Floral",
      "quantity": 1,
      "price": 89.90
    },
    {
      "name": "Bolsa de Couro",
      "quantity": 1,
      "price": 120.00
    }
  ],
  "total": 209.90,
  "shippingAddress": {
    "street": "Rua das Flores",
    "number": "123",
    "neighborhood": "Centro",
    "city": "São Paulo",
    "state": "SP",
    "zipCode": "01234-567"
  },
  "paymentMethod": "PIX"
}
```

## 3. Notificação de Novo Pedido (para a loja)

```bash
POST https://backend-mks-1.onrender.com/api/email/new-order
Content-Type: application/json

{
  "orderId": "12345",
  "customerName": "Maria Santos",
  "customerEmail": "maria@email.com",
  "items": [
    {
      "name": "Vestido Floral",
      "quantity": 1,
      "price": 89.90
    },
    {
      "name": "Bolsa de Couro",
      "quantity": 1,
      "price": 120.00
    }
  ],
  "total": 209.90
}
```

## Configuração do Gmail

Para usar o Gmail SMTP, você precisa:

1. **Ativar a verificação em 2 etapas** na sua conta Google
2. **Gerar uma senha de app** específica para o backend
3. **Usar essa senha** na variável `SMTP_PASSWORD`

### Passos para gerar senha de app:

1. Acesse: https://myaccount.google.com/security
2. Clique em "Verificação em duas etapas"
3. Role até "Senhas de app"
4. Selecione "Email" e "Outro (nome personalizado)"
5. Digite "MKS Store Backend"
6. Use a senha gerada de 16 caracteres

### Variáveis de ambiente necessárias:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=karinamodastore@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
```

## Testando os Endpoints

Após fazer o deploy, teste os endpoints usando:

- **Postman**
- **Insomnia** 
- **cURL**
- **Swagger UI**: https://backend-mks-1.onrender.com/docs

Os emails serão enviados automaticamente quando os endpoints forem chamados.
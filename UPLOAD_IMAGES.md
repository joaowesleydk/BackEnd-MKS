# 📸 Upload de Imagens de Produtos - MKS Store

## 🚀 Novo Endpoint Implementado

### `POST /api/products/frontend-create-with-file`

Endpoint para cadastrar produtos com upload de imagem via FormData.

## 📋 Parâmetros

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `name` | string | ✅ | Nome do produto |
| `price` | float | ✅ | Preço do produto |
| `category` | string | ✅ | Categoria do produto |
| `description` | string | ❌ | Descrição do produto |
| `promocao` | boolean | ❌ | Se está em promoção (default: false) |
| `imagemFile` | file | ✅ | Arquivo de imagem (JPG, PNG, GIF, WebP) |

## 🔒 Autenticação

Requer token de admin no header:
```
Authorization: Bearer SEU_TOKEN_AQUI
```

## ✅ Validações

- **Tipo de arquivo**: Apenas imagens (image/*)
- **Tamanho máximo**: 5MB
- **Formatos aceitos**: JPG, PNG, GIF, WebP
- **Nomes únicos**: UUID4 para evitar conflitos

## 📁 Estrutura de Arquivos

```
backend/
├── uploads/
│   └── products/
│       ├── 123e4567-e89b-12d3-a456-426614174000.jpg
│       ├── 987fcdeb-51a2-43d1-b789-123456789abc.png
│       └── ...
└── ...
```

## 🌐 Acesso às Imagens

As imagens ficam disponíveis em:
```
GET /uploads/products/{filename}
```

Exemplo:
```
https://backend-mks-1.onrender.com/uploads/products/123e4567-e89b-12d3-a456-426614174000.jpg
```

## 🧪 Exemplo de Uso

### Com cURL:

```bash
# 1. Login para obter token
curl -X POST "https://backend-mks-1.onrender.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@email.com", "password": "senha123"}'

# 2. Upload do produto
curl -X POST "https://backend-mks-1.onrender.com/api/products/frontend-create-with-file" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -F "name=Vestido Floral Verão" \
  -F "price=89.90" \
  -F "category=Vestidos" \
  -F "description=Lindo vestido floral perfeito para o verão" \
  -F "promocao=false" \
  -F "imagemFile=@/caminho/para/imagem.jpg"
```

### Com JavaScript (Frontend):

```javascript
const formData = new FormData();
formData.append('name', 'Vestido Floral Verão');
formData.append('price', '89.90');
formData.append('category', 'Vestidos');
formData.append('description', 'Lindo vestido floral');
formData.append('promocao', 'false');
formData.append('imagemFile', fileInput.files[0]);

fetch('/api/products/frontend-create-with-file', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Com Python:

```python
import requests

# Login
login_response = requests.post('/api/auth/login', json={
    'email': 'admin@email.com',
    'password': 'senha123'
})
token = login_response.json()['access_token']

# Upload
with open('produto.jpg', 'rb') as f:
    response = requests.post('/api/products/frontend-create-with-file', 
        headers={'Authorization': f'Bearer {token}'},
        data={
            'name': 'Vestido Floral',
            'price': 89.90,
            'category': 'Vestidos',
            'description': 'Descrição do produto',
            'promocao': False
        },
        files={'imagemFile': f}
    )
```

## 📤 Resposta de Sucesso

```json
{
  "success": true,
  "message": "Produto criado com sucesso",
  "produto": {
    "name": "Vestido Floral Verão",
    "price": 89.9,
    "category": "Vestidos",
    "image": "/uploads/products/123e4567-e89b-12d3-a456-426614174000.jpg",
    "description": "Lindo vestido floral perfeito para o verão",
    "promocao": false
  }
}
```

## ❌ Possíveis Erros

| Código | Erro | Solução |
|--------|------|---------|
| 400 | "Arquivo deve ser uma imagem" | Envie apenas arquivos de imagem |
| 400 | "Imagem muito grande. Máximo 5MB" | Reduza o tamanho da imagem |
| 401 | "Could not validate credentials" | Faça login e use token válido |
| 403 | "Acesso negado. Apenas admins..." | Use conta de administrador |
| 500 | "Erro interno" | Verifique logs do servidor |

## 🔧 Configuração no Deploy

Para funcionar no Render/Heroku, certifique-se de que:

1. O diretório `uploads/` seja criado automaticamente
2. As dependências estejam no `requirements.txt`:
   - `python-multipart`
   - `aiofiles`
3. O servidor tenha permissão de escrita

## 📝 Notas Importantes

- ✅ Imagens são salvas localmente no servidor
- ✅ Nomes únicos evitam conflitos
- ✅ Validação de tipo e tamanho
- ✅ Limpeza automática em caso de erro
- ✅ Compatível com deploy em nuvem

## 🔄 Endpoints Relacionados

- `GET /api/products/frontend` - Lista produtos (inclui URLs das imagens)
- `GET /uploads/products/{filename}` - Serve imagem específica
- `POST /api/products/frontend-create` - Criar produto sem arquivo (URL externa)
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

const authRoutes = require('./routes/auth');
const produtosRoutes = require('./routes/produtos');
const carrinhoRoutes = require('./routes/carrinho');
const usuarioRoutes = require('./routes/usuario');
const pagamentoRoutes = require('./routes/pagamento');
const cepRoutes = require('./routes/cep');
const freteRoutes = require('./routes/frete');
const webhookRoutes = require('./routes/webhook');

const app = express();
const PORT = process.env.PORT || 3000;

// Middlewares
app.use(helmet());
app.use(cors({
  origin: [
    'https://karinamodastore.com.br',
    'http://localhost:5173',
    'http://localhost:3000'
  ],
  credentials: true
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
  res.json({ 
    success: true, 
    message: 'Moda Karina Store API is running!', 
    version: '1.0.0' 
  });
});

app.use('/auth', authRoutes);
app.use('/produtos', produtosRoutes);
app.use('/carrinho', carrinhoRoutes);
app.use('/usuario', usuarioRoutes);
app.use('/pagamento', pagamentoRoutes);
app.use('/cep', cepRoutes);
app.use('/frete', freteRoutes);
app.use('/webhook', webhookRoutes);

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    success: false,
    data: null,
    message: 'Internal server error'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    data: null,
    message: 'Route not found'
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});